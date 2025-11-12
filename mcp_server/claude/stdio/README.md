# Claude Desktop Configuration for FABRIC Reports MCP Server

This directory contains configuration files for integrating the FABRIC Reports MCP server with Claude Desktop.

## Prerequisites

1. **Claude Desktop** installed on your machine
2. **Docker** installed and running
3. **FABRIC Reports MCP server** Docker image built

## Setup Instructions

### 1. Build the Docker Image

```bash
cd /Users/kthare10/claude-reports/reports/mcp_server
docker build -t reports-mcp-server:latest .
```

### 2. Locate Claude Desktop Configuration

The Claude Desktop MCP configuration file location varies by OS:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 3. Configure Claude Desktop

#### Option A: Using Docker (Recommended for Containerized Setup)

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fabric-reports": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env", "MCP_TRANSPORT=stdio",
        "--env", "REPORTS_API_BASE_URL=https://reports.fabric-testbed.net/reports",
        "--env", "FABRIC_RC=/fabric_config",
        "--volume", "/Users/kthare10/work/fabric_config_mcp:/fabric_config:ro",
        "kthare10/reports-mcp-server:latest",
        "python", "/app/mcp_reports_server.py"
      ]
    }
  }
}
```

**Important**: Update the volume mount path to match your FABRIC config location:
- Change `/Users/kthare10/work/fabric_config_mcp` to your actual FABRIC config directory

#### Option B: Direct Python Execution (No Docker)

If you prefer to run without Docker:

```json
{
  "mcpServers": {
    "fabric-reports": {
      "command": "python3",
      "args": [
        "/Users/kthare10/claude-reports/reports/mcp_server/mcp_reports_server.py"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "FABRIC_RC": "/Users/kthare10/work/fabric_config_mcp",
        "REPORTS_API_BASE_URL": "https://reports.fabric-testbed.net/reports"
      }
    }
  }
}
```

**Important**: Update these paths:
- Python script path: `/Users/kthare10/claude-reports/reports/mcp_server/mcp_reports_server_unified.py`
- FABRIC config path: `/Users/kthare10/work/fabric_config_mcp`

### 4. Restart Claude Desktop

After modifying the configuration:
1. Quit Claude Desktop completely
2. Restart Claude Desktop
3. The MCP server will be available in new conversations

## Verification

To verify the MCP server is working:

1. Start a new conversation in Claude Desktop
2. Look for the MCP tools icon (usually in the bottom toolbar)
3. You should see available tools like:
   - `query-version`
   - `query-sites`
   - `query-slices`
   - `query-slivers`
   - `query-users`
   - `query-projects`
   - `query-user-memberships`
   - `query-project-memberships`

## Troubleshooting

### MCP Server Not Appearing

1. **Check Docker image exists**:
   ```bash
   docker images | grep reports-mcp-server
   ```

2. **Test Docker command manually**:
   ```bash
   docker run --rm -i \
     --env MCP_TRANSPORT=stdio \
     --env FABRIC_RC=/fabric_config \
     --volume /Users/kthare10/work/fabric_config_mcp:/fabric_config:ro \
     reports-mcp-server:latest \
     python /app/mcp_reports_server.py
   ```

   You should see startup messages about loading FABRIC configuration.

3. **Check Claude Desktop logs**:
   - macOS: `~/Library/Logs/Claude/`
   - Look for MCP-related error messages

### Authentication Errors

1. **Verify FABRIC config directory** contains:
   - `fabric_rc` file with environment variables
   - Token file referenced by `FABRIC_TOKEN_LOCATION` in `fabric_rc`

2. **Check token file format**:
   ```bash
   cat /Users/kthare10/work/fabric_config_mcp/fabric_rc
   # Should show: export FABRIC_TOKEN_LOCATION=/path/to/token.json

   cat $(grep FABRIC_TOKEN_LOCATION /Users/kthare10/work/fabric_config_mcp/fabric_rc | cut -d= -f2)
   # Should show JSON with "id_token" field
   ```

3. **Test token loading**:
   ```bash
   export FABRIC_RC=/Users/kthare10/work/fabric_config_mcp
   export MCP_TRANSPORT=stdio
   python3 mcp_reports_server.py
   ```

   Look for: "Loaded FABRIC configuration from: ..." and "Loaded token from ..."

### Docker Permission Issues

If Docker commands fail:
1. Ensure Docker Desktop is running
2. Check volume mount permissions - the fabric_config_mcp directory must be readable
3. Try running with absolute paths in the volume mount

## Using the MCP Server

Once configured, you can ask Claude Desktop questions like:

- "What FABRIC sites are available?"
- "Show me active slices at the RENC site"
- "List all projects using GPUs"
- "Find users with failed slices in the last week"
- "What are the current project memberships?"

Claude will use the MCP tools to query the FABRIC Reports API and provide detailed answers.

## Configuration Files

- `claude_desktop_config.json` - Sample configuration for Docker-based setup
- This can be copied/modified and placed in your Claude Desktop config directory

## Support

For issues specific to:
- **MCP Server**: Check the main [MCP Server README](../../README.md)
- **FABRIC Reports API**: See [FABRIC Reports documentation](https://reports.fabric-testbed.net/reports/ui/)
- **Claude Desktop**: Visit [Claude Desktop documentation](https://docs.anthropic.com/claude/docs)
