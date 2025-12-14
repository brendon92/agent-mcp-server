# MCP Gateway Design

## Overview
The MCP Gateway acts as a centralized orchestrator that manages multiple MCP servers. It provides a single entry point for clients (agents) to access tools distributed across different servers.

## Architecture

```mermaid
graph TD
    Client[MCP Client / Agent] --> Gateway[MCP Gateway]
    Gateway --> Server1[MCP Server 1 (Filesystem)]
    Gateway --> Server2[MCP Server 2 (Browser)]
    Gateway --> Server3[MCP Server 3 (Search)]
```

## Core Responsibilities

1.  **Server Registration**:
    - Dynamic registration of MCP servers.
    - Health checking of registered servers.

2.  **Tool Aggregation**:
    - Aggregates tools from all registered servers into a unified list.
    - Namespacing to prevent collisions (e.g., `server1.read_file`).

3.  **Routing**:
    - Routes tool execution requests to the appropriate downstream server.
    - Handles authentication and error propagation.

## Implementation Plan

### Phase 1: Basic Proxy
- Static configuration of downstream servers.
- Simple pass-through of tool listing and execution.

### Phase 2: Dynamic Discovery
- API for servers to register themselves.
- Heartbeat mechanism.

### Phase 3: Intelligent Routing
- Load balancing.
- Capability-based routing.

## API Design

### Configuration (`gateway_config.yaml`)
```yaml
servers:
  - name: "local-fs"
    url: "http://localhost:8001"
    token: "secret-token"
  - name: "browser"
    url: "http://localhost:8002"
```

### Endpoints
- `GET /api/tools`: Returns aggregated list of tools.
- `POST /api/tools/execute`: Executes a tool on the target server.
