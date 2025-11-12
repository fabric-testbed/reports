#!/bin/bash

# Script to run the FABRIC Reports MCP server locally (stdio mode)
# Usage:
#   ./run_local.sh [token]                         # Provide token directly
#   Or: export FABRIC_RC=/path/to/fabric_config    # Use FABRIC config directory
#   Or: export FABRIC_TOKEN=YOUR_TOKEN             # Use token from environment

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if token is provided as argument
if [ -n "$1" ]; then
    export FABRIC_TOKEN="$1"
fi

# Check if credentials are available (either FABRIC_RC or FABRIC_TOKEN)
if [ -z "$FABRIC_RC" ] && [ -z "$FABRIC_TOKEN" ]; then
    echo "Error: Neither FABRIC_RC nor FABRIC_TOKEN is set"
    echo ""
    echo "Usage Options:"
    echo "  1. Use FABRIC_RC (recommended):"
    echo "     export FABRIC_RC=/Users/username/fabric_config"
    echo "     ./run_local.sh"
    echo ""
    echo "  2. Use FABRIC_TOKEN directly:"
    echo "     ./run_local.sh YOUR_TOKEN"
    echo "     Or: export FABRIC_TOKEN=YOUR_TOKEN && ./run_local.sh"
    echo ""
    exit 1
fi

# Validate FABRIC_RC if set
if [ -n "$FABRIC_RC" ]; then
    if [ ! -d "$FABRIC_RC" ]; then
        echo "Error: FABRIC_RC directory does not exist: $FABRIC_RC"
        exit 1
    fi

    # Check for fabric_rc configuration file
    if [ -f "$FABRIC_RC/fabric_rc" ]; then
        echo "Using FABRIC_RC: $FABRIC_RC"
        echo "Found fabric_rc configuration file"
        # Source the fabric_rc file to make variables available
        # shellcheck disable=SC1090
        source "$FABRIC_RC/fabric_rc"
    else
        echo "INFO: fabric_rc configuration file not found at $FABRIC_RC/fabric_rc"
        # Check for token files
        if [ ! -f "$FABRIC_RC/token.json" ] && [ ! -f "$FABRIC_RC/id_token.json" ]; then
            echo "Warning: No token files found in $FABRIC_RC"
            echo "         Expected fabric_rc file or token.json/id_token.json"
            echo "         Authentication may fail"
        fi
    fi
fi

# Set transport mode to stdio (local)
export MCP_TRANSPORT="stdio"

# Set default API base URL if not already set
if [ -z "$REPORTS_API_BASE_URL" ]; then
    export REPORTS_API_BASE_URL="https://reports.fabric-testbed.net/reports"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Run the MCP server in stdio mode
echo "Starting FABRIC Reports MCP server in stdio mode..."
echo "API Base URL: $REPORTS_API_BASE_URL"
echo ""
python3 mcp_reports_server.py
