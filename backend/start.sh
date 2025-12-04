#!/bin/bash
# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project root is one level up
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default port (MCP server uses stdio, but we can add HTTP support later)
PORT=${1:-8001}

# Add project root to PYTHONPATH
export PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH

echo "Starting MCP Backend Server..."
echo "  Port: $PORT (Note: MCP uses stdio, port is for future HTTP mode)"
echo "  Script: $SCRIPT_DIR/src/server.py"

# Run the server
exec python3 "$SCRIPT_DIR/src/server.py"
