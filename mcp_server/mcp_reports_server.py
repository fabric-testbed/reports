"""
FABRIC Reports MCP Server — single entry point.

Merges v1 explicit tool signatures with v2 structured config/logging.
Supports both stdio (local) and HTTP (server) transport modes.

Usage:
    # stdio mode (local, reads FABRIC_RC / FABRIC_TOKEN):
    python mcp_reports_server.py

    # HTTP mode (Bearer-auth per request):
    MCP_TRANSPORT=http python mcp_reports_server.py

    # With new-style env vars:
    MCP_TRANSPORT__MODE=http MCP_LOGGING__LEVEL=DEBUG python mcp_reports_server.py
"""

from __future__ import annotations

import json
import os
import asyncio
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BeforeValidator
from typing_extensions import Annotated

from fastmcp import FastMCP
from fabric_reports_client.reports_api import ReportsApi

# ---- Config / logging (from config/) ------------------------------------
from config.settings import get_settings
from config.logging_config import setup_logging, get_logger

# Initialize settings & logging at import time so every module sees them.
settings = get_settings()
setup_logging(settings.logging)
logger = get_logger(__name__)

# Conditionally import HTTP-specific dependencies
if settings.transport.mode == "http":
    from fastmcp.server.context import Context
    from fastmcp.server.dependencies import get_http_headers


# =========================================================================
# _parse_listish / JsonListStr  (from v1, verbatim)
# =========================================================================

def _parse_listish(v: Any) -> Any:
    """
    Accept list[str] OR a string that encodes a JSON list.
    Also accepts comma-separated strings.
    """
    if v is None:
        return None
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        if "," in s:
            return [p.strip() for p in s.split(",") if p.strip()]
        return [s]
    return v


JsonListStr = Annotated[Optional[List[str]], BeforeValidator(_parse_listish)]


# =========================================================================
# TokenProvider — thread-safe, TTL-cached for stdio mode
# =========================================================================

class TokenProvider:
    """
    Provides FABRIC auth tokens.

    - **stdio mode**: reads from FABRIC_RC / FABRIC_TOKEN env and caches
      with a configurable TTL (default 1800 s = 30 min).
    - **HTTP mode**: extracts Bearer token from request headers (no cache).
    """

    def __init__(self, transport_mode: str, ttl: int = 1800):
        self._transport_mode = transport_mode
        self._ttl = ttl
        self._lock = threading.Lock()
        self._cached_token: Optional[str] = None
        self._cached_at: float = 0.0

        # Eagerly load config on startup for stdio so we fail fast
        if self._transport_mode == "stdio":
            self._load_fabric_config()
            tok = self._read_token()
            if tok:
                self._cached_token = tok
                self._cached_at = time.monotonic()
                logger.info("FABRIC token loaded successfully")
            else:
                logger.warning(
                    "Neither FABRIC_RC nor FABRIC_TOKEN set — "
                    "authentication will fail in stdio mode"
                )

    # -- public API --------------------------------------------------------

    def get_token(self, headers: Optional[Dict[str, str]] = None) -> str:
        """Return a valid token or raise."""
        if self._transport_mode == "http":
            return self._token_from_headers(headers or {})
        return self._get_stdio_token()

    # -- internals ---------------------------------------------------------

    def _get_stdio_token(self) -> str:
        with self._lock:
            now = time.monotonic()
            if self._cached_token and (now - self._cached_at) < self._ttl:
                return self._cached_token
            tok = self._read_token()
            if not tok:
                raise ValueError(
                    "FABRIC_TOKEN environment variable must be set "
                    "(or set FABRIC_RC to the config directory)"
                )
            self._cached_token = tok
            self._cached_at = now
            return tok

    @staticmethod
    def _token_from_headers(headers: Dict[str, str]) -> str:
        low = {k.lower(): v for k, v in headers.items()}
        auth = low.get("authorization", "").strip()
        if auth.lower().startswith("bearer "):
            return auth.split(" ", 1)[1].strip()
        raise ValueError(
            "Authentication Required: Missing or invalid Authorization Bearer token."
        )

    @staticmethod
    def _load_fabric_config() -> None:
        """Parse FABRIC_RC/fabric_rc and inject env vars."""
        fabric_rc_dir = os.environ.get("FABRIC_RC")
        if not fabric_rc_dir:
            return
        fabric_rc_file = Path(fabric_rc_dir) / "fabric_rc"
        if not fabric_rc_file.exists():
            logger.info("FABRIC_RC set to %s but fabric_rc file not found", fabric_rc_dir)
            return
        try:
            with open(fabric_rc_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("export "):
                        line = line[7:]
                    if "=" in line:
                        key, value = line.split("=", 1)
                        value = value.strip().strip('"').strip("'")
                        if key not in os.environ:
                            os.environ[key] = value
            logger.info("Loaded FABRIC configuration from: %s", fabric_rc_file)
        except Exception as e:
            logger.warning("Failed to load fabric_rc from %s: %s", fabric_rc_file, e)

    @staticmethod
    def _read_token() -> Optional[str]:
        """Read token from FABRIC_TOKEN_LOCATION or FABRIC_TOKEN env."""
        token_location = os.environ.get("FABRIC_TOKEN_LOCATION")
        if token_location:
            token_file = Path(token_location)
            if token_file.exists():
                try:
                    with open(token_file, "r") as f:
                        data = json.load(f)
                    tok = data.get("id_token") or data.get("token")
                    if tok:
                        return tok
                except Exception as e:
                    logger.warning("Failed to read token from %s: %s", token_file, e)
        return os.environ.get("FABRIC_TOKEN")


# =========================================================================
# _CircuitBreaker — wraps actual API calls (not client creation)
# =========================================================================

class _CircuitBreaker:
    """
    Simple circuit breaker for the Reports API backend.

    States:
        closed   — requests flow normally
        open     — all requests are rejected immediately
        half-open — one probe request is allowed through
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self._threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._lock = threading.Lock()
        self._failures = 0
        self._opened_at: float = 0.0
        self._state: str = "closed"  # closed | open | half-open

    def check(self) -> None:
        """Raise if circuit is open (and not yet eligible for half-open)."""
        with self._lock:
            if self._state == "closed":
                return
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self._recovery_timeout:
                self._state = "half-open"
                logger.info("Circuit breaker entering half-open state")
                return
            raise RuntimeError(
                "Reports API circuit breaker is open — too many consecutive failures. "
                f"Will retry in {self._recovery_timeout - elapsed:.0f}s."
            )

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            if self._state != "closed":
                logger.info("Circuit breaker closed (backend recovered)")
            self._state = "closed"

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self._threshold and self._state == "closed":
                self._state = "open"
                self._opened_at = time.monotonic()
                logger.error(
                    "Circuit breaker opened after %d consecutive failures",
                    self._failures,
                )


_breaker = _CircuitBreaker()


# =========================================================================
# Helpers
# =========================================================================

# Meta fields various bridges may attach to tool calls — filter from kwargs
_EXTRA_META_ARGS = frozenset({
    "toolCallId", "tool_call_id", "id", "type", "name", "tool",
})

# Only coerce these keys to lists
_LIST_KEYS = frozenset({
    "user_id", "user_email", "project_id", "slice_id", "slice_state",
    "sliver_id", "sliver_type", "sliver_state",
    "component_type", "component_model", "bdf", "vlan",
    "ip_subnet", "ip_v4", "ip_v6",
    "site", "host", "facility",
    "exclude_user_id", "exclude_user_email", "exclude_project_id",
    "exclude_site", "exclude_host", "exclude_slice_state", "exclude_sliver_state",
    "project_type", "exclude_project_type",
})

token_provider = TokenProvider(transport_mode=settings.transport.mode)


def _get_headers() -> Optional[Dict[str, str]]:
    """Return HTTP headers if in HTTP mode, else None."""
    if settings.transport.mode == "http":
        return get_http_headers() or {}
    return None


def _get_client(headers: Optional[Dict[str, str]] = None) -> ReportsApi:
    """Create a ReportsApi client with the right token."""
    tok = token_provider.get_token(headers=headers)
    return ReportsApi(base_url=settings.api.base_url, token=tok)


def _coerce_to_list(v: Any) -> Any:
    """Coerce string-ish values to list[str]."""
    if v is None:
        return None
    if isinstance(v, list):
        return [str(x) for x in v]
    if not isinstance(v, str):
        return v
    s = v.strip()
    if not s:
        return []
    if s.startswith("[") and s.endswith("]"):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
    if "," in s:
        return [p.strip() for p in s.split(",") if p.strip()]
    return [s]


async def _call(client: ReportsApi, method: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Call a ReportsApi method in a thread, with circuit-breaker protection.

    - Filters out None values and meta args (toolCallId, etc.)
    - Coerces list-typed keys from strings if needed
    - Wraps execution with circuit breaker check/record
    """
    fn = getattr(client, method)

    final_args: Dict[str, Any] = {}
    for k, v in kwargs.items():
        if v is None or k in _EXTRA_META_ARGS:
            continue
        if k in _LIST_KEYS:
            final_args[k] = _coerce_to_list(v)
        else:
            final_args[k] = v

    _breaker.check()
    try:
        result = await asyncio.to_thread(fn, **final_args)
        _breaker.record_success()
        return result
    except Exception:
        _breaker.record_failure()
        raise


# =========================================================================
# FastMCP app + system prompt
# =========================================================================

mcp = FastMCP(
    name=f"fabric-reports-mcp-{settings.transport.mode}",
    instructions="Proxy for accessing FABRIC Reports API data via LLM tool calls.",
    version="1.4.0",
)

SYSTEM_TEXT_PATH = Path(__file__).parent / "system.md"
if SYSTEM_TEXT_PATH.exists():
    SYSTEM_TEXT = SYSTEM_TEXT_PATH.read_text(encoding="utf-8").strip()
else:
    SYSTEM_TEXT = "System rules for querying FABRIC Reports via MCP"


@mcp.prompt(name="fabric-reports-system")
def fabric_reports_system_prompt():
    """System rules for querying FABRIC Reports via MCP"""
    return SYSTEM_TEXT


# =========================================================================
# Tool definitions — explicit parameter signatures (from v1)
# =========================================================================

@mcp.tool(name="query-version", title="Query Version")
async def query_version(
        toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve version information from the FABRIC Reports API.

    Returns the current API version, build information, and service status.
    Useful for verifying API availability and compatibility.

    Returns:
        Dict containing version details including version number, git commit,
        and service metadata.
    """
    logger.info("Executing query-version")
    client = _get_client(_get_headers())
    result = await _call(client, "query_version")
    logger.info("query-version completed")
    return result


@mcp.tool(name="query-sites", title="Query Sites")
async def query_sites(
        toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve all FABRIC testbed sites.

    Returns a complete list of physical FABRIC sites where resources are located.
    Each site includes information about location, capacity, and available resources such as GPUs, FPGAs, SmartNICs.

    Note: This endpoint does not support filtering.

    Returns:
        Dict containing list of sites with details including site name, ID,
        location, and resource capacities.
    """
    logger.info("Executing query-sites")
    client = _get_client(_get_headers())
    result = await _call(client, "query_sites")
    logger.info("query-sites completed")
    return result


@mcp.tool(name="query-slices", title="Query Slices")
async def query_slices(
        toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: JsonListStr = None,
        user_email: JsonListStr = None,
        project_id: JsonListStr = None,
        slice_id: JsonListStr = None,
        slice_state: JsonListStr = None,
        sliver_id: JsonListStr = None,
        sliver_type: JsonListStr = None,
        sliver_state: JsonListStr = None,
        component_type: JsonListStr = None,
        component_model: JsonListStr = None,
        bdf: JsonListStr = None,
        vlan: JsonListStr = None,
        ip_subnet: JsonListStr = None,
        ip_v4: JsonListStr = None,
        ip_v6: JsonListStr = None,
        site: JsonListStr = None,
        host: JsonListStr = None,
        facility: JsonListStr = None,
        exclude_user_id: JsonListStr = None,
        exclude_user_email: JsonListStr = None,
        exclude_project_id: JsonListStr = None,
        exclude_site: JsonListStr = None,
        exclude_host: JsonListStr = None,
        exclude_slice_state: JsonListStr = None,
        exclude_sliver_state: JsonListStr = None,
        page: int = 0,
        per_page: int = 1000,
        fetch_all: bool = True,
) -> Dict[str, Any]:
    """
    Query FABRIC experimental slices with comprehensive filtering.

    Slices are user-created experimental environments that contain one or more
    slivers (resource allocations). Use this endpoint to find slices based on
    their state, associated resources, time periods, or relationships to users,
    projects, and sites.

    Args:
        start_time: ISO8601 timestamp - filter slices created/modified after this time
        end_time: ISO8601 timestamp - filter slices created/modified before this time
        user_id: List of user UUIDs to filter by (OR logic)
        user_email: List of user emails to filter by (OR logic)
        project_id: List of project UUIDs to filter by (OR logic)
        slice_id: List of slice UUIDs to filter by (OR logic)
        slice_state: List of slice states (Nascent, Configuring, StableOK,
                     StableError, ModifyOK, ModifyError, Closing, Dead)
        sliver_id: Filter slices containing these sliver UUIDs
        sliver_type: Filter slices by sliver types (VM, Switch, Facility, L2STS,
                     L2PTP, L2Bridge, FABNetv4, FABNetv6, etc.)
        sliver_state: Filter by sliver states within the slice (Nascent, Ticketed,
                      Active, ActiveTicketed, Closed, CloseWait, Failed, etc.)
        component_type: Filter by component types (GPU, SmartNIC, SharedNIC,
                        FPGA, NVME, Storage)
        component_model: Filter by specific hardware model strings
        bdf: Filter by PCI Bus-Device-Function identifiers
        vlan: Filter by VLAN tags
        ip_subnet: Filter by IP subnet (CIDR notation)
        ip_v4: Filter by IPv4 addresses
        ip_v6: Filter by IPv6 addresses
        site: List of FABRIC site names to filter by
        host: List of physical host names to filter by
        facility: Filter by facility type
        exclude_user_id: Exclude slices from these user UUIDs
        exclude_user_email: Exclude slices from these user emails
        exclude_project_id: Exclude slices from these project UUIDs (use for
                            filtering out FABRIC personnel projects)
        exclude_site: Exclude slices from these sites
        exclude_host: Exclude slices from these hosts
        exclude_slice_state: Exclude these slice states
        exclude_sliver_state: Exclude these sliver states
        page: Page number for pagination (0-indexed)
        per_page: Number of results per page (max 1000)
        fetch_all: If True, automatically fetch all pages

    Returns:
        Dict containing list of slices with details including slice_id, slice_name,
        state, project_id, user_id, site information, and associated resources.

    Examples:
        - Active slices at EDC site: site=["EDC"], exclude_slice_state=["Dead", "Closing"]
        - User's slices: user_email=["user@example.com"]
        - Slices with GPUs: component_type=["GPU"]
    """
    logger.info("Executing query-slices")
    client = _get_client(_get_headers())
    result = await _call(
        client, "query_slices",
        start_time=start_time, end_time=end_time,
        user_id=user_id, user_email=user_email, project_id=project_id,
        slice_id=slice_id, slice_state=slice_state,
        sliver_id=sliver_id, sliver_type=sliver_type, sliver_state=sliver_state,
        component_type=component_type, component_model=component_model,
        bdf=bdf, vlan=vlan, ip_subnet=ip_subnet, ip_v4=ip_v4, ip_v6=ip_v6,
        site=site, host=host, facility=facility,
        exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
        exclude_project_id=exclude_project_id, exclude_site=exclude_site,
        exclude_host=exclude_host, exclude_slice_state=exclude_slice_state,
        exclude_sliver_state=exclude_sliver_state,
        page=page, per_page=per_page, fetch_all=fetch_all,
    )
    logger.info("query-slices completed")
    return result


@mcp.tool(name="query-slivers", title="Query Slivers")
async def query_slivers(
        toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: JsonListStr = None,
        user_email: JsonListStr = None,
        project_id: JsonListStr = None,
        slice_id: JsonListStr = None,
        slice_state: JsonListStr = None,
        sliver_id: JsonListStr = None,
        sliver_type: JsonListStr = None,
        sliver_state: JsonListStr = None,
        component_type: JsonListStr = None,
        component_model: JsonListStr = None,
        bdf: JsonListStr = None,
        vlan: JsonListStr = None,
        ip_subnet: JsonListStr = None,
        ip_v4: JsonListStr = None,
        ip_v6: JsonListStr = None,
        site: JsonListStr = None,
        host: JsonListStr = None,
        facility: JsonListStr = None,
        exclude_user_id: JsonListStr = None,
        exclude_user_email: JsonListStr = None,
        exclude_project_id: JsonListStr = None,
        exclude_site: JsonListStr = None,
        exclude_host: JsonListStr = None,
        exclude_slice_state: JsonListStr = None,
        exclude_sliver_state: JsonListStr = None,
        page: int = 0,
        per_page: int = 1000,
        fetch_all: bool = True,
) -> Dict[str, Any]:
    """
    Query individual resource allocations (slivers) with comprehensive filtering.

    Slivers are the individual resource allocations within slices. Each sliver
    represents a specific resource type (VM, network connection, storage, etc.)
    allocated at a particular site. Use this endpoint for detailed resource-level
    queries and utilization tracking.

    Args:
        start_time: ISO8601 timestamp - filter slivers created/modified after this time
        end_time: ISO8601 timestamp - filter slivers created/modified before this time
        user_id: List of user UUIDs owning the parent slice
        user_email: List of user emails owning the parent slice
        project_id: List of project UUIDs to filter by
        slice_id: List of parent slice UUIDs
        slice_state: Filter by parent slice states
        sliver_id: List of specific sliver UUIDs to retrieve
        sliver_type: Filter by sliver types (VM, Switch, Facility, L2STS, L2PTP,
                     L2Bridge, FABNetv4, FABNetv6, PortMirror, L3VPN, etc.)
        sliver_state: Filter by sliver states (Nascent, Ticketed, Active,
                      ActiveTicketed, Closed, CloseWait, Failed, Unknown, CloseFail)
        component_type: Filter by attached component types (GPU, SmartNIC,
                        SharedNIC, FPGA, NVME, Storage)
        component_model: Filter by specific hardware model strings
        bdf: Filter by PCI Bus-Device-Function identifiers
        vlan: Filter by VLAN tags assigned to sliver interfaces
        ip_subnet: Filter by IP subnet (CIDR notation)
        ip_v4: Filter by assigned IPv4 addresses
        ip_v6: Filter by assigned IPv6 addresses
        site: List of FABRIC site names where slivers are allocated
        host: List of physical host names running the slivers
        facility: Filter by facility type
        exclude_user_id: Exclude slivers from these user UUIDs
        exclude_user_email: Exclude slivers from these user emails
        exclude_project_id: Exclude slivers from these project UUIDs
        exclude_site: Exclude slivers from these sites
        exclude_host: Exclude slivers from these hosts
        exclude_slice_state: Exclude based on parent slice states
        exclude_sliver_state: Exclude these sliver states
        page: Page number for pagination (0-indexed)
        per_page: Number of results per page (max 1000)
        fetch_all: If True, automatically fetch all pages

    Returns:
        Dict containing list of slivers with details including sliver_id,
        sliver_type, state, site, host, attached components, network interfaces,
        and parent slice information.

    Examples:
        - Active VM slivers: sliver_type=["VM"], exclude_sliver_state=["Dead"]
        - SmartNIC allocations at RENC: component_type=["SmartNIC"], site=["RENC"]
        - Failed slivers in last 24h: sliver_state=["Failed"], start_time="2025-01-09T00:00:00Z"
    """
    logger.info("Executing query-slivers")
    client = _get_client(_get_headers())
    result = await _call(
        client, "query_slivers",
        start_time=start_time, end_time=end_time,
        user_id=user_id, user_email=user_email, project_id=project_id,
        slice_id=slice_id, slice_state=slice_state,
        sliver_id=sliver_id, sliver_type=sliver_type, sliver_state=sliver_state,
        component_type=component_type, component_model=component_model,
        bdf=bdf, vlan=vlan, ip_subnet=ip_subnet, ip_v4=ip_v4, ip_v6=ip_v6,
        site=site, host=host, facility=facility,
        exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
        exclude_project_id=exclude_project_id, exclude_site=exclude_site,
        exclude_host=exclude_host, exclude_slice_state=exclude_slice_state,
        exclude_sliver_state=exclude_sliver_state,
        page=page, per_page=per_page, fetch_all=fetch_all,
    )
    logger.info("query-slivers completed")
    return result


@mcp.tool(name="query-users", title="Query Users")
async def query_users(
        toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: JsonListStr = None,
        user_email: JsonListStr = None,
        project_id: JsonListStr = None,
        slice_id: JsonListStr = None,
        slice_state: JsonListStr = None,
        sliver_id: JsonListStr = None,
        sliver_type: JsonListStr = None,
        sliver_state: JsonListStr = None,
        component_type: JsonListStr = None,
        component_model: JsonListStr = None,
        bdf: JsonListStr = None,
        vlan: JsonListStr = None,
        ip_subnet: JsonListStr = None,
        ip_v4: JsonListStr = None,
        ip_v6: JsonListStr = None,
        site: JsonListStr = None,
        host: JsonListStr = None,
        facility: JsonListStr = None,
        project_type: JsonListStr = None,
        user_active: Optional[bool] = True,
        exclude_user_id: JsonListStr = None,
        exclude_user_email: JsonListStr = None,
        exclude_project_id: JsonListStr = None,
        exclude_site: JsonListStr = None,
        exclude_host: JsonListStr = None,
        exclude_slice_state: JsonListStr = None,
        exclude_sliver_state: JsonListStr = None,
        exclude_project_type: JsonListStr = None,
        page: int = 0,
        per_page: int = 1000,
        fetch_all: bool = True,
) -> Dict[str, Any]:
    """
    Query FABRIC users with relationship and activity-based filtering.

    Retrieve user information with flexible filtering based on their project
    memberships, slice ownership, resource usage, and activity status. Useful
    for identifying active users, finding users by their experiments, or
    analyzing user communities.

    Args:
        start_time: ISO8601 timestamp - filter users with activity after this time
        end_time: ISO8601 timestamp - filter users with activity before this time
        user_id: List of specific user UUIDs to retrieve
        user_email: List of user email addresses to retrieve
        project_id: Filter users who are members of these projects
        slice_id: Filter users who own these slices
        slice_state: Filter users with slices in these states
        sliver_id: Filter users who own slices containing these slivers
        sliver_type: Filter users utilizing these sliver types
        sliver_state: Filter users with slivers in these states
        component_type: Filter users utilizing these component types
        component_model: Filter by specific hardware models used
        bdf: Filter by PCI Bus-Device-Function identifiers
        vlan: Filter by VLAN tags in user's resources
        ip_subnet: Filter by IP subnets used
        ip_v4: Filter by IPv4 addresses assigned to user resources
        ip_v6: Filter by IPv6 addresses assigned to user resources
        site: Filter users with resources at these sites
        host: Filter users with resources on these hosts
        facility: Filter by facility type
        project_type: Filter users by project types they belong to (research,
                      education, accept, test)
        user_active: If True, return only active users; if False, only inactive
        exclude_user_id: Exclude these user UUIDs
        exclude_user_email: Exclude these user emails
        exclude_project_id: Exclude users from these projects
        exclude_site: Exclude users with resources at these sites
        exclude_host: Exclude users with resources on these hosts
        exclude_slice_state: Exclude users with slices in these states
        exclude_sliver_state: Exclude users with slivers in these states
        exclude_project_type: Exclude users from these project types
        page: Page number for pagination (0-indexed)
        per_page: Number of results per page (max 1000)
        fetch_all: If True, automatically fetch all pages

    Returns:
        Dict containing list of users with details including user_id (UUID),
        email, name, active status, associated projects, and resource usage.

    Examples:
        - Active users with GPU allocations: user_active=True, component_type=["GPU"]
        - Users in research projects: project_type=["research"]
        - Users with failed slices: slice_state=["Dead", "StableError"]
    """
    logger.info("Executing query-users")
    client = _get_client(_get_headers())
    result = await _call(
        client, "query_users",
        start_time=start_time, end_time=end_time,
        user_id=user_id, user_email=user_email, project_id=project_id,
        slice_id=slice_id, slice_state=slice_state,
        sliver_id=sliver_id, sliver_type=sliver_type, sliver_state=sliver_state,
        component_type=component_type, component_model=component_model,
        bdf=bdf, vlan=vlan, ip_subnet=ip_subnet, ip_v4=ip_v4, ip_v6=ip_v6,
        site=site, host=host, facility=facility,
        project_type=project_type, user_active=user_active,
        exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
        exclude_project_id=exclude_project_id, exclude_site=exclude_site,
        exclude_host=exclude_host, exclude_slice_state=exclude_slice_state,
        exclude_sliver_state=exclude_sliver_state,
        exclude_project_type=exclude_project_type,
        page=page, per_page=per_page, fetch_all=fetch_all,
    )
    logger.info("query-users completed")
    return result


@mcp.tool(name="query-projects", title="Query Projects")
async def query_projects(
        toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: JsonListStr = None,
        user_email: JsonListStr = None,
        project_id: JsonListStr = None,
        slice_id: JsonListStr = None,
        slice_state: JsonListStr = None,
        sliver_id: JsonListStr = None,
        sliver_type: JsonListStr = None,
        sliver_state: JsonListStr = None,
        component_type: JsonListStr = None,
        component_model: JsonListStr = None,
        bdf: JsonListStr = None,
        vlan: JsonListStr = None,
        ip_subnet: JsonListStr = None,
        ip_v4: JsonListStr = None,
        ip_v6: JsonListStr = None,
        site: JsonListStr = None,
        host: JsonListStr = None,
        facility: JsonListStr = None,
        project_type: JsonListStr = None,
        project_active: Optional[bool] = True,
        exclude_user_id: JsonListStr = None,
        exclude_user_email: JsonListStr = None,
        exclude_project_id: JsonListStr = None,
        exclude_site: JsonListStr = None,
        exclude_host: JsonListStr = None,
        exclude_slice_state: JsonListStr = None,
        exclude_sliver_state: JsonListStr = None,
        exclude_project_type: JsonListStr = None,
        page: int = 0,
        per_page: int = 1000,
        fetch_all: bool = True,
) -> Dict[str, Any]:
    """
    Query FABRIC projects with membership, activity, and resource-based filtering.

    Projects are organizational units that group users and their experimental
    resources. Use this endpoint to find projects by type, activity status,
    member composition, or resource utilization patterns.

    Args:
        start_time: ISO8601 timestamp - filter projects with activity after this time
        end_time: ISO8601 timestamp - filter projects with activity before this time
        user_id: Filter projects containing these user UUIDs as members
        user_email: Filter projects containing these user emails as members
        project_id: List of specific project UUIDs to retrieve
        slice_id: Filter projects that own these slices
        slice_state: Filter projects with slices in these states
        sliver_id: Filter projects with slices containing these slivers
        sliver_type: Filter projects utilizing these sliver types
        sliver_state: Filter projects with slivers in these states
        component_type: Filter projects utilizing these component types (GPU,
                        SmartNIC, SharedNIC, FPGA, NVME, Storage)
        component_model: Filter by specific hardware models used
        bdf: Filter by PCI Bus-Device-Function identifiers
        vlan: Filter by VLAN tags in project's resources
        ip_subnet: Filter by IP subnets used
        ip_v4: Filter by IPv4 addresses assigned to project resources
        ip_v6: Filter by IPv6 addresses assigned to project resources
        site: Filter projects with resources at these sites
        host: Filter projects with resources on these hosts
        facility: Filter by facility type
        project_type: Filter by project types (research, education, accept, test)
        project_active: If True, return only active projects; if False, only inactive
        exclude_user_id: Exclude projects containing these user UUIDs
        exclude_user_email: Exclude projects containing these user emails
        exclude_project_id: Exclude these project UUIDs (useful for filtering
                            out FABRIC personnel projects)
        exclude_site: Exclude projects with resources at these sites
        exclude_host: Exclude projects with resources on these hosts
        exclude_slice_state: Exclude projects with slices in these states
        exclude_sliver_state: Exclude projects with slivers in these states
        exclude_project_type: Exclude these project types
        page: Page number for pagination (0-indexed)
        per_page: Number of results per page (max 1000)
        fetch_all: If True, automatically fetch all pages

    Returns:
        Dict containing list of projects with details including project_id (UUID),
        name, description, type, active status, member count, created/modified dates,
        and resource usage summary.

    Examples:
        - Active research projects: project_active=True, project_type=["research"]
        - Projects using GPUs at RENC: component_type=["GPU"], site=["RENC"]
        - Exclude FABRIC personnel: exclude_project_id=[list of FABRIC project UUIDs]
    """
    logger.info("Executing query-projects")
    client = _get_client(_get_headers())
    result = await _call(
        client, "query_projects",
        start_time=start_time, end_time=end_time,
        user_id=user_id, user_email=user_email,
        project_id=project_id, slice_id=slice_id, slice_state=slice_state,
        sliver_id=sliver_id, sliver_type=sliver_type, sliver_state=sliver_state,
        component_type=component_type, component_model=component_model,
        bdf=bdf, vlan=vlan, ip_subnet=ip_subnet, ip_v4=ip_v4, ip_v6=ip_v6,
        site=site, host=host, facility=facility,
        project_type=project_type, project_active=project_active,
        exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
        exclude_project_id=exclude_project_id, exclude_site=exclude_site,
        exclude_host=exclude_host, exclude_slice_state=exclude_slice_state,
        exclude_sliver_state=exclude_sliver_state,
        exclude_project_type=exclude_project_type,
        page=page, per_page=per_page, fetch_all=fetch_all,
    )
    logger.info("query-projects completed")
    return result


@mcp.tool(name="query-user-memberships", title="Query User Memberships")
async def query_user_memberships(
        toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: JsonListStr = None,
        user_email: JsonListStr = None,
        exclude_user_id: JsonListStr = None,
        exclude_user_email: JsonListStr = None,
        project_type: JsonListStr = ["research", "education"],
        exclude_project_type: JsonListStr = None,
        project_active: Optional[bool] = True,
        project_expired: Optional[bool] = None,
        project_retired: Optional[bool] = None,
        user_active: Optional[bool] = True,
        page: int = 0,
        per_page: int = 500,
        fetch_all: bool = True,
) -> Dict[str, Any]:
    """
    Query user-to-project membership relationships.

    Returns user-centric views of project memberships, showing which projects
    each user belongs to, their roles, and membership status. Useful for
    understanding user participation across projects and identifying user
    communities.

    Args:
        start_time: ISO8601 timestamp - filter memberships created after this time
        end_time: ISO8601 timestamp - filter memberships created before this time
        user_id: List of user UUIDs to retrieve memberships for
        user_email: List of user emails to retrieve memberships for
        exclude_user_id: Exclude memberships for these user UUIDs
        exclude_user_email: Exclude memberships for these user emails
        project_type: Filter by project types (research, education, accept, test)
        exclude_project_type: Exclude these project types
        project_active: If True, only include memberships in active projects
        project_expired: If True, only include memberships in expired projects
        project_retired: If True, only include memberships in retired projects
        user_active: If True, only include active users
        page: Page number for pagination (0-indexed)
        per_page: Number of results per page (max 500)
        fetch_all: If True, automatically fetch all pages

    Returns:
        Dict containing list of user memberships with details including user_id,
        email, list of projects with role information (owner, member, etc.),
        and membership dates.

    Examples:
        - User's active projects: user_email=["user@example.com"], project_active=True
        - Research project memberships: project_type=["research"]
        - Active users in non-test projects: user_active=True, exclude_project_type=["test"]
    """
    logger.info("Executing query-user-memberships")
    client = _get_client(_get_headers())
    result = await _call(
        client, "query_user_memberships",
        start_time=start_time, end_time=end_time,
        user_id=user_id, user_email=user_email,
        exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
        project_type=project_type, exclude_project_type=exclude_project_type,
        project_active=project_active, project_expired=project_expired,
        project_retired=project_retired, user_active=user_active,
        page=page, per_page=per_page, fetch_all=fetch_all,
    )
    logger.info("query-user-memberships completed")
    return result


@mcp.tool(name="query-project-memberships", title="Query Project Memberships")
async def query_project_memberships(
        toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        project_id: JsonListStr = None,
        exclude_project_id: JsonListStr = None,
        project_type: JsonListStr = ["research", "education"],
        exclude_project_type: JsonListStr = None,
        project_active: Optional[bool] = True,
        project_expired: Optional[bool] = None,
        project_retired: Optional[bool] = None,
        user_active: Optional[bool] = True,
        page: int = 0,
        per_page: int = 500,
        fetch_all: bool = True,
) -> Dict[str, Any]:
    """
    Query project-to-user membership relationships.

    Returns project-centric views of memberships, showing which users belong
    to each project, their roles, and membership status. Useful for analyzing
    project team composition, identifying project owners, and tracking member
    participation.

    Args:
        start_time: ISO8601 timestamp - filter memberships created after this time
        end_time: ISO8601 timestamp - filter memberships created before this time
        project_id: List of project UUIDs to retrieve memberships for
        exclude_project_id: Exclude memberships for these project UUIDs (useful
                            for filtering out FABRIC personnel projects)
        project_type: Filter by project types (research, education, accept, test)
        exclude_project_type: Exclude these project types
        project_active: If True, only include active projects
        project_expired: If True, only include expired projects
        project_retired: If True, only include retired projects
        user_active: If True, only include active users in results
        page: Page number for pagination (0-indexed)
        per_page: Number of results per page (max 500)
        fetch_all: If True, automatically fetch all pages

    Returns:
        Dict containing list of project memberships with details including
        project_id, name, type, active status, and list of members with their
        roles (owner, member, etc.) and membership dates.

    Examples:
        - Project team roster: project_id=["uuid"]
        - Research project teams: project_type=["research"], project_active=True
        - Active members only: user_active=True
    """
    logger.info("Executing query-project-memberships")
    client = _get_client(_get_headers())
    result = await _call(
        client, "query_project_memberships",
        start_time=start_time, end_time=end_time,
        project_id=project_id, exclude_project_id=exclude_project_id,
        project_type=project_type, exclude_project_type=exclude_project_type,
        project_active=project_active, project_expired=project_expired,
        project_retired=project_retired, user_active=user_active,
        page=page, per_page=per_page, fetch_all=fetch_all,
    )
    logger.info("query-project-memberships completed")
    return result


# =========================================================================
# Entry point
# =========================================================================

if __name__ == "__main__":
    logger.info(
        "Starting FABRIC Reports MCP Server",
        extra={
            "transport_mode": settings.transport.mode,
            "api_base_url": settings.api.base_url,
            "log_level": settings.logging.level,
        },
    )

    if settings.transport.mode == "http":
        logger.info(
            "Starting HTTP server",
            extra={
                "host": settings.transport.http_host,
                "port": settings.transport.http_port,
            },
        )
        mcp.run(
            transport="http",
            host=settings.transport.http_host,
            port=settings.transport.http_port,
        )
    else:
        logger.info("Starting stdio mode")
        mcp.run(transport="stdio")
