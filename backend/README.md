# MCP Server - Backend

The Backend component is the core implementation of the Model Context Protocol server. It manages tool registration, execution, and third-party integrations.

## Features

- **Multi-Tool Support**: Native tools + Third-party integrations.
- **Integrations**:
    - **Web Search**: DuckDuckGo, Multi-Engine, SearXNG.
    - **Browser**: Playwright, Puppeteer.
    - **Database**: SQLite, PostgreSQL.
    - **Filesystem**: Secure file operations with `BoxedPath` sandboxing.
    - **Command**: Local commands, Process management, SSH.
    - **VCS**: Git, GitHub Ingest.
    - **Developer**: Code Runner.
- **Dynamic Registry**: Load and manage tools dynamically.
- **Security**:
    - **Sandboxing**: `BoxedPath` abstraction for filesystem isolation.
    - **Atomic Operations**: Safe file writes to prevent TOCTOU attacks.
    - **Audit Logging**: Comprehensive logging of all tool executions.
- **Single-Instance Protection**: Prevents multiple server instances.

## Structure

```
backend/
├── src/
│   ├── server.py        # Main FastMCP server entry point
│   ├── registry.py      # Tool registration system
│   ├── workspace.py     # Workspace management
│   ├── integrations/    # Integration modules
│   │   ├── web_search/  # DuckDuckGo, Multi-Engine, SearXNG
│   │   ├── browser/     # Playwright, Puppeteer, Fetch
│   │   ├── database/    # SQLite, PostgreSQL
│   │   ├── command/     # Local Commands, Process Mgmt, SSH
│   │   ├── vcs/         # Git, Git Ingest
│   │   └── developer/   # Code Runner
│   ├── tools/           # Native tool implementations
│   └── utils/           # Utilities
├── config/              # Configuration files
├── README.md            # This file
├── CHANGELOG.md         # Backend-specific changes
└── TASKS.md             # Backend-specific tasks
```

## Configuration

Configuration files are located in `backend/config/`:
- `workspace_config.yaml`: General server settings.
- `enabled_integrations.yaml`: Toggle and configure integrations.

## Running Locally

```bash
./backend/start.sh
# or
python3 backend/src/server.py
```

> **Note**: The server uses a lock file (`.mcp_server.pid`) to prevent multiple instances.

## Codebase Context for LLMs

### Key Classes

- **`ServerConfig`** (`src/config/settings.py`): Manages configuration from `config/workspace_config.yaml`.
- **`ToolRegistry`** (`src/registry.py`): Central component for managing tools and integrations.
- **`Workspace`** (`src/workspace.py`): Handles file system isolation and security.
- **`BoxedPath`** (`src/utils/security.py`): Enforces secure path validation and sandboxing.
- **`MCPIntegration`** (`src/integrations/base.py`): Base class for all integrations.

### Data Flow

1. **Startup**: `server.py` initializes `ServerConfig`, `Workspace`, and `ToolRegistry`.
2. **Registration**: `ToolRegistry` loads integrations from `src/integrations/`.
3. **Request**: MCP requests are routed to the appropriate integration.
4. **Execution**: Tool executes and returns results.
