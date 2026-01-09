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

## Injection Strategies

Content injection via hooks is a critical pattern for multi-agent coordination. This section documents the strategies, trade-offs, and API-specific approaches.

### Why Injection Matters

When Agent A provides an answer mid-stream, other agents need to see that update **without losing their progress**. Without injection:
- Agents would need full restarts on every new answer
- 10 minutes of work lost when another agent answers
- Wasted tokens and increased latency

With injection:
- Agents receive updates mid-thought during natural tool pauses
- Conversation history preserved
- Work continues with new context

### Injection Strategies

The `HookResult.inject` field supports two strategies:

#### 1. `tool_result` Strategy (Default for MidStreamInjectionHook)

Appends content to the current tool result. Used for cross-agent updates.

```python
HookResult(
    inject={
        "content": "[UPDATE] New answer from agent2: ...",
        "strategy": "tool_result"
    }
)
```

**Pros**: Minimal message overhead, natural continuation point
**Cons**: Mixed with tool output, model may confuse meta-content with actual output

**API Handling**:
```
Tool Result Message (modified):
  actual_output + "\n" + separator + injection_content + separator
```

#### 2. `user_message` Strategy (Default for HighPriorityTaskReminderHook)

Injects as a separate user message after the tool result. Used for system reminders.

```python
HookResult(
    inject={
        "content": "⚠️ SYSTEM REMINDER\n\nYour TODO list is empty",
        "strategy": "user_message"
    }
)
```

**Pros**: Clear semantic separation, model understands it's not tool output
**Cons**: Additional message in conversation, slightly higher overhead

### API-Specific Injection Patterns

Different LLM APIs have different capabilities for clean injection:

#### Anthropic API (Claude)

The Anthropic API supports **multiple content blocks** in a single message. This is the cleanest approach:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "call_123",
      "content": "actual tool output here"
    },
    {
      "type": "text",
      "text": "<system-reminder>Your TODO list is empty...</system-reminder>"
    }
  ]
}
```

**Benefits**:
- Tool result semantically separate from reminder
- Model clearly understands the distinction
- No string parsing ambiguity

#### OpenAI API (GPT-4, o1, etc.)

OpenAI's API doesn't support mixed content blocks in tool responses. Two approaches:

**Option 1: Separate User Message**
```json
// Tool result (clean)
{"role": "tool", "tool_call_id": "call_123", "content": "actual output"}

// Separate injection
{"role": "user", "content": "<system-reminder>Your TODO list is empty</system-reminder>"}
```

**Option 2: Structured Tool Output**
```json
{
  "role": "tool",
  "tool_call_id": "call_123",
  "content": "{\"output\": \"actual output\", \"system_notes\": [\"TODO list empty\"]}"
}
```

With system prompt explaining the format:
> Tool results are JSON with `output` (actual result) and `system_notes` (contextual reminders).

#### Visual Separation Pattern

When appending to tool result strings (any API), use clear visual separators:

```
actual tool output here

═══════════════════════════════════════════════════════
SYSTEM CONTEXT (not part of tool output):
- Your TODO list is empty
- Consider using TodoWrite for multi-step tasks
═══════════════════════════════════════════════════════
```

The visual separation helps the model understand it's meta-content.

### Workspace Handling During Injection

When injecting answers from other agents, workspace paths must be normalized so the receiving agent can actually access the files.

#### The Problem

Each agent has an isolated workspace:
- Agent A: `.massgen/workspaces/agent_a_workspace/`
- Agent B: `.massgen/workspaces/agent_b_workspace/`

If Agent A provides an answer referencing `/path/to/massgen/workspaces/agent_a_workspace/output.py`, Agent B cannot access that path.

#### The Solution: Path Normalization

During injection, workspace paths are normalized to temporary workspace paths:

```python
# Before normalization (Agent A's answer)
"I created the file at /Users/foo/.massgen/workspaces/agent_a_workspace/output.py"

# After normalization (what Agent B sees)
"I created the file at /Users/foo/.massgen/temp_workspaces/agent1/output.py"
```

The `_normalize_workspace_paths_in_answers()` method:
1. Identifies all agent workspace paths in the answer
2. Maps them to anonymous temporary workspace paths
3. Creates anonymous agent IDs (`agent1`, `agent2`) for privacy

#### Workspace Snapshot Sharing

When Agent A provides an answer:
1. Agent A's workspace is snapshotted to `.massgen/snapshots/agent_a/`
2. The snapshot is copied to Agent B's temp workspace at `.massgen/temp_workspaces/agent1/`
3. Paths in the injected answer point to the temp workspace
4. Agent B can now read Agent A's files for verification

#### Anonymization Trade-off

**What we preserve**: Agent anonymization (Agent B doesn't know "agent1" is really "Agent A")
**What we lose**: Self-identification (Agent B knows the injection isn't from itself)

This is an acceptable trade-off because:
- Knowing an update is external is useful (prevents self-confirmation loops)
- Anonymization between other agents still prevents bias
- The alternative (full restart) loses ALL progress

### Implementation Details

The injection flow in MassGen:

```
┌─────────────────────────────────────────────────────────────────┐
│ Agent B executing tool (e.g., Read file)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PostToolUse hooks execute                                        │
│ 1. MidStreamInjectionHook checks for pending updates            │
│ 2. If new answers exist → get_injection_content() called        │
│ 3. HighPriorityTaskReminderHook checks tool output for reminders      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ HookResult.inject aggregated                                     │
│ - MidStreamInjection: {content: "[UPDATE]...", strategy: tool}  │
│ - ReminderExtraction: {content: "⚠️ REMINDER", strategy: user}  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Backend applies injection based on strategy                      │
│ - tool_result: Append to current tool result content            │
│ - user_message: Add separate message after tool result          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Agent B continues with injected context                          │
│ - Sees new answers from other agents                            │
│ - Sees system reminders                                          │
│ - Conversation history preserved                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Timing Considerations

Mid-stream injection has timing constraints:

1. **First Injection**: Uses traditional full-message approach (not mid-stream)
   - Prevents premature convergence where agents immediately adopt first answer

2. **Subsequent Injections**: Use mid-stream hook injection
   - Lighter weight, preserves agent's work in progress
   - Only new answers (not already seen) are injected

3. **Vote-Only Mode**: Skips mid-stream injection entirely
   - Tool schemas are fixed at stream start
   - Can't update vote enum mid-stream
   - Full restart required for new vote options

## Open Questions

- Should hooks be able to spawn async tasks? (Deferred to future work)
- Should we support hook chaining with priority? (Using registration order for now)

## References

- Claude Code's injection pattern: Separate content blocks in Anthropic API
- OpenAI Response API: Structured JSON tool output pattern
- MassGen coordination: `orchestrator.py:_setup_hook_manager_for_agent()`
