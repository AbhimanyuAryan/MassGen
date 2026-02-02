## Context
The main Textual TUI renders from parsed stream output (`StreamChunk` objects), while subagent views render from `events.jsonl` via `ContentProcessor.process_event()`. This causes visual and behavioral drift between the two views.

## Current State Analysis

### Two Rendering Paths

**Main TUI (stream-chunk path)**:
```
StreamChunk (from backend)
  → CoordinationUI.update_agent_content()
    → display.update_agent_content()
      → TimelineEventAdapter._handle_stream_chunk()
        → ContentProcessor (via direct method calls)
```

**Subagent TUI (event-driven path)**:
```
events.jsonl (written by subagent orchestrator)
  → EventReader (polls file for new lines)
    → TimelineEventAdapter.handle_event()
      → ContentProcessor.process_event()
```

### Event Emission Gaps

The `EventEmitter` class (`massgen/events/emitter.py`) defines methods for all event types:
- `emit_tool_start`, `emit_tool_complete`, `emit_thinking`, `emit_text`, `emit_status`, `emit_round_start`, etc.

**However, these are almost never called from the agent execution path:**
- `chat_agent.py` — emits NO structured events during streaming
- `backend/*.py` — emits NO structured events (only yields `StreamChunk` objects)
- `orchestrator.py` — emits `round_start` and a few coordination events, but not tool/thinking/text events
- Subagent `events.jsonl` files mostly contain raw `STREAM_CHUNK` events, not clean structured events

This means the structured event path (`process_event()`) receives far less granular data than the stream-chunk path, causing rendering differences.

### Concrete Bug: TaskPlanCard

The `is_filtered_tool` function in `ContentProcessor` has two codepaths:
- **Stream-chunk path**: includes an `is_planning_tool` exemption that allows `task_plan` tool calls through even when tools are filtered
- **Structured-event path**: does NOT have this exemption

Result: `TaskPlanCard` renders correctly for main agents but may be incorrectly filtered for subagents.

## Goals / Non-Goals
- Goals:
  - Single rendering path for both main and subagent TUI views
  - All timeline-relevant content emitted as structured events
  - Identical rendering output for the same event sequence regardless of view
  - Inner agent tabs in subagent view show agent_id + model name
- Non-Goals:
  - Redesigning the overall TUI layout or styles
  - Changing the event schema format (only emission completeness and consumption path)

## Decisions
- Decision: Wire `EventEmitter` calls into `chat_agent.py` and backend streaming paths so all content is emitted as structured events.
  - Why: The emitter already exists with all needed methods; we just need to call them.
- Decision: Route the main TUI through `EventReader` + `TimelineEventAdapter.handle_event()` + `ContentProcessor.process_event()` — the same path subagents use.
  - Why: Eliminates the stream-chunk parsing path entirely, guaranteeing parity.
- Decision: Remove `_handle_stream_chunk()` from `TimelineEventAdapter` and related raw-parsing logic from `ContentProcessor`.
  - Why: Having one path is the whole point; keeping the old path as dead code invites regression.
- Decision: Inner agent tabs derived from `execution_metadata.yaml` or event `agent_id` fields.
  - Why: Matches main TUI display pattern.

## Risks / Trade-offs
- Risk: Some content currently only appears in stream parsing; missing event emission would drop content.
  - Mitigation: Phase 1 is a complete audit — catalog every content type the stream-chunk path handles and verify the event emitter covers it.
- Risk: Performance impact from writing all events to `events.jsonl` for main agents.
  - Mitigation: Main agents can use in-memory event bus (no file I/O) with same `EventReader` interface. File-based persistence only needed for subagents (cross-process).
- Risk: Transition period where both paths exist increases complexity.
  - Mitigation: Feature flag to switch between old/new path during development; remove old path once verified.

## Migration Plan

### Phase 1: Audit & Emit (no TUI changes)
1. Audit all content types handled by `_handle_stream_chunk()` — document each one
2. Add `EventEmitter` calls to `chat_agent.py` / backend streaming for each content type
3. Verify `events.jsonl` now contains complete structured events for a full run
4. Compare event stream against stream-chunk timeline to confirm completeness

### Phase 2: Unify Rendering Path
1. Create in-memory event bus for main agents (same interface as `EventReader`)
2. Route main TUI through `TimelineEventAdapter.handle_event()` → `ContentProcessor.process_event()`
3. Run both old and new paths in parallel behind a flag; diff outputs
4. Remove `_handle_stream_chunk()` and stream-chunk parsing once parity confirmed

### Phase 3: Cleanup & Polish
1. Remove dead code (old stream-chunk handling in `ContentProcessor`)
2. Standardize subagent inner-agent tabs
3. Add tests validating identical output for shared event sequences
4. Document the unified pipeline

## Open Questions
- Should main agents use file-based or in-memory event transport? (File is simpler but has I/O cost; in-memory needs a shared bus interface)
- Do we need to preserve `StreamChunk` objects at all, or can backends emit events directly?
