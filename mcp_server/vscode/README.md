# Set up and use an HTTP-streamable MCP server in VS Code (with a custom Chat mode)

## Table of Contents
- [Set up and use an HTTP-streamable MCP server in VS Code (with a custom Chat mode)](#set-up-and-use-an-http-streamable-mcp-server-in-vs-code-with-a-custom-chat-mode)
  - [Prerequisites](#prerequisites)
  - [Setup Options](#setup-options)
    - [Option A: Remote HTTP Server (Production)](#option-a-remote-http-server-production)
    - [Option B: Local Docker Server (Development)](#option-b-local-docker-server-development)
  - [1) Create `.vscode/mcp.json` and add your server](#1-create-vscodemcpjson-and-add-your-server)
  - [2) Start the MCP server from VS Code](#2-start-the-mcp-server-from-vs-code)
  - [3) Create a custom Chat mode and add your System prompt](#3-create-a-custom-chat-mode-and-add-your-system-prompt)
  - [4) Use your custom mode with the running MCP server](#4-use-your-custom-mode-with-the-running-mcp-server)
  - [Example "first query" ideas](#example-first-query-ideas)

## Prerequisites

* VS Code (latest)
* The MCP-capable chat extension enabled (e.g., GitHub Copilot Chat with MCP support)

**For Remote Setup:**
* Your MCP server reachable over HTTPS
* Your per-user token (FABRIC token) handy. You can generate a new FABRIC token by visiting [https://cm.fabric-testbed.net/](https://cm.fabric-testbed.net/).

**For Local Setup:**
* Docker installed and running
* FABRIC configuration directory with credentials (typically `~/.fabric` or custom path)
* The Reports API backend accessible (either running locally or via network)

---

## Setup Options

You can connect to the FABRIC Reports MCP server in two ways:

### Option A: Remote HTTP Server (Production)

Use the **`mcp.json`** configuration to connect to the production FABRIC Reports server at `https://reports.fabric-testbed.net/mcp`. This is the recommended approach for regular usage.

**Pros:**
* No local setup required
* Always uses the latest production version
* No need to run Docker locally

**Cons:**
* Requires network connectivity
* Needs a valid FABRIC token

### Option B: Local Docker Server (Development)

Use the **`mcp_local.json`** configuration to run the MCP server locally via Docker with stdio transport. This is ideal for development and testing.

**Pros:**
* Works offline (after initial Docker image pull)
* Test local changes before deploying
* No authentication token required if using local config
* Full control over the server version

**Cons:**
* Requires Docker and local setup
* Need to maintain local FABRIC configuration
* Must ensure backend API is accessible

**To use `mcp_local.json`:**

1. **Update the configuration path**: Edit `mcp_local.json` and change the volume mount path to point to your FABRIC configuration directory:
   ```json
   "-v",
   "/path/to/your/fabric_config:/fabric_config:ro",
   ```
   Replace `/path/to/your/fabric_config` with your actual FABRIC configuration directory path.

2. **Verify Docker image**: Ensure you have the `kthare10/fabric-reports:latest` image, or update the image name to match your local build:
   ```bash
   docker pull kthare10/fabric-reports:latest
   ```
   Or build locally:
   ```bash
   cd reports
   docker-compose build reports-mcp-server
   docker tag reports-mcp-server:latest kthare10/fabric-reports:latest
   ```

3. **Configure the backend URL** (optional): The default `REPORTS_API_BASE_URL` is set to `http://reports-api:8080/reports`. If you're running the full stack locally with docker-compose, you may need to adjust the Docker network:
   ```json
   "--network", "reports_backend",
   ```
   Add this to the `args` array in `mcp_local.json` if connecting to a local docker-compose stack.

4. **Copy to `.vscode/mcp.json`**: Once configured, copy `mcp_local.json` to `.vscode/mcp.json` in your workspace:
   ```bash
   cp mcp_server/vscode/mcp_local.json .vscode/mcp.json
   ```

---

## 1) Create `.vscode/mcp.json` and add your server

In your workspace, create the file `.vscode/mcp.json`:

* **For remote setup**: Copy the provided `mcp.json` file, which connects to the production server. The token is prompted once per VS Code session.
* **For local setup**: Copy the provided `mcp_local.json` file (after customizing paths as described above). 
![Start MCP](./images/1_start_mcp.png)
---

## 2) Start the MCP server from VS Code

* Open `.vscode/mcp.json` in the editor.
* Click the **Start** (▶︎) button that appears for your server:
  * `fabric-reports` (for remote HTTP setup)
  * `fabric-reports-local` (for local Docker setup)
* Confirm it shows as **running** (you'll typically see status in the MCP panel or the editor UI).

**Note for local setup**: The first time you start the local server, Docker will pull the image if not already available. This may take a few moments.
![System Prompt-1](./images/2_create_custom_mode.png)
![System Prompt-2](./images/2_create_prompt_file.png)
---

## 3) Create a custom Chat mode and add your System prompt

* Open the Chat view in VS Code.
* Go to **Configure Modes** → **Create new custom mode chat file**.
* In the new mode file (it’s JSON), give it a name and paste the contents of `fabric-reports.chatmode.md`

Save the file.
![Ask Questions](./images/3_ask_questions.png)

---

## 4) Use your custom mode with the running MCP server

* In the Chat window, select the new mode (e.g., **fabric-reports**) from the mode dropdown.
* Ensure your MCP server shows up as connected:
  * `fabric-reports` (remote) or `fabric-reports-local` (local)
  * You'll see available tools in the Chat sidebar/panel when the server is active
* Start asking questions—your requests will flow through the custom mode + MCP tools.

**Troubleshooting local setup:**
* If the server fails to start, check Docker logs: `docker logs <container-id>`
* Verify the FABRIC configuration path is correct and readable
* Ensure the backend API URL is accessible from within the Docker container
* Check that the Docker image exists: `docker images | grep fabric-reports`

---

## Example “first query” ideas

* “List all active slivers connected to AWS, GCP, CloudLab”
* “Show slice utilization by site, excluding FABRIC-owned projects.”
* “Summarize sliver states with counts per state.”

---