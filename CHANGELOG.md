# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Docker Support**: Added `Dockerfile` for backend and frontend, and `docker-compose.yml` for orchestration.
- **Authentication**: Implemented Token-based Authentication for Web UI and API endpoints.
- **Testing**: Added comprehensive unit tests for backend (`pytest`) and authentication logic.
- **Gateway**: Implemented basic MCP Gateway for multi-server orchestration (Phase 2).
- **Research**: Added research on Agent-to-Agent (A2A) communication patterns.
- Initial project structure and documentation.

### Fixed
- Resolved "Process stdin closed" error for `fetch_url` and `kill_process` tools.
- Fixed Web UI "half built" state by correcting configuration paths.
- Fixed Console Log widget truncation and "Invalid Date" issues.
- Fixed Health Indicator to reflect actual server status.
- Fixed Web UI to properly detect manually started MCP servers (prevents duplicate instances).
  - Added `psutil` for process detection.
  - Added PID file tracking for reliable server discovery.
  - Web UI can now stop externally started servers.
  - Added single-instance lock mechanism for both MCP Server and Web UI.
- Added `start.sh` for unified process management.
- Fixed `fetch_url` tool in Playground by replacing external dependency with native `playwright` implementation.
- Fixed `kill_process` tool execution by updating command to use `uvx`.
- `CHANGELOG.md` file created.
- `TASKS.md` file created.
- LLM Agent rules added to `README.md`.
- Implemented `ServerConfig` and `MCPIntegration` architecture.
- Implemented `ToolRegistry` with integration support.
- Implemented `DuckDuckGo` web search integration.
- Implemented `PostgreSQL` and `SQLite` database integrations.
- Implemented `Local Commands` integration with security checks.
- Implemented `Git` integration.
- Added `enabled_integrations.yaml` configuration.
- Added new LLM Agent rules: "Predict Future Problems" and "Prioritize Free Tools".
