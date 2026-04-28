# FABRIC Reports

FABRIC testbed analytics platform: a REST API, MCP server for LLM-queryable tools, and nginx reverse proxy. Tracks users, projects, slices, slivers, and sites with secure token-based authentication.

## Features

- **Reports API** — OpenAPI 3.0 Flask backend with comprehensive query endpoints for users, projects, slices, slivers, sites, and hosts
- **MCP Server** — [Model Context Protocol](https://modelcontextprotocol.io/) bridge exposing the API as 8 LLM-queryable tools (see [mcp_server/README.md](mcp_server/README.md))
- **PostgreSQL** — relational store for all FABRIC analytics data
- **Nginx** — TLS reverse proxy with streaming support for MCP transport
- Time-based, user-based, and project-based filtering
- Component type filtering (SharedNIC, SmartNIC, FPGA, GPU, NVMe, Storage)
- Bearer token authentication via FABRIC credential manager
- Dockerized microservices architecture

## Architecture

```
                    ┌─────────────────────┐
                    │   MCP Clients        │
                    │ (Claude, VS Code,    │
                    │  mcp-remote, etc.)   │
                    └────────┬────────────┘
                             │ HTTPS :443
                             v
                    ┌─────────────────────┐
                    │   nginx (TLS)       │
                    │   /reports  /mcp    │
                    └───┬────────────┬────┘
              frontend  │            │  frontend
              ──────────┼────────────┼──────────
              backend   │            │  backend
                        v            v
              ┌──────────────┐ ┌──────────────┐
              │ reports-api  │ │  mcp-server  │
              │ (Flask:8080) │ │ (FastMCP:5000│
              └──────┬───────┘ └──────┬───────┘
                     │                │
                     v                │
              ┌──────────────┐        │
              │  PostgreSQL  │ <──────┘
              │  (reports-db)│   (via reports-api)
              └──────────────┘
```

### Services

| Service | Description |
|---------|-------------|
| **reports-db** | PostgreSQL 17 database storing analytics data |
| **reports-api** | Flask backend serving the Reports REST API on port 8080 |
| **reports-mcp-server** | MCP server exposing the API as LLM-queryable tools on port 5000 |
| **reports-nginx** | Nginx reverse proxy handling TLS on port 443 |

### Networks

- **frontend** — external-facing (nginx)
- **backend** — internal only (database, API, MCP server)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- SSL certificates in `./ssl/` (`fullchain.pem`, `privkey.pem`)

### 1. Clone

```bash
git clone https://github.com/fabric-testbed/reports.git
cd reports
```

### 2. Configure

Create a `.env` file (or use the defaults):

```bash
POSTGRES_HOST=database
POSTGRES_DB=analytics
POSTGRES_USER=fabric
POSTGRES_PASSWORD=fabric
PGDATA=/var/lib/postgresql/data
```

Configure the API in `reports_api/config.yml`:
- `runtime.excluded.projects` — project UUIDs to exclude from queries
- `runtime.bearer_tokens` — API authentication tokens
- `oauth.jwks-url` — CILogon JWKS endpoint for token validation

### 3. Build & Run

```bash
docker compose up --build -d
```

This starts all four services. The API is accessible at `https://<host>/reports` and the MCP server at `https://<host>/mcp`.

### 4. Verify

```bash
# API health
curl -s https://localhost/reports/version -k | jq .

# MCP server (via streamable HTTP)
curl -s https://localhost/mcp -k
```

## API

The Reports API is generated from an OpenAPI 3.0 spec (`reports_api/openapi.yml`).

**Swagger UI:** `https://<host>/reports/ui/`

Key endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /reports/version` | API version and status |
| `GET /reports/users` | Query users with filters |
| `GET /reports/projects` | Query projects |
| `GET /reports/slices` | Query slices by state, site, project |
| `GET /reports/slivers` | Query resource allocations |
| `GET /reports/sites` | Query FABRIC sites |
| `GET /reports/hosts` | Query hosts at sites |
| `POST /reports/calendar/find-slot` | Find available resource slots |

## MCP Server

The MCP server exposes 8 read-only tools for LLM agents. See [mcp_server/README.md](mcp_server/README.md) for full documentation including:

- HTTP and stdio transport modes
- Claude Desktop / VS Code integration
- YAML configuration
- Local development setup

## Repository Structure

```
reports/
├── docker-compose.yml          # Production stack (all services)
├── nginx/
│   └── default.conf            # TLS + /reports and /mcp proxy
├── ssl/                        # TLS certificates
├── reports_api/                # Flask REST API
│   ├── openapi.yml             # OpenAPI 3.0 spec
│   ├── config.yml              # Runtime configuration
│   ├── Dockerfile
│   ├── swagger_server/         # Generated + custom controllers
│   ├── response_code/          # Business logic controllers
│   └── database/               # SQLAlchemy models & DB manager
├── mcp_server/                 # MCP server (see mcp_server/README.md)
│   ├── mcp_reports_server.py   # Single server entry point
│   ├── config/                 # Pydantic settings + YAML configs
│   ├── Dockerfile              # Production multi-stage build
│   └── Dockerfile.local        # Local development build
├── reports_client/             # Python client library (fabric_reports_client)
├── tools/                      # Jupyter notebooks with API examples
├── import.py                   # Slice data importer
└── upgrade.sh                  # Database schema upgrade script
```

## Development

### Reports API

```bash
cd reports_api
pip install -r requirements.txt
python -m swagger_server
# Swagger UI at http://localhost:8080/reports/ui/
```

### MCP Server

```bash
cd mcp_server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
MCP_TRANSPORT=stdio FABRIC_RC=/path/to/fabric_config python mcp_reports_server.py
```

### Database

Apply schema upgrades:

```bash
./upgrade.sh
# or manually:
psql -h reports-db -U fabric -d analytics -f psql.upgrade
```

## Troubleshooting

View logs for a specific service:

```bash
docker logs -f reports-api
docker logs -f reports-mcp-server
docker logs -f reports-nginx
```

Rebuild everything:

```bash
docker compose down -v
docker compose up --build -d
```

Log files are mounted at `./reports-logs`, `./mcp-logs`, and `./nginx-logs`.

## Contributing

Contributions are welcome. Fork the repository and submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
