# Agent MCP Server

**A production-ready Model Context Protocol server designed for complex, agentic AI workflows.**

## Features

-   **Secure by Default**: Enforced environment-based auth, input sanitization, and sandboxed code execution.
-   **Agentic Capabilities**: Supports "Reasoning" features like Human-in-the-Loop (`ask_human`) and reactive filesystem notifications.
-   **Observability**: Structured JSON logging with trace IDs and rate limiting.
-   Check `logs/backend_server.log`: You should see JSON log lines.
-   **Modular Architecture**: Pluggable Executors (Docker/Local) and clear tool separation.

## Usage

### Prerequisites
-   Docker (recommended for sandboxing)
-   Python 3.11+
-   An MCP Client (e.g., `forgery-ai-agent` or Claude Desktop)

### Quick Start (Docker)

1.  Create a `.env` file:
    ```bash
    MCP_AUTH_TOKEN=your-secure-token-here
    ```

2.  Run with Docker Compose:
    ```bash
    docker-compose up backend
    ```

3.  Connect your agent to the stdio or SSE endpoint (depending on deployment).

### Configuration

Configuration is managed via Environment Variables (Pydantic validated).

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_AUTH_TOKEN` | **Required**. Secret token for auth. | - |
| `MCP_SANDBOX_ENABLED` | Enable Docker-based isolation. | `True` |
| `MCP_WORKSPACE_DIR` | Root directory for file operations. | `./test_workspace` |

## Architecture

See [DESIGN.md](DESIGN.md) for detailed diagrams and decision logs.

## Security

-   **Sandboxing**: Code execution runs in isolated Docker containers by default.
-   **Path Traversal Prevention**: All file operations are jailed to the workspace.

## Development

Run conformance tests:
```bash
pytest tests/conformance
```

See [TASKS.md](TASKS.md) for roadmap.
