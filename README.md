# MCP-SERVER Project

This project implements a Multi-Tool Integration Architecture using the Model Context Protocol (MCP). It is split into two main components:

1.  **[Frontend (Web UI)](frontend/README.md)**: A user-friendly dashboard for managing tools, viewing logs, and controlling the server.
2.  **[Backend (MCP Server)](backend/README.md)**: The core server implementation handling tool execution, integrations, and resource management.
3.  **[Gateway](gateway/DESIGN.md)**: A centralized orchestrator for managing multiple MCP servers (Phase 2).

## Architecture Overview

The system is designed as a split-process architecture:

-   **Backend Process**: Runs the FastMCP server, managing the tool registry, integrations (DuckDuckGo, Playwright, etc.), and the secure workspace.
-   **Frontend Process**: Runs a FastAPI server serving the Web UI. It communicates with the backend via JSON-RPC (or manages the backend process lifecycle).
-   **Communication**: The Web UI can start/stop the backend process.

## Quick Start

### Using Docker (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd agent-mcp-server
    ```

2.  **Start with Docker Compose**:
    ```bash
    docker-compose up --build
    ```
    Access the dashboard at `http://localhost:8000`.
    
    **Login Credentials:**
    - **Token**: `15ed8c4d77f2cb779c030f2146bf5bbc` (Default for Docker)
    - Enter this token in the login page.

### Manual Setup

1.  **Install dependencies**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install --with-deps chromium
    ```

2.  **Start the Application**:
    ```bash
    ./start.sh
    ```

## Authentication

The server is protected by a Bearer token.
- **Default**: If `MCP_AUTH_TOKEN` is not set, a random token is generated and printed to the console on startup.
- **Configuration**: Set the `MCP_AUTH_TOKEN` environment variable to define a static token.
    ```bash
    export MCP_AUTH_TOKEN="my-secret-token"
    ./start.sh
    ```
    Or in `docker-compose.yml`:
    ```yaml
    environment:
      - MCP_AUTH_TOKEN=my-secret-token
    ```

## Testing

Run the test suite using `pytest`:
```bash
pytest backend/tests
```

## Project Structure

```
mcp-server/
├── frontend/           # Web UI source code and static files
├── backend/            # MCP Server source code, integrations, and config
├── start.sh            # Master startup script
├── .mcp_server.pid     # Lock file for MCP Server (auto-generated)
├── .mcp_web_ui.pid     # Lock file for Web UI (auto-generated)
├── README.md           # This file
└── RESOURCES.md        # Useful links and documentation resources
```
## Documentation

- **[Frontend Documentation](frontend/README.md)**
- **[Backend Documentation](backend/README.md)**
- **[Resources](RESOURCES.md)**


