# Set up and use an HTTP-streamable MCP server in VS Code (with a custom Chat mode)

## Prerequisites

* VS Code (latest)
* The MCP-capable chat extension enabled (e.g., GitHub Copilot Chat with MCP support)
* Your MCP server reachable over HTTPS
* Your per-user token (FABRIC token) handy

---

## 1) Create `.vscode/mcp.json` and add your server

In your workspace, create the file `.vscode/mcp.json` (or replace it with the provided `mcp.json`).
Make sure to update the placeholder string `<REPLACE_WITH_ID_TOKEN_FROM_FABRIC_TOKEN>` with the actual `id_token` value from your FABRIC token.
You can generate a new FABRIC token by visiting [https://cm.fabric-testbed.net/](https://cm.fabric-testbed.net/).

---

## 2) Start the MCP server from VS Code

* Open `.vscode/mcp.json` in the editor.
* Click the **Start** (▶︎) button that appears for the `fabric-reports` server.
* Confirm it shows as **running** (you’ll typically see status in the MCP panel or the editor UI).

---

## 3) Create a custom Chat mode and add your System prompt

* Open the Chat view in VS Code.
* Go to **Configure Modes** → **Create new custom mode chat file**.
* In the new mode file (it’s JSON), give it a name and paste the contents of `fabric-reports.chatmode.md`

Save the file.

---

## 4) Use your custom mode with the running MCP server

* In the Chat window, select the new mode (e.g., **fabric-reports**) from the mode dropdown.
* Ensure your `fabric-reports` MCP server shows up as connected (you’ll see available tools in the Chat sidebar/panel when the server is active).
* Start asking questions—your requests will flow through the custom mode + MCP tools.

---

## Example “first query” ideas

* “List all active slivers connected to AWS, GCP, CloudLab”
* “Show slice utilization by site, excluding FABRIC-owned projects.”
* “Summarize sliver states with counts per state.”

---