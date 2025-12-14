# Agent-to-Agent (A2A) Communication Patterns

## Overview
As the MCP ecosystem grows, agents need to communicate not just with servers, but with each other to coordinate complex tasks. This document explores potential A2A patterns.

## Patterns

### 1. Shared Workspace / Blackboard
- **Concept**: Agents read and write to a shared state (e.g., a database or file).
- **Pros**: Simple, decoupled.
- **Cons**: Polling required, race conditions.

### 2. Direct Messaging (Actor Model)
- **Concept**: Agents send addressed messages to each other.
- **Pros**: Low latency, clear intent.
- **Cons**: Service discovery needed, tight coupling.

### 3. Pub/Sub (Event Bus)
- **Concept**: Agents publish events ("Task Completed", "New Information") and others subscribe.
- **Pros**: Highly decoupled, scalable.
- **Cons**: Event schema management.

### 4. Hierarchical (Manager-Worker)
- **Concept**: A "Manager" agent breaks down tasks and assigns them to "Worker" agents.
- **Pros**: Clear control flow.
- **Cons**: Single point of failure (Manager).

## Recommendation for MCP Server
Implement a **Pub/Sub** mechanism via the Gateway.
- The Gateway can act as the Event Bus.
- Agents subscribe to topics (e.g., `tools.filesystem.events`).
- When a tool is executed, an event is published.
