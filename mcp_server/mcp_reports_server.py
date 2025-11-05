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
          description="Returns version info from the Reports API.",

          )
async def query_version(ctx: Context, toolCallId: Optional[str] = None,
                        tool_call_id: Optional[str] = None, ) -> Dict[str, Any]:
    client = _client_from_headers()
    return await _call(client, "query_version")


@mcp.tool(name="query-sites", title="Query Sites",
          description="Returns list of sites (no filters supported by client).",

          )
async def query_sites(ctx: Context, toolCallId: Optional[str] = None,
                      tool_call_id: Optional[str] = None, ) -> Dict[str, Any]:
    client = _client_from_headers()
    return await _call(client, "query_sites")


# ---------------------------------------
# Slices
# ---------------------------------------
@mcp.tool(
    name="query-slices",
    title="Query Slices",
    description="Query slices with rich filters. Lists accept multiple values.",

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
        exclude_slice_state: Optional[List[str]] = None,
        exclude_sliver_state: Optional[List[str]] = None,
        page: int = 0,
        per_page: int = 1000,
        fetch_all: bool = True,
) -> Dict[str, Any]:
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
    description="Query slivers with rich filters. Lists accept multiple values.",

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
        exclude_sliver_state: Optional[List[str]] = None,
        page: int = 0,
        per_page: int = 1000,
        fetch_all: bool = True,
) -> Dict[str, Any]:
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
    description="Query users with filters (slice/project relationships, activity, etc.).",

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
        user_active: Optional[bool] = None,
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
    description="Query projects with filters (activity, type, memberships, etc.).",

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
        project_active: Optional[bool] = None,
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
    description="Query user-project memberships with filters.",

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
        project_type: Optional[List[str]] = None,
        exclude_project_type: Optional[List[str]] = None,
        project_active: Optional[bool] = None,
        project_expired: Optional[bool] = None,
        project_retired: Optional[bool] = None,
        user_active: Optional[bool] = None,
        page: int = 0,
        per_page: int = 500,
        fetch_all: bool = True,
) -> Dict[str, Any]:
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
    description="Query project-user memberships with filters.",

)
async def query_project_memberships(
        ctx: Context, toolCallId: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        project_id: Optional[List[str]] = None,
        exclude_project_id: Optional[List[str]] = None,
        project_type: Optional[List[str]] = None,
        exclude_project_type: Optional[List[str]] = None,
        project_active: Optional[bool] = None,
        project_expired: Optional[bool] = None,
        project_retired: Optional[bool] = None,
        user_active: Optional[bool] = None,
        page: int = 0,
        per_page: int = 500,
        fetch_all: bool = True,
) -> Dict[str, Any]:
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
    description="Create or update a slice by slice_id.",

)
async def post_slice(
        ctx: Context,
        slice_id: str,
        slice_payload: Dict[str, Any],
) -> Dict[str, Any]:
    client = _client_from_headers()
    return await _call(client, "post_slice", slice_id=slice_id, slice_payload=slice_payload)


@mcp.tool(
    name="post-sliver",
    title="Post Sliver",
    description="Create or update a sliver by slice_id and sliver_id.",

)
async def post_sliver(
        ctx: Context,
        slice_id: str,
        sliver_id: str,
        sliver_payload: Dict[str, Any],
) -> Dict[str, Any]:
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