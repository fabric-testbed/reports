from __future__ import annotations

import os
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, List

from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.server.dependencies import get_http_headers

from fabric_reports_client.reports_api import ReportsApi

# ---------------------------------------
# Config
# ---------------------------------------
REPORTS_API_BASE_URL = os.environ.get(
    "REPORTS_API_BASE_URL",
    "https://reports.fabric-testbed.net/reports",
)
print(f"Reports API Base URL set to: {REPORTS_API_BASE_URL}")

# Meta fields various bridges may attach to tool calls
EXTRA_META_ARGS = [
    "toolCallId",  # camelCase
    "tool_call_id",  # snake_case
    "id",  # "call_tool" envelope
    "type",  # "call_tool" envelope
    "name",  # envelope alt for tool name
    "tool",  # if a wrapper redundantly includes it
]

mcp = FastMCP(
    name="fabric-reports-mcp-proxy",
    instructions="Proxy for accessing FABRIC Reports API data via LLM tool calls.",
    version="1.3.0",
)

# Load your markdown system prompt
SYSTEM_TEXT = Path("system.md").read_text(encoding="utf-8").strip()

# Define a function to load the prompt content
# The docstring becomes the prompt's description.
@mcp.prompt(name="fabric-reports-system")
def fabric_reports_system_prompt():
    """System rules for querying FABRIC Reports via MCP"""
    # FastMCP automatically wraps the string as a PromptMessage with role="system"
    # if you return it from the function. You could also return a list of PromptMessage objects.
    return SYSTEM_TEXT

# Note: The function name (or the name parameter) is the key.
# The docstring is the description.
# The return value is the prompt content/messages.

# ---------------------------------------
# Helpers
# ---------------------------------------
def _bearer_from_headers(headers: Dict[str, str]) -> Optional[str]:
    low = {k.lower(): v for k, v in headers.items()}
    auth = low.get("authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def _client_from_headers() -> ReportsApi:
    headers = get_http_headers() or {}
    token = _bearer_from_headers(headers)
    if not token:
        raise ValueError("Authentication Required: Missing or invalid Authorization Bearer token.")
    return ReportsApi(base_url=REPORTS_API_BASE_URL, token=token)


async def _call(client: ReportsApi, method: str, **kwargs) -> Dict[str, Any]:
    """
    Call a ReportsApi method in a thread, filtering out None args.
    """
    fn = getattr(client, method)
    final_args = {k: v for k, v in kwargs.items() if v is not None}
    return await asyncio.to_thread(fn, **final_args)


# ---------------------------------------
# Simple endpoints
# ---------------------------------------
@mcp.tool(name="query-version", title="Query Version",
          description="Get API version, build info, and service status. Use to verify API availability and compatibility."
          )
async def query_version(ctx: Context, toolCallId: Optional[str] = None,
                        tool_call_id: Optional[str] = None, ) -> Dict[str, Any]:
    """
    Retrieve version information from the FABRIC Reports API.

    Returns the current API version, build information, and service status.
    Useful for verifying API availability and compatibility.

    Returns:
        Dict containing version details including version number, git commit,
        and service metadata.
    """
    client = _client_from_headers()
    return await _call(client, "query_version")


@mcp.tool(name="query-sites", title="Query Sites",
          description="Get all FABRIC testbed sites with location, capacity, and available resources (GPUs, FPGAs, SmartNICs). No filters available - returns complete site list."
          )
async def query_sites(ctx: Context, toolCallId: Optional[str] = None,
                      tool_call_id: Optional[str] = None, ) -> Dict[str, Any]:
    """
    Retrieve all FABRIC testbed sites.

    Returns a complete list of physical FABRIC sites where resources are located.
    Each site includes information about location, capacity, and available resources such as GPUs, FPGAs, SmartNICs.

    Note: This endpoint does not support filtering.

    Returns:
        Dict containing list of sites with details including site name, ID,
        location, and resource capacities.
    """
    client = _client_from_headers()
    return await _call(client, "query_sites")


# ---------------------------------------
# Slices
# ---------------------------------------
@mcp.tool(
    name="query-slices",
    title="Query Slices",
    description="Query FABRIC experimental slices (user environments containing resources). Filter by state (StableOK, StableError, Dead, etc.), user, project, site, time range, or resource types (GPU, SmartNIC, etc.). Use exclude_slice_state to filter out terminated slices. Default excludes Dead and Closing states."
)
async def query_slices(
        ctx: Context, toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: Optional[List[str]] = None,
        user_email: Optional[List[str]] = None,
        project_id: Optional[List[str]] = None,
        slice_id: Optional[List[str]] = None,
        slice_state: Optional[List[str]] = None,
        sliver_id: Optional[List[str]] = None,
        sliver_type: Optional[List[str]] = None,
        sliver_state: Optional[List[str]] = None,
        component_type: Optional[List[str]] = None,
        component_model: Optional[List[str]] = None,
        bdf: Optional[List[str]] = None,
        vlan: Optional[List[str]] = None,
        ip_subnet: Optional[List[str]] = None,
        ip_v4: Optional[List[str]] = None,
        ip_v6: Optional[List[str]] = None,
        site: Optional[List[str]] = None,
        host: Optional[List[str]] = None,
        facility: Optional[List[str]] = None,
        exclude_user_id: Optional[List[str]] = None,
        exclude_user_email: Optional[List[str]] = None,
        exclude_project_id: Optional[List[str]] = None,
        exclude_site: Optional[List[str]] = None,
        exclude_host: Optional[List[str]] = None,
        exclude_slice_state: Optional[List[str]] = ["Dead", "Closing"],
        exclude_sliver_state: Optional[List[str]] = None,
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
        - Active slices at EDC site: slice_state=["StableOK", "StableError"], site=["EDC"]
        - User's slices: user_email=["user@example.com"]
        - Slices with GPUs: component_type=["GPU"]
    """
    client = _client_from_headers()
    return await _call(
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


# ---------------------------------------
# Slivers
# ---------------------------------------
@mcp.tool(
    name="query-slivers",
    title="Query Slivers",
    description="Query individual resource allocations (VMs, network connections, storage). Filter by sliver_type (VM, L2PTP, FABNetv4, etc.), sliver_state (Active, Failed, Closed, etc.), component_type (GPU, SmartNIC, FPGA, NVME, Storage), site, host, or time range. Use for detailed resource utilization tracking. Default excludes Closed slivers."
)
async def query_slivers(
        ctx: Context, toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: Optional[List[str]] = None,
        user_email: Optional[List[str]] = None,
        project_id: Optional[List[str]] = None,
        slice_id: Optional[List[str]] = None,
        slice_state: Optional[List[str]] = None,
        sliver_id: Optional[List[str]] = None,
        sliver_type: Optional[List[str]] = None,
        sliver_state: Optional[List[str]] = None,
        component_type: Optional[List[str]] = None,
        component_model: Optional[List[str]] = None,
        bdf: Optional[List[str]] = None,
        vlan: Optional[List[str]] = None,
        ip_subnet: Optional[List[str]] = None,
        ip_v4: Optional[List[str]] = None,
        ip_v6: Optional[List[str]] = None,
        site: Optional[List[str]] = None,
        host: Optional[List[str]] = None,
        facility: Optional[List[str]] = None,
        exclude_user_id: Optional[List[str]] = None,
        exclude_user_email: Optional[List[str]] = None,
        exclude_project_id: Optional[List[str]] = None,
        exclude_site: Optional[List[str]] = None,
        exclude_host: Optional[List[str]] = None,
        exclude_slice_state: Optional[List[str]] = None,
        exclude_sliver_state: Optional[List[str]] = ["Closed"],
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
        - Active VM slivers: sliver_type=["VM"], sliver_state=["Active"]
        - SmartNIC allocations at RENC: component_type=["SmartNIC"], site=["RENC"]
        - Failed slivers in last 24h: sliver_state=["Failed"], start_time="2025-01-09T00:00:00Z"
    """
    client = _client_from_headers()
    return await _call(
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


# ---------------------------------------
# Users
# ---------------------------------------
@mcp.tool(
    name="query-users",
    title="Query Users",
    description="Query FABRIC users filtered by activity, project membership, resource usage, or experiments. Filter by user_active (default: true), project_type (research/education/test), component_type, site, or slice ownership. Use to identify active users, find users by experiments, or analyze user communities."
)
async def query_users(
        ctx: Context, toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: Optional[List[str]] = None,
        user_email: Optional[List[str]] = None,
        project_id: Optional[List[str]] = None,
        slice_id: Optional[List[str]] = None,
        slice_state: Optional[List[str]] = None,
        sliver_id: Optional[List[str]] = None,
        sliver_type: Optional[List[str]] = None,
        sliver_state: Optional[List[str]] = None,
        component_type: Optional[List[str]] = None,
        component_model: Optional[List[str]] = None,
        bdf: Optional[List[str]] = None,
        vlan: Optional[List[str]] = None,
        ip_subnet: Optional[List[str]] = None,
        ip_v4: Optional[List[str]] = None,
        ip_v6: Optional[List[str]] = None,
        site: Optional[List[str]] = None,
        host: Optional[List[str]] = None,
        facility: Optional[List[str]] = None,
        project_type: Optional[List[str]] = None,
        user_active: Optional[bool] = True,
        exclude_user_id: Optional[List[str]] = None,
        exclude_user_email: Optional[List[str]] = None,
        exclude_project_id: Optional[List[str]] = None,
        exclude_site: Optional[List[str]] = None,
        exclude_host: Optional[List[str]] = None,
        exclude_slice_state: Optional[List[str]] = None,
        exclude_sliver_state: Optional[List[str]] = None,
        exclude_project_type: Optional[List[str]] = None,
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
    client = _client_from_headers()
    return await _call(
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


# ---------------------------------------
# Projects
# ---------------------------------------
@mcp.tool(
    name="query-projects",
    title="Query Projects",
    description="Query FABRIC projects (organizational units grouping users and resources). Filter by project_active (default: true), project_type (research/education/test), members, resource usage, or site. Use exclude_project_id to filter out FABRIC personnel projects. Useful for finding projects by activity, team composition, or resource patterns."
)
async def query_projects(
        ctx: Context, toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: Optional[List[str]] = None,
        user_email: Optional[List[str]] = None,
        project_id: Optional[List[str]] = None,
        slice_id: Optional[List[str]] = None,
        slice_state: Optional[List[str]] = None,
        sliver_id: Optional[List[str]] = None,
        sliver_type: Optional[List[str]] = None,
        sliver_state: Optional[List[str]] = None,
        component_type: Optional[List[str]] = None,
        component_model: Optional[List[str]] = None,
        bdf: Optional[List[str]] = None,
        vlan: Optional[List[str]] = None,
        ip_subnet: Optional[List[str]] = None,
        ip_v4: Optional[List[str]] = None,
        ip_v6: Optional[List[str]] = None,
        site: Optional[List[str]] = None,
        host: Optional[List[str]] = None,
        facility: Optional[List[str]] = None,
        project_type: Optional[List[str]] = None,
        project_active: Optional[bool] = True,
        exclude_user_id: Optional[List[str]] = None,
        exclude_user_email: Optional[List[str]] = None,
        exclude_project_id: Optional[List[str]] = None,
        exclude_site: Optional[List[str]] = None,
        exclude_host: Optional[List[str]] = None,
        exclude_slice_state: Optional[List[str]] = None,
        exclude_sliver_state: Optional[List[str]] = None,
        exclude_project_type: Optional[List[str]] = None,
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
    client = _client_from_headers()
    return await _call(
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


# ---------------------------------------
# Memberships
# ---------------------------------------
@mcp.tool(
    name="query-user-memberships",
    title="Query User Memberships",
    description="Get user-centric view of project memberships showing which projects each user belongs to with roles. Filter by user_active (default: true), project_type (default: research, education), project_active (default: true), or project status. Use to understand user participation across projects."
)
async def query_user_memberships(
        ctx: Context, toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        user_id: Optional[List[str]] = None,
        user_email: Optional[List[str]] = None,
        exclude_user_id: Optional[List[str]] = None,
        exclude_user_email: Optional[List[str]] = None,
        project_type: Optional[List[str]] = ["research", "education"],
        exclude_project_type: Optional[List[str]] = None,
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
    client = _client_from_headers()
    return await _call(
        client, "query_user_memberships",
        start_time=start_time, end_time=end_time,
        user_id=user_id, user_email=user_email,
        exclude_user_id=exclude_user_id, exclude_user_email=exclude_user_email,
        project_type=project_type, exclude_project_type=exclude_project_type,
        project_active=project_active, project_expired=project_expired,
        project_retired=project_retired, user_active=user_active,
        page=page, per_page=per_page, fetch_all=fetch_all,
    )


@mcp.tool(
    name="query-project-memberships",
    title="Query Project Memberships",
    description="Get project-centric view of memberships showing which users belong to each project with roles. Filter by project_type (default: research, education), project_active (default: true), user_active (default: true), or project status. Use to analyze team composition and identify project owners."
)
async def query_project_memberships(
        ctx: Context, toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        project_id: Optional[List[str]] = None,
        exclude_project_id: Optional[List[str]] = None,
        project_type: Optional[List[str]] = ["research", "education"],
        exclude_project_type: Optional[List[str]] = None,
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
    client = _client_from_headers()
    return await _call(
        client, "query_project_memberships",
        start_time=start_time, end_time=end_time,
        project_id=project_id, exclude_project_id=exclude_project_id,
        project_type=project_type, exclude_project_type=exclude_project_type,
        project_active=project_active, project_expired=project_expired,
        project_retired=project_retired, user_active=user_active,
        page=page, per_page=per_page, fetch_all=fetch_all,
    )


# ---------------------------------------
# POST helpers (optional tools)
# ---------------------------------------
@mcp.tool(
    name="post-slice",
    title="Post Slice",
    description="Administrative endpoint to create or update slice records in Reports database. Requires slice_id and slice_payload with state, name, project_id, user_id, timestamps. Use for data import/sync operations only, not regular queries."
)
async def post_slice(
        ctx: Context,
        slice_id: str,
        slice_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create or update a slice in the Reports database.

    This endpoint allows programmatic creation or updating of slice records.
    Typically used for data import/sync operations rather than regular queries.
    Requires appropriate authentication and permissions.

    Args:
        slice_id: The unique UUID of the slice to create or update
        slice_payload: Dict containing slice data including state, name,
                       project_id, user_id, created_time, and other slice attributes

    Returns:
        Dict with operation status and created/updated slice information.

    Note:
        This is an administrative endpoint primarily used for data synchronization
        from other FABRIC systems into the Reports database.
    """
    client = _client_from_headers()
    return await _call(client, "post_slice", slice_id=slice_id, slice_payload=slice_payload)


@mcp.tool(
    name="post-sliver",
    title="Post Sliver",
    description="Administrative endpoint to create or update sliver records in Reports database. Requires slice_id, sliver_id, and sliver_payload with state, type, site, host, components, interfaces. Use for data import/sync from orchestrator/controllers only, not regular queries."
)
async def post_sliver(
        ctx: Context,
        slice_id: str,
        sliver_id: str,
        sliver_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create or update a sliver within a slice in the Reports database.

    This endpoint allows programmatic creation or updating of sliver records
    (individual resource allocations). Typically used for data import/sync
    operations rather than regular queries. Requires appropriate authentication
    and permissions.

    Args:
        slice_id: The unique UUID of the parent slice
        sliver_id: The unique UUID of the sliver to create or update
        sliver_payload: Dict containing sliver data including state, type,
                        site, host, components, interfaces, and other attributes

    Returns:
        Dict with operation status and created/updated sliver information.

    Note:
        This is an administrative endpoint primarily used for data synchronization
        from other FABRIC systems (orchestrator, controllers) into the Reports
        database.
    """
    client = _client_from_headers()
    return await _call(
        client, "post_sliver",
        slice_id=slice_id, sliver_id=sliver_id, sliver_payload=sliver_payload
    )


# ---------------------------------------
# Run
# ---------------------------------------
if __name__ == "__main__":
    import os

    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting FABRIC Reports MCP (FastMCP) on http://{host}:{port}")
    mcp.run(transport="http", host=host, port=port)