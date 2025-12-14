# MCP Server - Frontend (Web UI)

The Frontend component provides a web-based dashboard for interacting with the MCP Server.

## Features

- **Tool Explorer**: Browse available tools and their capabilities.
- **Playground**: Execute tools directly from the browser with a user-friendly interface.
- **Console Log**: Real-time log of server events, tool executions, and errors.
- **Task Manager**: Track running and completed tasks.
- **Server Control**: Start, stop, and restart the MCP Server backend.
- **External Server Detection**: Automatically detects manually started backend servers.
- **Single-Instance Protection**: Prevents multiple Web UI instances from running.

## Structure

```
frontend/
├── src/
│   ├── web_ui.py       # FastAPI application serving the UI
│   └── static/         # HTML, CSS, JS assets
├── README.md           # This file
├── CHANGELOG.md        # Frontend-specific changes
└── TASKS.md            # Frontend-specific tasks
```

## Development

The Web UI is built with **FastAPI** (backend) and **Vanilla JS/CSS** (frontend).

### Running Locally

### Using Docker (Recommended)
```bash
docker-compose up frontend
```

### Manual Setup

You can run the frontend independently (though it requires the backend code to be present for imports):

```bash
./frontend/start.sh
# or
python3 frontend/src/web_ui.py
```

Access the dashboard at `http://localhost:8000`.

### Authentication

The Web UI is protected by a Bearer token.
- **Default**: If `MCP_AUTH_TOKEN` is not set, a random token is generated on startup.
- **Login**: Use the generated token to log in via the `/login.html` page.

> **Note**: The Web UI uses a lock file (`.mcp_web_ui.pid`) to prevent multiple instances.
> If you see "Error: MCP Web UI is already running", kill the existing process first.

### Server Detection

The Web UI automatically detects if the MCP Server backend is running:
- Uses PID file (`.mcp_server.pid`) for fast detection
- Falls back to process scanning via `psutil`
- Health widget shows green when server is running, red when stopped
- Can stop externally started servers via the UI

## Codebase Context for LLMs

### Architecture

- **Backend (FastAPI)**: `src/web_ui.py`
    - Serves static files from `src/static/`.
    - Provides API endpoints for server control (`/api/control/start`, `/api/control/stop`) and status (`/api/status`).
    - Proxies requests to the MCP Server if needed (though currently mostly independent control).

- **Frontend (Vanilla JS)**: `src/static/app.js`
    - **`App` Class**: Main entry point, manages state and initialization.
    - **`MCPClient` Class**: Handles communication with the MCP Server (JSON-RPC).
    - **`ToolManager` Class**: Renders the tool list and handles tool execution UI.
    - **`LogManager` Class**: Manages the console log display.

### Key Files

- `src/static/index.html`: Main layout.
- `src/static/style.css`: Styling (Vanilla CSS).
- `src/static/app.js`: Core logic.

