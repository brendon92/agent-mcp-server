#!/bin/bash

# Kill existing processes
echo "Stopping existing processes..."
pkill -f "python3 .*web_ui.py"
pkill -f "python3 .*server.py"

# Wait a moment
sleep 2

# Start Web UI using its startup script
echo "Starting Web UI..."
./frontend/start.sh > web_ui.log 2>&1 &
WEB_UI_PID=$!

# Wait for Web UI to be ready
echo "Waiting for Web UI to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "Web UI is ready!"
        echo "Access at: http://localhost:8000"
        break
    fi
    sleep 1
done

# Keep script running
wait $WEB_UI_PID
