# Change: Add General Hook Framework for Agent Lifecycle Events

## Why

Multiple MassGen features require injecting content or intercepting operations at specific points in the agent lifecycle (mid-stream injection, reminder injection, permission validation). Currently, these are implemented as ad-hoc patterns scattered across the codebase. A general hook framework provides a standardized, composable way to:

- Inject content into conversations at tool boundaries
- Block or modify tool operations
- Track and observe agent behavior
- Extend functionality without modifying core code

This follows patterns established by Claude Code hooks and Claude Agent SDK.

## What Changes

- Add `PreToolUse` and `PostToolUse` hook events to the existing hook infrastructure
- Support both Python callable hooks and external command hooks (JSON stdin/stdout protocol)
- Add YAML configuration for registering hooks at **two levels**:
  - **Global hooks** (top-level `hooks:` section) - apply to ALL agents
  - **Per-agent hooks** (in agent's `backend.hooks:`) - can override or extend global hooks
- **Migrate existing patterns** to use hooks:
  - Mid-stream injection (answers from other agents → tool results)
  - Tool result injection building
  - Reminder injection (tool result → user message)
  - Permission hooks (unify with new framework)

## Impact

- **Affected specs**: New `hook-framework` capability
- **Affected code**:
  - `massgen/mcp_tools/hooks.py` - Core infrastructure
  - `massgen/backend/base_with_custom_tool_and_mcp.py` - Integration point
  - `massgen/backend/base.py` - Hook setup
  - `massgen/orchestrator.py` - Global hook registration, built-in hooks
  - `massgen/config_validator.py` - YAML validation
