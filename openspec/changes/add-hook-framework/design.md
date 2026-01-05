# Design: Hook Framework

## Context

MassGen has several ad-hoc injection patterns:
1. Mid-stream injection via callback (`set_mid_stream_injection_callback`)
2. Reminder extraction inline in tool execution
3. Permission hooks via `FunctionHookManager`

These need unification into a general framework following Claude Agent SDK patterns.

## Goals

- Unified hook registration and execution
- Support Python callables and external command hooks
- Pattern-based matching (tool name regex/glob)
- Backward compatibility with existing permission hooks
- Clean migration path for existing injection patterns

## Non-Goals

- Hook events beyond PreToolUse/PostToolUse (deferred)
- GUI for hook management
- Remote/distributed hook execution

## Decisions

### Decision 1: Extend existing hooks.py

**What**: Build on existing `HookType`, `HookResult`, `FunctionHook`, `FunctionHookManager` in `mcp_tools/hooks.py`

**Why**: Reuse existing infrastructure, maintain backward compatibility with permission hooks

**Alternatives considered**:
- New module: Would duplicate functionality and create migration burden
- Replace entirely: Would break existing permission hook usage

### Decision 2: Two-level hook registration (Global + Per-Agent)

**What**: Support both global hooks (apply to all agents) and per-agent hooks (extend or override)

```yaml
# Global hooks - apply to ALL agents
hooks:
  PreToolUse:
    - matcher: "*"
      handler: "massgen.hooks.audit_all_tools"
      type: "python"

agents:
  - id: "agent1"
    backend:
      # Per-agent hooks - extend global by default
      hooks:
        PreToolUse:
          - matcher: "Write"
            handler: "custom_write_hook.py"
            type: "command"
        PostToolUse:
          override: true  # Only use per-agent hooks, disable global
          hooks:
            - handler: "agent1_logging.py"
              type: "command"
```

**Why**:
- Global hooks simplify common cross-cutting concerns (auditing, security)
- Per-agent hooks allow customization for specialized agents
- Override capability prevents hook conflicts

**Alternatives considered**:
- Agent-only hooks: Would require duplicating hooks across all agents
- Global-only hooks: Would prevent agent-specific customization

### Decision 3: HookEvent/HookResult dataclasses as contracts

**What**: Use typed dataclasses for hook input/output

```python
@dataclass
class HookEvent:
    hook_type: str
    session_id: str
    orchestrator_id: str
    agent_id: Optional[str]
    timestamp: datetime
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str] = None  # PostToolUse only

@dataclass
class HookResult:
    allowed: bool = True
    decision: Literal['allow', 'deny', 'ask'] = 'allow'
    reason: Optional[str] = None
    updated_input: Optional[Dict[str, Any]] = None
    inject: Optional[Dict[str, Any]] = None
```

**Why**: Type safety, clear contracts, JSON serializable for external hooks

### Decision 4: Pattern matching via fnmatch

**What**: Use `fnmatch` for tool name matching (glob patterns)

**Why**: Simple, familiar syntax (`*`, `?`, `[seq]`), no regex complexity for common cases

**Example**: `matcher: "Write|Edit"` matches Write or Edit tools

### Decision 5: External command protocol

**What**: JSON stdin/stdout with environment variables

- stdin: JSON-encoded HookEvent
- stdout: JSON-encoded HookResult
- Environment: `MASSGEN_HOOK_TYPE`, `MASSGEN_TOOL_NAME`, etc.

**Why**: Language-agnostic, follows Claude Code conventions

### Decision 6: Error handling - fail open/closed by type

**What**:
- Timeout: Fail open (allow) - don't block agent on slow hooks
- Import errors: Fail closed (deny) - configuration error
- Runtime errors: Fail open with logging - don't crash agent

**Why**: Balance safety with reliability

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Hook execution overhead | Lazy loading, async execution, short timeouts |
| Breaking existing permission hooks | Backward compatible HookResult, gradual migration |
| External hook security | Environment isolation, timeout enforcement |

## Migration Plan

1. Add new hook types and classes (non-breaking)
2. Add GeneralHookManager alongside FunctionHookManager
3. Create built-in hooks for existing patterns
4. Migrate orchestrator to use new hooks
5. Deprecate old injection callback patterns
6. Remove old code in future release

## Open Questions

- Should hooks be able to spawn async tasks? (Deferred to future work)
- Should we support hook chaining with priority? (Using registration order for now)
