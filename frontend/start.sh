#!/bin/bash
# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project root is one level up
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default port
PORT=${1:-8000}

# Add project root to PYTHONPATH
export PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH

echo "Starting MCP Frontend (Web UI)..."
echo "  Port: $PORT"
echo "  URL: http://localhost:$PORT"
echo "  Script: $SCRIPT_DIR/src/web_ui.py"

# Run the Web UI with the specified port
exec python3 "$SCRIPT_DIR/src/web_ui.py" --port $PORT
