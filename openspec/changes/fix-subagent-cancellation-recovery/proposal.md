# Change: Fix Subagent Cancellation Recovery

## Why

When subagents are cancelled due to timeout, the system discards all completed work and returns `answer: null` with empty `token_usage: {}`. Analysis of production logs shows cancelled subagents often have 100% completion, finished voting, selected winners, and created output files - all of which is lost. This wastes API costs ($0.05-0.08 per cancelled subagent) and degrades parent agent quality by missing valuable context.

**Root cause identified:** The `SubagentManager._execute_with_orchestrator()` uses `asyncio.wait_for()` to enforce timeouts. When timeout occurs, it terminates the subprocess and calls `SubagentResult.create_timeout()` which sets `answer=None` - but **never attempts to read the subagent's workspace for completed work**.

## Architecture Context

### Existing Graceful Selection (orchestrator-level)
The orchestrator already has graceful timeout handling in `_handle_orchestrator_timeout()` (`orchestrator.py:4632-4732`):
- Collects answers from all agents who completed
- Uses `_determine_final_agent_from_votes()` to select best answer by vote count
- Falls back to first agent with answer if no votes

**This same pattern should be applied to subagent timeout recovery.**

### Current Subagent Timeout Flow
```
Parent's asyncio.wait_for() times out
    → process.terminate()
    → SubagentResult.create_timeout(answer=None)
    → MCP tool returns {status: "timeout", answer: null}
    → Parent agent receives null answer
```

### Proposed Recovery Flow
```
Parent's asyncio.wait_for() times out
    → process.terminate()
    → Read subagent workspace:
        - status.json (coordination phase, winner, costs)
        - answer.txt (if orchestrator wrote it)
        - Workspace files (partial outputs)
    → SubagentResult with recovered answer and costs
    → MCP tool returns {status: "completed_but_timeout", answer: "..."}
    → Parent agent receives useful answer
```

## What Changes

### 1. Subagent Manager Changes (`massgen/subagent/manager.py`)
- **Add workspace extraction on timeout**: After terminating subprocess, read `status.json` and `answer.txt` from workspace
- **Apply orchestrator's selection logic**: If multiple agents completed, use vote-based selection (same as `_determine_final_agent_from_votes`)
- **Extract token costs**: Read `costs` section from `status.json` for accurate tracking

### 2. SubagentResult Model Changes (`massgen/subagent/models.py`)
- **New status values**:
  - `completed_but_timeout` - Work finished but timeout triggered (recovered answer available)
  - `partial` - Work in progress when cancelled (partial work available)
  - Keep `timeout` for cases with no recoverable work
- **Add completion_percentage field**: From `status.json` coordination data
- **Factory method**: `create_timeout_with_recovery()` that accepts recovered answer and costs

### 3. MCP Tool Enhancements (`massgen/mcp_tools/subagent/_subagent_mcp_server.py`)
- **Enhanced result format**: Include completion status and recovered data
- **Summary improvements**: Distinguish between hard timeouts vs recovered timeouts

## Impact

- **Affected code**:
  - `massgen/subagent/manager.py` - timeout handling, workspace extraction
  - `massgen/subagent/models.py` - result model, new status values
  - `massgen/mcp_tools/subagent/_subagent_mcp_server.py` - result formatting
- **Affected specs**: New `subagent-orchestration` capability
- **Backward compatibility**:
  - New status values are additive
  - Parent agents already check `status` field per system prompt guidance
  - Token usage field structure unchanged (just populated on timeout)
- **Risk**: Low - changes isolated to timeout path; normal execution unchanged

## References

- Linear: [MAS-207](https://linear.app/massgen-ai/issue/MAS-207)
- GitHub: [#732](https://github.com/massgen/MassGen/issues/732)
