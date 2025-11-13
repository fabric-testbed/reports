# FABRIC Reports MCP Server

The **Reports MCP Server** is a lightweight Model Context Protocol (MCP) bridge that exposes the [FABRIC Reports API](https://reports.fabric-testbed.net/reports) as a toolset that can be queried directly by LLMs, N8n workflows, or any MCP-compatible client.

It provides a structured, secure interface for querying **users**, **projects**, **slices**, **slivers**, **components**, and **sites** — while enforcing domain constraints, normalization rules, and optional project exclusion filters.

## Quick Links

- **[Claude Desktop Setup →](CLAUDE_DESKTOP_QUICKSTART.md)** - Fast setup for Claude Desktop integration
- **[Claude Desktop Configuration →](claude/stdio/README.md)** - Detailed Claude Desktop documentation
- **[Local Mode Setup](#local-mode-stdio)** - Run locally with Python or Docker

## Table of Contents
- [FABRIC Reports MCP Server](#fabric-reports-mcp-server)
  - [Features](#features)
  - [Architecture](#architecture)
  - [Deployment Options](#deployment-options)
  - [Quick Start (HTTP Mode)](#quick-start-http-mode)
    - [1. Clone and build](#1-clone-and-build)
    - [2. Run directly with Docker](#2-run-directly-with-docker)
    - [3. Verify](#3-verify)
  - [Local Mode (stdio)](#local-mode-stdio)
    - [Quick Start - Local](#quick-start---local)
    - [Using with Claude Code or MCP Clients](#using-with-claude-code-or-mcp-clients)
  - [Configuration](#configuration)
    - [Environment Variables](#environment-variables)
  - [Structure](#structure)
  - [Local Development](#local-development)
    - [Install dependencies](#install-dependencies)
    - [Run the server](#run-the-server)
  - [Integration with Reverse Proxy](#integration-with-reverse-proxy)
  - [API Overview](#api-overview)
    - [`GET /mcp/capabilities`](#get-mcpcapabilities)
    - [`POST /mcp/call_tool`](#post-mcpcall_tool)
  - [Prompts for LLM Integration](#prompts-for-llm-integration)
  - [Dependencies](#dependencies)
  - [Security](#security)
  - [Usage](#usage)
    - [Using the MCP Server in VS Code](#using-the-mcp-server-in-vs-code)
    - [n8n Integration](#n8n-integration)
      - [Example Queries](#example-queries)
  - [Maintainer](#maintainer)


## Features

* **Unified Codebase**: Single implementation supporting both HTTP and stdio transports
* **Flexible Deployment**: Switch between modes using environment variable
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
* Domain-optimized prompts for N8n and LLM agents (see [`PROMPTS.md`](system.md))
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

## Deployment Options

The MCP server supports two transport modes, both powered by a single unified codebase (`mcp_reports_server_unified.py`):

1. **HTTP Mode**: Runs as an HTTP server for remote access, suitable for production deployment behind reverse proxy
2. **Local/stdio Mode**: Runs locally using stdio transport for direct integration with Claude Code, MCP Inspector, and other local MCP clients

The mode is controlled via the `MCP_TRANSPORT` environment variable:
- `MCP_TRANSPORT=http` - HTTP server mode (default in Docker)
- `MCP_TRANSPORT=stdio` - Local stdio mode (default when running directly)

## Quick Start (HTTP Mode)

### 1. Clone and build

```bash
git clone https://github.com/fabric-testbed/reports.git
cd reports/mcp_server
docker build -t reports-mcp-server .
```

### 2. Run directly with Docker

```bash
docker run -d \
  -e MCP_TRANSPORT=http \
  -e REPORTS_API_BASE_URL=https://reports.fabric-testbed.net/reports \
  -p 5000:5000 \
  reports-mcp-server
```

Or use the launcher script:

```bash
./run_http.sh
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

## Local Mode (stdio)

The local mode version runs using stdio transport, making it ideal for direct integration with MCP clients like Claude Code, MCP Inspector, and other tools that communicate via stdin/stdout.

### Quick Start - Local

1. **Set your FABRIC credentials (choose one option):**

   **Option 1: Using FABRIC_RC (Recommended)**
   ```bash
   export FABRIC_RC="/Users/username/fabric_config"
   ```
   This points to your FABRIC configuration directory. The directory should contain:
   - `fabric_rc` file with FABRIC environment variables (including `FABRIC_TOKEN_LOCATION`)
   - Or `token.json` / `id_token.json` directly in the directory

   The `fabric_rc` file typically contains variables like:
   ```bash
   export FABRIC_TOKEN_LOCATION=/path/to/id_token.json
   export FABRIC_ORCHESTRATOR_HOST=orchestrator.fabric-testbed.net
   export FABRIC_PROJECT_ID=your-project-id
   # ... other FABRIC configuration
   ```

   **Option 2: Using FABRIC_TOKEN directly**
   ```bash
   export FABRIC_TOKEN="your-fabric-token-here"
   ```

2. **Run the launcher script:**
   ```bash
   cd reports/mcp_server
   ./run_local.sh
   ```

   Or pass the token directly:
   ```bash
   ./run_local.sh your-fabric-token-here
   ```

The launcher script will:
- Create a virtual environment if it doesn't exist
- Install dependencies
- Load credentials from FABRIC_RC or FABRIC_TOKEN
- Start the MCP server in stdio mode

### Using with Claude Desktop or MCP Clients

**Claude Desktop Integration**

Quick setup:
1. Build the Docker image: `docker build -t reports-mcp-server:latest .`
2. Add the MCP server to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS)
3. See [claude-desktop/claude_desktop_config.json](claude/stdio/claude_desktop_config_stdio.json) for example configuration

**Claude Code Integration**

For Claude Code, copy the configuration to your MCP settings:

```bash
# For Claude Code
cp vscode/mcp_local.json ~/.config/claude/mcp_settings.json
```

Then update the path in `mcp_local.json` to point to your local installation.

**Option 2: Manual configuration**

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "fabric-reports-local": {
      "command": "python3",
      "args": [
        "/path/to/claude-reports/reports/mcp_server/mcp_reports_server.py"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "FABRIC_RC": "/Users/username/fabric_config",
        "REPORTS_API_BASE_URL": "https://reports.fabric-testbed.net/reports"
      }
    }
  }
}
```

Note: You can use either `FABRIC_RC` (recommended) or `FABRIC_TOKEN` in the env section.

**Testing with MCP Inspector:**

```bash
# Option 1: Using FABRIC_RC
export FABRIC_RC="/Users/username/fabric_config"
export MCP_TRANSPORT="stdio"
npx @modelcontextprotocol/inspector python3 mcp_reports_server.py

# Option 2: Using FABRIC_TOKEN directly
export FABRIC_TOKEN="your-token"
export MCP_TRANSPORT="stdio"
npx @modelcontextprotocol/inspector python3 mcp_reports_server.py
```

This will open a web interface where you can test all available tools interactively.

**Running with Docker Compose (Local Mode):**

For a containerized local setup:

```bash
# Update docker-compose.yml with your FABRIC_RC path
# Then start the container
docker-compose -f docker-compose.yml up --build -d

# View logs
docker-compose -f docker-compose.yml logs -f

# Stop the container
docker-compose -f docker-compose.yml down
```

**Running directly with Python:**

```bash
# For stdio mode (local) - Option 1: Using FABRIC_RC
export MCP_TRANSPORT="stdio"
export FABRIC_RC="/Users/username/fabric_config"
python3 mcp_reports_server.py

# For stdio mode (local) - Option 2: Using FABRIC_TOKEN
export MCP_TRANSPORT="stdio"
export FABRIC_TOKEN="your-token"
python3 mcp_reports_server.py

# For HTTP mode (server)
export MCP_TRANSPORT="http"
export PORT="5000"
python3 mcp_reports_server.py
```

## Configuration

### Environment Variables

| Variable               | Description                                                 | Default                                      | Mode  |
| ---------------------- | ----------------------------------------------------------- | -------------------------------------------- | ----- |
| `MCP_TRANSPORT`        | Transport mode: `stdio` (local) or `http` (server)          | `stdio`                                      | Both  |
| `REPORTS_API_BASE_URL` | Base URL for the Reports API (used internally by the proxy) | `https://reports.fabric-testbed.net/reports` | Both  |
| `FABRIC_RC`            | Path to FABRIC config directory containing `fabric_rc` file and tokens (recommended) | None                                    | stdio |
| `FABRIC_TOKEN_LOCATION`| Path to token JSON file (typically set via `fabric_rc`)  | None                                         | stdio |
| `FABRIC_TOKEN`         | Your FABRIC authentication token (alternative to FABRIC_RC)  | None                                         | stdio |
| `PORT`                 | Local port to run the server                                | `5000`                                       | http  |
| `HOST`                 | Host binding for uvicorn                                    | `0.0.0.0`                                    | http  |

**Note**: For stdio mode, you must set either `FABRIC_RC` (recommended) or `FABRIC_TOKEN`.

**FABRIC_RC Setup:**
- `FABRIC_RC` should point to a directory containing a `fabric_rc` file
- The `fabric_rc` file contains FABRIC environment variables (as `export` statements)
- The `FABRIC_TOKEN_LOCATION` variable in `fabric_rc` points to your token JSON file
- Alternatively, place `token.json` or `id_token.json` directly in the FABRIC_RC directory

**Token Loading Priority:**
1. `FABRIC_TOKEN_LOCATION` from `fabric_rc` file (if FABRIC_RC is set)
2. `token.json` or `id_token.json` in FABRIC_RC directory
3. `FABRIC_TOKEN` environment variable

**Benefits of Using FABRIC_RC:**
When you set `FABRIC_RC` and provide a `fabric_rc` file, the MCP server loads all FABRIC environment variables, making them available for current and future features. This includes:
- `FABRIC_ORCHESTRATOR_HOST` - For orchestrator API integration
- `FABRIC_CREDMGR_HOST` - For credential management
- `FABRIC_PROJECT_ID` - Default project context
- `FABRIC_BASTION_HOST`, `FABRIC_BASTION_USERNAME` - For SSH/bastion access features
- And other FABRIC-specific configuration

This provides a consistent configuration experience across all FABRIC tools.


## Structure

| File                       | Purpose                                                      |
|----------------------------| ------------------------------------------------------------ |
| `mcp_reports_server.py`    | Unified FastAPI + fastmcp implementation supporting both modes|
| `run_local.sh`             | Launcher script for stdio mode with virtual environment setup|
| `run_http.sh`              | Launcher script for HTTP server mode with virtual environment setup|
| `system.md`                | System prompts and operational rules for LLM clients         |
| `requirements.txt`         | Python dependencies                                          |
| `Dockerfile`               | Container build instructions (defaults to HTTP mode)         |
| `vscode/mcp.json`          | Configuration for HTTP mode (remote server)                  |
| `vscode/mcp_local.json`    | Configuration for local stdio mode                           |
| `docker-compose-local.yml` | Docker Compose configuration for local stdio mode           |
| `claude-desktop/`          | Claude Desktop configuration files and setup guide           |


## Local Development

### Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the server

**For stdio mode (local):**
```bash
# Option 1: Using FABRIC_RC (recommended)
export MCP_TRANSPORT="stdio"
export FABRIC_RC="/Users/username/fabric_config"
python mcp_reports_server.py

# Option 2: Using FABRIC_TOKEN directly
export MCP_TRANSPORT="stdio"
export FABRIC_TOKEN="your-token"
python mcp_reports_server.py
```

**For HTTP mode (development server):**
```bash
export MCP_TRANSPORT="http"
export PORT="5000"
python mcp_reports_server.py
```

Access HTTP mode at:
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

See [`PROMPTS.md`](system.md) for:

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


## Usage

### Using the MCP Server in VS Code

You can interact with this MCP server directly from **VS Code Chat** using the built-in MCP client.
To get started, follow the detailed setup guide in [`vscode/README.md`](vscode/README.md).

Once configured, start the MCP server from VS Code, select your custom chat mode, and begin querying FABRIC data directly through the Chat interface.

### N8n Integration

In an N8n LLM node:

* **System Prompt:** contents from `PROMPTS.md`
* **Tool Name:** `reports-mcp-server`
* **Base URL:** `https://your-host/mcp/`
* **Authentication:** handled by n8n credentials or proxy

The node can then use `query_projects`, `query_slices`, etc., automatically using MCP conventions.


### Example Queries

* Ask an LLM: *“List all active slices at site RENC”*
  → Internally calls: `query-slices(site="RENC", state=["StableOK","StableError"])`

* Ask an LLM: *“Show projects excluding FABRIC personnel”*
  → Internally calls: `query-projects(exclude_fabric_projects=True)`

## Maintainer

Komal Thareja

