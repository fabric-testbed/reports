# Containerizing the MCP Server

This bundle gives you a ready-to-run Docker setup for your MCP server.

## Contents
- `Dockerfile` — builds a Node 20 Alpine image and runs the TypeScript server via `ts-node`.
- `docker-compose.yml` — convenience for local runs with port mapping and envs.
- `.dockerignore` — keeps the image small and clean.

> Note: Your project currently uses `ts-node` at runtime (no TS build step). The Dockerfile installs **devDependencies** so the `--loader ts-node/esm` works in the container. If you prefer a production-only image, switch to compiling TypeScript to JS (see the Production Build section below).

## Quickstart

1) Put these files **next to** your project files (i.e., `package.json`, `package-lock.json`, `src/`, `tsconfig.json`). If you're using the zip I reviewed, just place this folder's files into the repo root.

2) Build and run with Docker Compose:
```bash
export MCP_SERVER_PORT=4000   # optional; defaults to 4000
docker compose up --build -d
```

3) Verify it’s healthy:
```bash
docker ps
# Look for 'healthy' status on mcp-server
```

4) Sanity test (JSON-RPC `mcp.list_capabilities`):
```bash
curl -sS -X POST "http://localhost:${MCP_SERVER_PORT:-4000}/mcp"   -H "Content-Type: application/json"   -H "Accept: application/json, text/event-stream"   -d '{"jsonrpc":"2.0","id":"1","method":"mcp.list_capabilities","params":{}}' | jq .
```

If your server uses extra environment variables (e.g., `MCP_API_URL`, tokens), add them in `docker-compose.yml` under `environment:`.

## Logs
```bash
docker logs -f mcp-server
```

## Production Build (Optional)
If you want a slimmer, production-only image:
1. Add build scripts to `package.json`:
```json
{
  "scripts": {
    "build": "tsc --outDir dist --module es2022 --moduleResolution node",
    "start": "node dist/index.js"
  }
}
```
2. Update `tsconfig.json` (`noEmit` must be false or removed) and ensure imports compile to JS in `dist/`.
3. Use a multi-stage Dockerfile like:
```Dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json .
RUN npm ci

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/dist ./dist
COPY package*.json ./
RUN npm ci --omit=dev
EXPOSE 4000
CMD ["node", "dist/index.js"]
```
4. Then build:
```bash
docker build -t mcp-server:prod .
docker run -p 4000:4000 mcp-server:prod
```

## Troubleshooting
- **Port in use**: change `MCP_SERVER_PORT` in env and compose mapping.
- **Node version**: this setup targets Node 20; your `engines` field allows >=18, which is compatible.
- **Healthcheck fails**: check application logs; ensure the `/mcp` route is listening on `MCP_SERVER_PORT`.
- **DevDeps missing**: if you see `ts-node` not found, make sure `npm ci` installed devDependencies (keep `NODE_ENV=development` during build).

## Security Notes
- The image runs as an unprivileged user.
- Avoid baking secrets into the image; pass tokens via environment variables or Docker secrets.
