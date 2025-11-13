#!/bin/bash

# Script to run the FABRIC Reports MCP server in HTTP mode
# Usage: ./run_http.sh

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Set transport mode to http
export MCP_TRANSPORT="http"

# Set default API base URL if not already set
if [ -z "$REPORTS_API_BASE_URL" ]; then
    export REPORTS_API_BASE_URL="https://reports.fabric-testbed.net/reports"
fi

# Set default port and host if not already set
if [ -z "$PORT" ]; then
    export PORT="5000"
fi

if [ -z "$HOST" ]; then
    export HOST="0.0.0.0"
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

# Run the MCP server in HTTP mode
echo "Starting FABRIC Reports MCP server in HTTP mode..."
echo "API Base URL: $REPORTS_API_BASE_URL"
echo "Listening on http://$HOST:$PORT"
echo ""
python3 mcp_reports_server.py
