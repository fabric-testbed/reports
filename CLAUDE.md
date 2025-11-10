# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

The **FABRIC Reports Dashboard** is a microservices-based web application for tracking and analyzing sliver allocations across FABRIC testbed projects, users, and sites. The system provides time-based, user-based, and project-based filtering with secure authentication.

## Architecture

The system is composed of multiple Docker services that communicate across two network segments:

### Core Services

- **reports-db**: PostgreSQL 12.3 database storing users, projects, slices, slivers, components, sites, and hosts
- **reports-api**: Swagger/OpenAPI-generated Flask backend serving analytics data at port 8080
- **reports-mcp-server**: Model Context Protocol (MCP) server exposing the Reports API as LLM-queryable tools (port 5000)
- **dash-app**: Python Dash visualization dashboard (deprecated/unused in current docker-compose)
- **reports-nginx**: Nginx reverse proxy handling HTTPS traffic on port 443
- **vouch-proxy**: OAuth/SSO authentication proxy securing API access

### Network Topology

- **frontend network**: External-facing (nginx, MCP server, vouch-proxy)
- **backend network**: Internal only (database, API communication)

### Data Model

The PostgreSQL schema uses SQLAlchemy ORM models defined in `reports_api/database/`:
- **Users**: FABRIC users with email, UUID, and membership relationships
- **Projects**: FABRIC projects with UUIDs, types (research/education/test), and facility flags
- **Slices**: Experimental slices with states (StableOK, StableError, Closing, Dead, etc.)
- **Slivers**: Individual resource allocations within slices, with types and states
- **Components**: Hardware components (SharedNIC, SmartNIC, FPGA, GPU, NVMe, Storage)
- **Sites**: Physical FABRIC sites with capacities
- **Hosts**: Physical hosts at sites
- **Interfaces**: Network interfaces with VLANs, IPs
- **Membership**: Project-user relationships with roles

## Development Commands

### Docker Operations

Start all services:
```bash
cd reports
docker-compose up --build -d
```

View logs for a specific service:
```bash
docker logs -f reports-api
docker logs -f reports-mcp-server
docker logs -f reports-nginx
```

Restart a service:
```bash
docker-compose restart reports-api
```

Rebuild and restart everything:
```bash
docker-compose down -v
docker-compose up --build -d
```

### API Development (reports_api/)

The API is generated from `openapi.yml` using swagger-codegen.

Run locally (without Docker):
```bash
cd reports/reports_api
pip3 install -r requirements.txt
python3 -m swagger_server
```

Access Swagger UI at: `http://localhost:8080/reports/ui/`

Run tests:
```bash
cd reports/reports_api
sudo pip install tox
tox
```

Regenerate API code from OpenAPI spec:
```bash
cd reports/reports_api
swagger-codegen generate -i openapi.yml -l python-flask -o generated-server
./update_swagger_stub.sh
# Compare swagger_server_archive and swagger_server to merge changes
```

### MCP Server Development (mcp_server/)

Run locally:
```bash
cd reports/mcp_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python mcp_reports_server.py
```

Test capabilities endpoint:
```bash
curl -s http://localhost:5000/mcp/capabilities | jq .
```

Test tool invocation:
```bash
curl -s -X POST http://localhost:5000/mcp/call_tool \
  -H "Content-Type: application/json" \
  -d '{"name": "query_projects", "arguments": {"limit": 3}}' | jq .
```

Available MCP tools:
- `query_users`: Query FABRIC users
- `query_projects`: Query projects with filters
- `query_slices`: Query slices by state, site, project
- `query_slivers`: Query resource allocations
- `query_components`: Query hardware components
- `query_sites`: Query FABRIC sites

### Client Library (reports_client/)

Python client for the Reports API:
```bash
cd reports/reports_client
pip install -e .
```

Package name: `fabric_reports_client`

### Data Import

Import slice data from JSON files:
```bash
cd reports
python3 import.py --slices-dir /path/to/slices/json/files
```

Import project memberships:
```bash
cd reports
python3 import_memberships_from_json.py
```

### Database Operations

Apply schema upgrades:
```bash
cd reports
psql -h reports-db -U fabric -d analytics -f psql.upgrade
```

Or use the upgrade script:
```bash
cd reports
./upgrade.sh
```

## Configuration

### Environment Variables

Set in `.env` file or docker-compose environment sections:

- `POSTGRES_HOST`: Database host (default: `database`)
- `POSTGRES_DB`: Database name (default: `analytics`)
- `POSTGRES_USER`: Database user (default: `fabric`)
- `POSTGRES_PASSWORD`: Database password (default: `fabric`)
- `REPORTS_API_BASE_URL`: MCP server backend URL (default: `http://reports-api:8080/reports`)
- `API_URL`: Dash app backend URL (if used)

### API Configuration (reports_api/config.yml)

Key settings:
- `runtime.excluded.projects`: Comma-separated project UUIDs to exclude from queries
- `runtime.bearer_tokens`: API authentication tokens
- `runtime.allowed_roles`: OAuth roles (facility-viewers, facility-operators)
- `oauth.jwks-url`: Certificate endpoint for token validation
- `database.*`: Database connection parameters

### SSL Certificates

Place SSL certificates in `reports/ssl/`:
- `fullchain.pem`: Public certificate
- `privkey.pem`: Private key

## Key Implementation Patterns

### Authentication Flow

1. Nginx receives HTTPS request
2. Vouch Proxy validates OAuth token
3. Request forwarded to reports-api or mcp-server
4. Backend validates token using `fabric_credmgr_client` and JWKS
5. Authorization checked via `response_code/authorization_controller.py`

### API Controllers

Business logic lives in `reports_api/response_code/*_controller.py`, not in the generated `openapi_server/controllers/` stubs. The generated controllers delegate to response_code controllers.

### Database Access

Use `DatabaseManager` (reports_api/database/db_manager.py) for all DB operations:
- Always use `get_session()` for thread-safe sessions
- Supports complex filters, pagination, and aggregations
- Built-in 30-day default time window

### MCP Server Integration

The MCP server (`mcp_server/mcp_reports_server.py`) uses FastAPI + fastmcp to expose Reports API as MCP tools. See `mcp_server/system.md` for LLM system prompts and query patterns.

## Testing

Tests are in `reports_api/openapi_server/test/test_*_controller.py` using pytest/tox framework.

Example notebooks demonstrating API usage are in `tools/*.ipynb`:
- `api_usage.ipynb`: General API usage examples
- `queries_slivers.ipynb`: Sliver query examples
- `reports.ipynb`: Analytics and reporting examples
- `quotas.ipynb`: Quota tracking examples

## Important Notes

- The database schema uses SQLAlchemy with models in `reports_api/database/__init__.py`
- Slice states: `Nascent`, `Configuring`, `StableOK`, `StableError`, `ModifyOK`, `ModifyError`, `Closing`, `Dead`
- Sliver states: `Nascent`, `Configuring`, `Active`, `ModifyOK`, `ModifyError`, `Failed`, `Closing`, `Closed`
- Component types: `SharedNIC`, `SmartNIC`, `FPGA`, `GPU`, `NVMe`, `Storage`
- Project types: `research`, `education`, `accept`, `test`
- The API supports extensive filtering via query parameters - refer to `openapi.yml` for complete parameter lists
- Logs are written to mounted volumes: `./reports-logs`, `./mcp-logs`, `./nginx-logs`
