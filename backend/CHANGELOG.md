# Backend Changelog

## [Unreleased]

### Fixed
- Resolved "Process stdin closed" error for `fetch_url` and `kill_process` tools.
- Fixed `fetch_url` tool by replacing external dependency with native `playwright`.
- Fixed `kill_process` tool execution by using `uvx`.
- Fixed server startup failure due to tool name collision.
- Fixed "no current event loop" async error during startup.

### Added

#### Integrations
- Implemented `ToolRegistry` with integration support.
- Implemented `DuckDuckGo`, `SQLite`, `Local Commands`, `Git` integrations.
- Added `enabled_integrations.yaml` configuration.
- Implemented `multi_engine` web search integration using `open-websearch`.
- Enabled `puppeteer` browser integration.
- Implemented `ssh` integration for remote command execution.
- Implemented `git_ingest` integration for GitHub repository analysis.
- Configured `searxng` integration (disabled by default, requires instance URL).
- Configured `postgres` integration (disabled by default, requires connection URL).
- Implemented `code_runner` integration for isolated code execution.

#### Secure File System
- Implemented `BoxedPath` class with sandboxing and strict validation.
- Implemented atomic file write pattern (`AtomicWriter`) with TOCTOU protection.
- Enhanced `BoxedPath` with `sys.audit` hooks and `os.path.realpath` validation.
- Added `QuotaEnforcedFile` wrapper (10MB default limit).
- Added `FileSystemIntegration` with tools: `list_directory`, `read_file`, `write_file`, `delete_file`, `search_files`.
- Added advanced file tools: `mkdir`, `copy_file`, `move_file`, `append_file`, `chmod_file`.

#### Error Handling & Logging
- Refactored `ToolRegistry` with `logging` (replaced `print` statements).
- Added custom exceptions: `ToolNotFoundError`, `ToolExecutionError`.
- Added `sys.audit` hooks for tool call monitoring.

#### Testing
- Added unit tests for `BoxedPath` (traversal, symlinks, quotas).
- Added unit tests for `FileSystemIntegration` tools.
- Added unit tests for `ToolRegistry` error handling.

