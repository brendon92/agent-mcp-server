# MCP-SERVER Project

This project implements a Multi-Tool Integration Architecture using the Model Context Protocol (MCP). It is split into two main components:

1.  **[Frontend (Web UI)](frontend/README.md)**: A user-friendly dashboard for managing tools, viewing logs, and controlling the server.
2.  **[Backend (MCP Server)](backend/README.md)**: The core server implementation handling tool execution, integrations, and resource management.

## Architecture Overview

The system is designed as a split-process architecture:

-   **Backend Process**: Runs the FastMCP server, managing the tool registry, integrations (DuckDuckGo, Playwright, etc.), and the secure workspace.
-   **Frontend Process**: Runs a FastAPI server serving the Web UI. It communicates with the backend via JSON-RPC (or manages the backend process lifecycle).
-   **Communication**: The Web UI can start/stop the backend process.

## Quick Start

The project includes a master startup script that launches both the backend and frontend.

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd mcp-server
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Start the Application**:
    ```bash
    ./start.sh
    ```
    Access the dashboard at `http://localhost:8000`.

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

## Agentic Workflow

-   **`TASKS.md`**: Check this file in `backend/` or `frontend/` for pending tasks.
-   **`CHANGELOG.md`**: Update this file in `backend/` or `frontend/` when making significant changes.
-   **`implementation_plan.md`**: Always create a plan before starting complex tasks.

## Documentation

- **[Frontend Documentation](frontend/README.md)**
- **[Backend Documentation](backend/README.md)**
- **[Resources](RESOURCES.md)**

---
## LLM Agent Guidelines

> [!IMPORTANT]
> **To all future Agents working on this codebase:**

1.  **Keep it Clean**:
    - Do not create files in the root directory unless absolutely necessary.
    - Place code in `backend/` or `frontend/` appropriately.
    - Remove unused files and directories immediately.

2.  **Markdown Format**:
    - Maintain all documentation in **Markdown** format.
    - Use clear headers, bullet points, and code blocks.
    - Ensure `README.md` files are kept up-to-date with code changes.
    - Use "Codebase Context for LLMs" sections in sub-project READMEs to help future agents understand the context.

## END OF GUIDELINES
---

