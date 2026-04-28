# FABRIC Reports MCP Server

The **Reports MCP Server** is a lightweight Model Context Protocol (MCP) bridge that exposes the [FABRIC Reports API](https://reports.fabric-testbed.net/reports) as a toolset that can be queried directly by LLMs or any MCP-compatible client.

It provides a structured, secure interface for querying **users**, **projects**, **slices**, **slivers**, and **sites** — while enforcing domain constraints, normalization rules, and optional project exclusion filters.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Deployment Options](#deployment-options)
- [Quick Start (HTTP Mode)](#quick-start-http-mode)
- [Local Mode (stdio)](#local-mode-stdio)
- [Configuration](#configuration)
- [File Structure](#file-structure)
- [Local Development](#local-development)
- [Integration with Reverse Proxy](#integration-with-reverse-proxy)
- [Security](#security)
- [Example Queries](#example-queries)
- [Maintainer](#maintainer)

## Features

* **Unified Codebase**: Single `mcp_reports_server.py` supporting both HTTP and stdio transports
* **Structured Config**: YAML configs with environment variable overrides via pydantic-settings
* **Structured Logging**: JSON or text logging with correlation IDs and file rotation
* **Circuit Breaker**: Automatic backend failure detection with half-open recovery
* **Token Caching**: Thread-safe TTL-cached token provider for stdio mode (30-min TTL)
* **Explicit Tool Signatures**: All 8 tools have fully typed parameter signatures (no `**kwargs`)
* Bridges to the official **FABRIC Reports API**
* Available tools:
  * `query-version` — API version and service status
  * `query-sites` — physical FABRIC testbed sites
  * `query-slices` — experimental slices (comprehensive filtering)
  * `query-slivers` — individual resource allocations
  * `query-users` — users with activity/relationship filtering
  * `query-projects` — projects with membership/resource filtering
  * `query-user-memberships` — user-to-project membership relationships
  * `query-project-memberships` — project-to-user membership relationships
* Supports additional metadata fields (`toolCallId`, `id`, etc.) gracefully
* Domain-optimized system prompt for LLM agents (see [`system.md`](system.md))
* Dockerized with multi-stage production build

## Architecture

```
[MCP Client (Claude Desktop, VS Code, mcp-remote, etc.)]
          |
          v
   nginx (TLS + /mcp proxy)
          |
          v
   Reports MCP Server  (FastMCP + pydantic-settings)
          |
          v
     Reports API
          |
          v
      PostgreSQL
```

## Deployment Options

The MCP server supports two transport modes:

1. **HTTP Mode** (production): Runs as an HTTP server behind nginx. Authentication via Bearer token per request.
2. **stdio Mode** (local): Runs locally using stdio transport for direct integration with Claude Desktop, VS Code, MCP Inspector, etc. Authentication via FABRIC_RC or FABRIC_TOKEN.

The mode is controlled via the `MCP_TRANSPORT` environment variable:
- `MCP_TRANSPORT=http` — HTTP server mode (default in Docker)
- `MCP_TRANSPORT=stdio` — Local stdio mode (default when running directly)

## Quick Start (HTTP Mode)

### Using Docker Compose (production)

```bash
git clone https://github.com/fabric-testbed/reports.git
cd reports/mcp_server
docker compose up --build -d
```

This uses `Dockerfile` (multi-stage production build) and runs in HTTP mode by default.

### Using Docker directly

```bash
cd reports/mcp_server
docker build -t fabric-reports-mcp .
docker run -d \
  -e MCP_TRANSPORT=http \
  -e REPORTS_API_BASE_URL=http://reports-api:8080/reports \
  -p 5000:5000 \
  fabric-reports-mcp
```

### Using the launcher script

```bash
./run_http.sh
```

## Local Mode (stdio)

### Quick Start - Local

1. **Set your FABRIC credentials (choose one option):**

   **Option A: Using FABRIC_RC (Recommended)**
   ```bash
   export FABRIC_RC="/Users/username/fabric_config"
   ```
   This points to your FABRIC configuration directory containing a `fabric_rc` file with `FABRIC_TOKEN_LOCATION` and other env vars.

   **Option B: Using FABRIC_TOKEN directly**
   ```bash
   export FABRIC_TOKEN="your-fabric-token-here"
   ```

2. **Run the launcher script:**
   ```bash
   cd reports/mcp_server
   ./run_local.sh
   ```

### Using with Claude Desktop

Add the MCP server to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "fabric-reports": {
      "command": "python3",
      "args": [
        "/path/to/reports/mcp_server/mcp_reports_server.py"
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

For remote HTTP mode via `mcp-remote`, use the `scripts/fabric-reports.sh` wrapper which reads a local token file and passes it as a Bearer header.

### Using with Docker Compose (local)

```bash
docker compose -f docker-compose.local.yml up --build -d
```

This uses `Dockerfile.local` (single-stage build) and runs in stdio mode.

### Testing with MCP Inspector

```bash
export FABRIC_RC="/Users/username/fabric_config"
export MCP_TRANSPORT="stdio"
npx @modelcontextprotocol/inspector python3 mcp_reports_server.py
```

## Configuration

### Environment Variables (legacy)

These are backward-compatible and mapped internally to the new nested format:

| Variable               | Description                              | Default                                      | Mode  |
| ---------------------- | ---------------------------------------- | -------------------------------------------- | ----- |
| `MCP_TRANSPORT`        | Transport mode: `stdio` or `http`        | `stdio`                                      | Both  |
| `REPORTS_API_BASE_URL` | Base URL for the Reports API             | `https://reports.fabric-testbed.net/reports`  | Both  |
| `PORT`                 | HTTP server port                         | `5000`                                       | http  |
| `HOST`                 | HTTP server host                         | `0.0.0.0`                                    | http  |
| `FABRIC_RC`            | Path to FABRIC config directory          | None                                         | stdio |
| `FABRIC_TOKEN`         | FABRIC authentication token              | None                                         | stdio |

### Environment Variables (new nested format)

| Variable                     | Description                    | Default    |
| ---------------------------- | ------------------------------ | ---------- |
| `MCP_TRANSPORT__MODE`        | Transport mode                 | `stdio`    |
| `MCP_TRANSPORT__HTTP_HOST`   | HTTP server host               | `0.0.0.0`  |
| `MCP_TRANSPORT__HTTP_PORT`   | HTTP server port               | `5000`     |
| `MCP_API__BASE_URL`          | Reports API base URL           | (see above)|
| `MCP_API__TIMEOUT`           | API request timeout (seconds)  | `30`       |
| `MCP_LOGGING__LEVEL`         | Log level                      | `INFO`     |
| `MCP_LOGGING__FORMAT`        | Log format: `json` or `text`   | `json`     |
| `MCP_LOGGING__DESTINATION`   | `stdout`, `file`, or `both`    | `stdout`   |
| `MCP_LOGGING__FILE_PATH`     | Log file path (if destination includes file) | None |

### YAML Configuration

YAML config files in `config/` are loaded based on `MCP_ENV` (default: `prod`):

- `config/config.dev.yml` — stdio mode, DEBUG logging, text format
- `config/config.staging.yml` — HTTP mode, INFO logging, JSON format
- `config/config.prod.yml` — HTTP mode, INFO logging, JSON format with file output

Override with `MCP_CONFIG_FILE=/path/to/custom.yml` or `MCP_ENV=dev`.

**Priority order**: Environment variables > YAML config > code defaults.

### Token Loading Priority (stdio mode)

1. `FABRIC_TOKEN_LOCATION` from `fabric_rc` file (if `FABRIC_RC` is set)
2. `FABRIC_TOKEN` environment variable

## File Structure

```
mcp_server/
  mcp_reports_server.py      # Single server entry point
  system.md                  # LLM system prompt
  requirements.txt           # Python dependencies
  entrypoint.sh              # Docker entrypoint (fixes log dir permissions)
  Dockerfile                 # Production multi-stage build (default)
  Dockerfile.local           # Local single-stage build
  docker-compose.yml         # Production HTTP mode
  docker-compose.local.yml   # Local stdio mode
  run_local.sh               # Launcher script for stdio mode
  run_http.sh                # Launcher script for HTTP mode
  config/
    __init__.py
    settings.py              # Pydantic settings with env var mapping
    logging_config.py         # Structured logging with correlation IDs
    config.dev.yml
    config.staging.yml
    config.prod.yml
  scripts/
    fabric-reports.sh         # mcp-remote wrapper with Bearer auth
```

## Local Development

### Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the server

**stdio mode:**
```bash
export MCP_TRANSPORT="stdio"
export FABRIC_RC="/Users/username/fabric_config"
python mcp_reports_server.py
```

**HTTP mode:**
```bash
export MCP_TRANSPORT="http"
python mcp_reports_server.py
```

## Integration with Reverse Proxy

Example nginx configuration for production deployment:

```nginx
location /mcp {
    proxy_pass http://reports-mcp-server:5000;
    proxy_http_version 1.1;
    proxy_set_header Host              $host;
    proxy_set_header Authorization     $http_authorization;
    proxy_set_header X-Real-IP         $remote_addr;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Connection "";
    proxy_set_header Content-Length $content_length;
    proxy_set_header Content-Type   $http_content_type;
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding on;
}
```

Key settings for MCP's streamable HTTP transport:
- `proxy_buffering off` — required for SSE/streaming responses
- `proxy_set_header Authorization` — forward Bearer tokens to MCP server
- `chunked_transfer_encoding on` — support streamed tool responses

## Security

* **HTTP mode**: Authentication is via Bearer tokens in the `Authorization` header, validated by the Reports API backend.
* **stdio mode**: Authentication uses locally-stored FABRIC tokens (via `FABRIC_RC` or `FABRIC_TOKEN`).
* Always deploy behind TLS (nginx with HTTPS) in production.
* The MCP server does not store or manage credentials — it passes them through to the Reports API.

## Example Queries

* *"List all active slices at site RENC"*
  -> `query-slices(site=["RENC"], slice_state=["StableOK", "StableError"])`

* *"Show projects excluding FABRIC personnel"*
  -> `query-projects(exclude_project_id=[...FABRIC personnel UUIDs...])`

* *"Which users have GPU allocations?"*
  -> `query-users(component_type=["GPU"], user_active=True)`

* *"Show memberships for a specific project"*
  -> `query-project-memberships(project_id=["uuid"])`

## Maintainer

Komal Thareja (<kthare10@renci.org>)
