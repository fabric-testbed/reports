# Claude Desktop Configuration for FABRIC Reports MCP Server (HTTP)

This directory contains configuration files for integrating the FABRIC Reports MCP server with Claude Desktop using HTTP transport via `mcp-remote`.

## Overview

This setup uses the `mcp-remote` npm package to connect Claude Desktop to a remote FABRIC Reports MCP server over HTTPS. This is ideal when:
- You want to connect to the production FABRIC Reports server
- You prefer HTTP transport over stdio
- You don't want to run Docker locally
- You need to connect to a server behind authentication

## Prerequisites

1. **Claude Desktop** installed on your machine
2. **Node.js and npm** installed (for `npx` command)
3. **jq** installed for JSON parsing
   ```bash
   # macOS
   brew install jq

   # Ubuntu/Debian
   sudo apt-get install jq

   # Other systems: https://stedolan.github.io/jq/download/
   ```
4. **FABRIC ID Token** in JSON format

## Setup Instructions

### 1. Prepare Your FABRIC Token

Create a JSON file containing your FABRIC ID token:

```bash
# Create token file (default location: ~/work/id_token.json)
mkdir -p ~/work
cat > ~/work/id_token.json <<EOF
{
  "id_token": "YOUR_FABRIC_ID_TOKEN_HERE"
}
EOF
```

**To get your FABRIC token:**
1. Visit [https://cm.fabric-testbed.net/](https://cm.fabric-testbed.net/)
2. Generate a new token
3. Download the token JSON file

### 2. Configure the Script

The `fabric-mcp.sh` script can be configured via environment variables:

```bash
# Token file location (default: ~/work/id_token.json)
export FABRIC_TOKEN_JSON="$HOME/work/id_token.json"

# Remote MCP server URL (default: https://reports.fabric-testbed.net/mcp)
export FABRIC_MCP_URL="https://reports.fabric-testbed.net/mcp"

# Optional: System prompt file (currently not used)
# export FABRIC_SYSTEM_MD="/path/to/system.md"
```

### 3. Locate Claude Desktop Configuration

The Claude Desktop MCP configuration file location varies by OS:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 4. Configure Claude Desktop

Add the following to your `claude_desktop_config.json`:

#### Option A: Using Default Settings

```json
{
  "mcpServers": {
    "fabric-reports-http": {
      "command": "/Users/kthare10/claude-reports/reports/mcp_server/claude/http/fabric-mcp.sh"
    }
  }
}
```

**Important**: Update the path to match your actual location of `fabric-mcp.sh`

#### Option B: With Custom Environment Variables

```json
{
  "mcpServers": {
    "fabric-reports-http": {
      "command": "/Users/kthare10/claude-reports/reports/mcp_server/claude/http/fabric-mcp.sh",
      "env": {
        "FABRIC_TOKEN_JSON": "/custom/path/to/id_token.json",
        "FABRIC_MCP_URL": "https://reports.fabric-testbed.net/mcp"
      }
    }
  }
}
```

#### Option C: Direct mcp-remote Configuration (Without Script)

If you prefer to configure `mcp-remote` directly without using the script:

```json
{
  "mcpServers": {
    "fabric-reports-http": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://reports.fabric-testbed.net/mcp",
        "--header",
        "Authorization: Bearer YOUR_FABRIC_TOKEN_HERE"
      ]
    }
  }
}
```

**Note**: You'll need to manually replace `YOUR_FABRIC_TOKEN_HERE` with your actual token, and update it when it expires.

### 5. Make the Script Executable

```bash
chmod +x /Users/kthare10/claude-reports/reports/mcp_server/claude/http/fabric-mcp.sh
```

### 6. Create FABRIC-Reports Project in Claude Desktop

To get the best experience with domain-specific prompts and context:

1. **Create a new project** in Claude Desktop:
   - Click on "Projects" in the sidebar
   - Click "Create Project"
   - Name it **"FABRIC-Reports"** (exact name recommended for consistency)

2. **Add the system prompt**:
   - In the project settings, go to "Custom Instructions"
   - Upload or copy the contents of `mcp_server/system.md` into the project instructions
   - This file contains specialized prompts for querying FABRIC Reports data

   ```bash
   # The system.md file is located at:
   /Users/kthare10/claude-reports/reports/mcp_server/system.md
   ```

3. **Why this matters**:
   - The system.md file provides Claude with context about FABRIC terminology, data structures, and query patterns
   - It helps Claude understand concepts like slivers, slices, components, and sites
   - It includes best practices for formulating queries and interpreting results

### 7. Restart Claude Desktop

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

### Script Fails to Start

1. **Check script permissions**:
   ```bash
   ls -l /path/to/fabric-mcp.sh
   # Should show: -rwxr-xr-x
   ```

2. **Test script manually**:
   ```bash
   /path/to/fabric-mcp.sh
   ```

   You should see mcp-remote startup messages.

3. **Verify jq is installed**:
   ```bash
   which jq
   jq --version
   ```

### Token Issues

1. **Verify token file exists and is readable**:
   ```bash
   cat ~/work/id_token.json
   # Should show: {"id_token": "..."}
   ```

2. **Check token format with jq**:
   ```bash
   jq -r '.id_token' ~/work/id_token.json
   # Should output your token string (not "null")
   ```

3. **Token expired**:
   - FABRIC tokens expire after a certain period
   - Generate a new token at [https://cm.fabric-testbed.net/](https://cm.fabric-testbed.net/)
   - Update your `id_token.json` file

### Connection Issues

1. **Test network connectivity**:
   ```bash
   curl -I https://reports.fabric-testbed.net/mcp
   ```

2. **Verify mcp-remote package**:
   ```bash
   npx -y mcp-remote --help
   ```

3. **Check Claude Desktop logs**:
   - macOS: `~/Library/Logs/Claude/`
   - Look for MCP-related error messages

### MCP Server Not Appearing in Claude Desktop

1. **Check configuration file syntax**:
   ```bash
   # Validate JSON syntax
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .
   ```

2. **Ensure absolute paths are used**:
   - Use full paths, not relative paths or `~` in JSON config
   - Replace `~` with your actual home directory path

3. **Check for conflicting server names**:
   - Each MCP server must have a unique name
   - If you have both stdio and http configs, use different names

## Using the MCP Server

Once configured, you can ask Claude Desktop questions like:

- "What FABRIC sites are available?"
- "Show me active slices at the RENC site"
- "List all projects using GPUs"
- "Find users with failed slices in the last week"
- "What are the current project memberships?"
- "Show sliver allocation trends over the last month"

**Important**: For the best results, always use the **FABRIC-Reports project** when asking these questions. This ensures Claude has access to both the MCP tools and the domain-specific context from system.md.

Claude will use the MCP tools to query the FABRIC Reports API and provide detailed answers.

## Comparison: HTTP vs Stdio Transport

| Feature | HTTP (this setup) | Stdio |
|---------|------------------|-------|
| **Transport** | HTTPS via mcp-remote | Direct stdio |
| **Deployment** | Remote server | Local Docker or Python |
| **Authentication** | Bearer token | FABRIC config files |
| **Dependencies** | Node.js, jq | Docker or Python |
| **Latency** | Network dependent | Local (faster) |
| **Use Case** | Production server access | Local development/testing |
| **Offline** | No | Yes (after setup) |
| **Token Management** | Manual updates | Auto-refresh via FABRIC SDK |

## Advanced Configuration

### Using a Custom System Prompt

The script supports loading a system prompt from a Markdown file (currently commented out):

1. Uncomment the system prompt lines in `fabric-mcp.sh`:
   ```bash
   SYSTEM_MD="${FABRIC_SYSTEM_MD:-$PWD/system.md}"
   ```

2. Set the environment variable:
   ```bash
   export FABRIC_SYSTEM_MD="/path/to/your/system.md"
   ```

3. Uncomment the `--system` flag in the exec line:
   ```bash
   exec npx mcp-remote \
     "$REMOTE_URL" \
     --header "Authorization: Bearer ${ID_TOKEN}" \
     --system "$SYSTEM_PROMPT"
   ```

**Note**: This requires `mcp-remote` to support the `--system` flag. Check the `mcp-remote` documentation for current feature support.

### Connecting to a Different MCP Server

To connect to a local or staging server:

```bash
export FABRIC_MCP_URL="http://localhost:5000/mcp"
```

Or modify directly in the script or Claude Desktop configuration.

## Configuration Files

- `fabric-mcp.sh` - Shell script that launches mcp-remote with authentication
- `README.md` - This documentation file

## Support

For issues specific to:
- **MCP Server**: Check the main [MCP Server README](../../README.md)
- **FABRIC Reports API**: See [FABRIC Reports documentation](https://reports.fabric-testbed.net/reports/ui/)
- **Claude Desktop**: Visit [Claude Desktop documentation](https://docs.anthropic.com/claude/docs)
- **mcp-remote**: See [mcp-remote npm package](https://www.npmjs.com/package/mcp-remote)

## See Also

- **Stdio Configuration**: See [../stdio/README.md](../stdio/README.md) for local Docker-based setup
- **VS Code Integration**: See [../../vscode/README.md](../../vscode/README.md) for VS Code setup
- **System Prompt**: See [../../system.md](../../system.md) for the LLM system prompt used by the MCP server
