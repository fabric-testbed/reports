# FABRIC Reports MCP Server

The **Reports MCP Server** is a lightweight Model Context Protocol (MCP) bridge that exposes the [FABRIC Reports API](https://reports.fabric-testbed.net/reports) as a toolset that can be queried directly by LLMs, N8n workflows, or any MCP-compatible client.

It provides a structured, secure interface for querying **users**, **projects**, **slices**, **slivers**, **components**, and **sites** — while enforcing domain constraints, normalization rules, and optional project exclusion filters.


## Features

* MCP-compliant endpoints (`/mcp/capabilities`, `/mcp/call_tool`)
* Bridges to the official **FABRIC Reports API**
* Modular tool definitions for:

  * `query-users`
  * `query-projects`
  * `query-slices`
  * `query-slivers`
  * `query-components`
  * `query-sites`
* Supports additional metadata fields (`toolCallId`, `id`, etc.) gracefully
* Domain-optimized prompts for N8n and LLM agents (see [`PROMPTS.md`](./PROMPTS.md))
* Dockerized for easy deployment and integration behind nginx or Vouch Proxy


## Architecture

```
[MCP Client or N8n LLM Node]
          │
          ▼
   Reports MCP Server  (FastAPI + fastmcp)
          │
          ▼
     Reports API
          │
          ▼
      PostgreSQL
```


## Quick Start

### 1. Clone and build

```bash
git clone https://github.com/fabric-testbed/reports.git
cd reports/mcp_server
docker build -t reports-mcp-server .
```

### 2. Run directly with Docker

```bash
docker run -d \
  -e REPORTS_API_BASE_URL=https://reports.fabric-testbed.net/reports \
  -p 5000:5000 \
  reports-mcp-server
```

### 3. Verify

Check available tools:

```bash
curl -s http://localhost:5000/mcp/capabilities | jq .
```

Call a tool (example):

```bash
curl -s -X POST http://localhost:5000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{"name": "query_projects", "arguments": {"limit": 3}}' | jq .
```


## Configuration

### Environment Variables

| Variable               | Description                                                 | Default                                      |
| ---------------------- | ----------------------------------------------------------- | -------------------------------------------- |
| `REPORTS_API_BASE_URL` | Base URL for the Reports API (used internally by the proxy) | `https://reports.fabric-testbed.net/reports` |
| `PORT`                 | Local port to run the server                                | `5000`                                       |
| `HOST`                 | Host binding for uvicorn                                    | `0.0.0.0`                                    |


## Structure

| File                    | Purpose                                                      |
| ----------------------- | ------------------------------------------------------------ |
| `mcp_reports_server.py` | FastAPI + fastmcp-based MCP implementation                   |
| `PROMPTS.md`            | System prompts and operational rules for LLM clients (v1/v2) |
| `requirements.txt`      | Python dependencies                                          |
| `Dockerfile`            | Container build instructions                                 |


## Local Development

### Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the server

```bash
python mcp_reports_server.py
```

Access it at:
→ [http://localhost:5000/mcp/capabilities](http://localhost:5000/mcp/capabilities)
→ [http://localhost:5000/mcp/call_tool](http://localhost:5000/mcp/call_tool)


## Integration with Reverse Proxy

If you deploy this in production behind nginx or Vouch Proxy (SSO), you can map it like:

```nginx
location /mcp/ {
    proxy_pass http://reports-mcp-server:5000/;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Optional: use Vouch `/validate` to protect `/mcp/` routes with OAuth-based login.


## API Overview

### `GET /mcp/capabilities`

Returns a JSON object describing available tools and schemas.

### `POST /mcp/call_tool`

Executes a single tool call.
Example payload:

```json
{
  "name": "query_slices",
  "arguments": {
    "state": ["StableOK", "StableError"],
    "site": "EDC"
  }
}
```

### Example Response

```json
{
  "name": "query_slices",
  "result": [
    {"slice_id": "s123", "state": "StableOK", "project": "FABRIC-Example"},
    {"slice_id": "s124", "state": "StableError", "project": "FABRIC-Example"}
  ]
}
```


## Prompts for LLM Integration

See [`PROMPTS.md`](./PROMPTS.md) for:

* N8n system prompts (Version 1 and 2)
* Behavior rules for filtering, summarization, and FABRIC project exclusion
* Domain-specific canonical enumerations (slice/sliver/component states)

These prompts ensure any connected LLM consistently queries the MCP tools correctly and formats responses safely.


## Dependencies

From [`requirements.txt`](./requirements.txt):

```
fastapi
uvicorn
pydantic
requests
fabric_reports_client
fastmcp
```


## Security

* The MCP server itself does not manage authentication.
  Place it behind a reverse proxy or integrate SSO via Vouch Proxy.
* Use HTTPS in all deployments.
* Avoid exposing `/mcp/` endpoints publicly without access control.


## Example n8n Integration

In an N8n LLM node:

* **System Prompt:** contents from `PROMPTS.md`
* **Tool Name:** `reports-mcp-server`
* **Base URL:** `https://your-host/mcp/`
* **Authentication:** handled by n8n credentials or proxy

The node can then use `query_projects`, `query_slices`, etc., automatically using MCP conventions.


## Example Use Cases

* Ask an LLM: *“List all active slices at site RENC”*
  → Internally calls: `query-slices(site="RENC", state=["StableOK","StableError"])`

* Ask an LLM: *“Show projects excluding FABRIC personnel”*
  → Internally calls: `query-projects(exclude_fabric_projects=True)`

## Usage

### Using the MCP Server in VS Code

You can interact with this MCP server directly from **VS Code Chat** using the built-in MCP client.
To get started, follow the detailed setup guide in [`vscode/README.md`](vscode/README.md).

Once configured, start the MCP server from VS Code, select your custom chat mode, and begin querying FABRIC data directly through the Chat interface.


## Maintainer

Komal Thareja

