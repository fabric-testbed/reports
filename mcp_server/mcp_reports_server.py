from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import asyncio
import os
import inspect

# Import your ReportsApi client class
from fabric_reports_client.reports_api import ReportsApi

# --- Configuration ---
MCP_SERVER_VERSION = "1.3.0"
DEFAULT_BASE_URL = "https://reports.fabric-testbed.net/reports"
REPORTS_API_BASE_URL = os.environ.get("REPORTS_API_BASE_URL", DEFAULT_BASE_URL)
print(f"Reports API Base URL set to: {REPORTS_API_BASE_URL}")


# --- Pydantic Models for MCP and Tool Call Handling ---
class CallParams(BaseModel):
    """Structure for the 'params' in a tool/call request."""
    name: str = Field(..., description="The name of the tool to call.")
    # Arguments must be flexible to support all client method parameters
    arguments: Dict[str, Any] = Field(default_factory=dict, description="The arguments for the tool.")


class ToolCallRequest(BaseModel):
    """Full JSON-RPC request for a tool/call."""
    jsonrpc: str = "2.0"
    method: str = Field(..., pattern="^tools/call$")
    params: CallParams
    id: str = Field(..., description="A unique identifier for the request.")


# --- Client Generator (Replaces global client) ---
def get_reports_client(token: str) -> ReportsApi:
    """Creates a ReportsApi client instance with the provided token."""
    if not token:
        # Raise an exception if token is missing
        raise ValueError("Authorization token is missing or invalid.")

    # Instantiate the client for this specific request
    return ReportsApi(base_url=REPORTS_API_BASE_URL, token=token)


# --- Helper Function to Generate Tool Parameters from Client Signature ---
def generate_tool_parameters(client_method, include_params: Optional[List[str]] = None) -> Dict[str, Any]:
    """Dynamically generates the OpenAPI/JSON schema for a client method."""

    signature = inspect.signature(client_method)
    docstring = client_method.__doc__ or ""
    function_description = docstring.strip().split('\n')[0].strip()

    # Parameters to ignore, as they are handled internally by the client or the MCP server
    ignore_params = ['self', 'token_file', 'token', 'base_url', 'page', 'per_page', 'fetch_all', 'slice_payload',
                     'sliver_payload']

    properties = {}
    required = []

    for name, param in signature.parameters.items():
        if name in ignore_params:
            continue

        # If specific parameters were requested, only include those
        if include_params is not None and name not in include_params:
            continue

        # Simplistic type mapping for LLM guidance
        param_type = "string"
        description = f"Filter for {name}."

        # Heuristic for common filter types based on your client's structure
        if param.annotation in (list[str], list[int], list[Any]) or name.endswith('_id') or name.endswith('_ids'):
            param_type = "array"
            description = f"List of string IDs or values to filter by {name}."
        elif param.annotation is bool or name.startswith(('is_', 'exclude_')):
            param_type = "boolean"
            description = f"Boolean filter for {name} (True/False)."
        elif 'time' in name:
            param_type = "string"
            description = "Start or end time for filtering (e.g., 'YYYY-MM-DD')."

        properties[name] = {"type": param_type, "description": description}

        # Parameters with no default value are generally considered required
        if param.default is param.empty and param.annotation is not Optional:
            required.append(name)

    # Manually adding required/special payload parameters for POST/PUT methods
    if client_method.__name__ == 'post_sliver':
        properties['slice_id'] = {"type": "string", "description": "UUID of the slice for the sliver."}
        properties['sliver_payload'] = {"type": "object",
                                        "description": "The JSON payload containing the sliver specification (core, ram, host, etc.)."}
        required.extend(['slice_id', 'sliver_payload'])
    elif client_method.__name__ == 'post_slice':
        properties['slice_id'] = {"type": "string", "description": "UUID of the slice to create/update."}
        properties['slice_payload'] = {"type": "object",
                                       "description": "The JSON payload containing the slice specification (lease_start, lease_end, state, etc.)."}
        required.extend(['slice_id', 'slice_payload'])

    return {
        "description": function_description,
        "function": {
            "name": client_method.__name__.replace('_', '-'),  # LLM standard naming convention
            "description": function_description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        },
        # Store the actual unbound method (not yet attached to an instance)
        "client_method": client_method
    }


# --- Tool Definitions (Dynamically generated using client methods) ---
# We instantiate a dummy client just to get the unbound methods for inspection
_dummy_client = ReportsApi(base_url="http://dummy", token="dummy")

TOOL_DEFINITIONS = {
    "query-version": generate_tool_parameters(_dummy_client.query_version),
    "query-sites": generate_tool_parameters(_dummy_client.query_sites),
    "query-users": generate_tool_parameters(_dummy_client.query_users),
    "query-projects": generate_tool_parameters(_dummy_client.query_projects),
    "query-slices": generate_tool_parameters(_dummy_client.query_slices),
    "query-slivers": generate_tool_parameters(_dummy_client.query_slivers),
    "query-user-memberships": generate_tool_parameters(_dummy_client.query_user_memberships),
    "query-project-memberships": generate_tool_parameters(_dummy_client.query_project_memberships),
    #"post-sliver": generate_tool_parameters(_dummy_client.post_sliver),
    #"post-slice": generate_tool_parameters(_dummy_client.post_slice),
}

# --- FastAPI Application Setup ---
app = FastAPI(
    title="FABRIC Reports MCP Server",
    description="A Python-based Micro-Context Protocol (MCP) server for querying FABRIC reports data.",
    version=MCP_SERVER_VERSION
)


# --- MCP Endpoints ---

@app.get("/capabilities", summary="List all LLM-invocable tools (MCP)")
async def get_capabilities():
    """
    Implements the /capabilities endpoint required by the Model Context Protocol.
    This informs the LLM what tools are available, including comprehensive filters.
    """
    capabilities = []
    for name, tool in TOOL_DEFINITIONS.items():
        capabilities.append({
            "name": tool["function"]["name"],
            "type": "tool",
            "function": tool["function"]
        })

    return {
        "version": MCP_SERVER_VERSION,
        "name": "fabric-reports-mcp-proxy",
        "description": "Proxy for accessing FABRIC Reports API data via LLM tool calls.",
        "capabilities": capabilities,
    }


@app.post("/mcp", summary="Execute a tool call (MCP JSON-RPC)")
async def mcp_handler(request: Request, tool_call_request: ToolCallRequest):
    """
    Implements the /mcp endpoint to handle JSON-RPC tool/call requests from the LLM.
    Handles per-request token extraction and client instantiation.
    """
    tool_name = tool_call_request.params.name
    tool_args = tool_call_request.params.arguments
    request_id = tool_call_request.id

    if tool_name not in TOOL_DEFINITIONS:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": f"Method not found: '{tool_name}' is not a recognized tool."},
            "id": request_id,
        }

    # --- 1. Extract Token from Authorization Header ---
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32000,
                      "message": "Authentication Required: Missing or invalid Authorization Bearer token."},
            "id": request_id,
        }

    token = auth_header.split(" ")[1]

    try:
        # --- 2. Create Request-Scoped Client ---
        client = get_reports_client(token)
        tool = TOOL_DEFINITIONS[tool_name]

        # Bind the handler method to the new client instance
        handler = getattr(client, tool["client_method"].__name__)

        # --- 3. Prepare Arguments ---
        # Filter out None values and set fetch_all=True for query methods
        final_args = {k: v for k, v in tool_args.items() if v is not None}
        if tool_name.startswith('query-'):
            final_args['fetch_all'] = True

        # --- 4. Call the blocking client method ---
        # Use asyncio.to_thread to run the synchronous client call without blocking FastAPI
        result_data = await asyncio.to_thread(handler, **final_args)

        # Standard JSON-RPC success response
        total_count = result_data.get('total', result_data.get('size', 'N/A'))

        return {
            "jsonrpc": "2.0",
            "result": {
                "content": [{
                    "type": "text",
                    "text": f"Successfully invoked tool '{tool_name}'. Query returned a total of {total_count} records. The full data payload is in the 'payload' field."
                }],
                "payload": result_data
            },
            "id": request_id,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()

        error_message = f"API Client Error: {str(e)}"

        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal server error during tool '{tool_name}' call: {error_message}",
            },
            "id": request_id,
        }


# --- Server Execution ---
if __name__ == "__main__":
    import uvicorn

    print(f"Starting FABRIC Reports MCP Server on http://0.0.0.0:5000")
    print(f"Reports API Base URL: {REPORTS_API_BASE_URL}")
    print("Test /capabilities endpoint: http://127.0.0.1:5000/capabilities")
    uvicorn.run(app, host="0.0.0.0", port=5000)
