# Change: Unify TUI Event Pipeline

## Why
The main TUI and subagent TUI use **two completely different rendering pipelines**, causing visual drift, duplicated logic, and bugs that only appear in one view. Concretely:

- **Main TUI path**: `StreamChunk` → `CoordinationUI` → `display.update_agent_content()` → `TimelineEventAdapter._handle_stream_chunk()` → `ContentProcessor`
- **Subagent TUI path**: `events.jsonl` → `EventReader` → `TimelineEventAdapter.handle_event()` → `ContentProcessor.process_event()`

The two paths parse and filter content differently, leading to real bugs (e.g., `TaskPlanCard` rendering breaks because `is_filtered_tool` checks differ between the stream-chunk path and the structured-event path).

## What Changes
1. **Fill event emission gaps**: `chat_agent.py` and `backend/*.py` currently emit NO structured events. The `EventEmitter` class has methods (`emit_tool_start`, `emit_thinking`, etc.) but they are never called from the agent execution path. Wire these up.
2. **Route main TUI through events.jsonl**: Main agents write structured events to `events.jsonl` via `EventEmitter`. The main TUI reads them via `EventReader` + `TimelineEventAdapter` — the same path subagents already use.
3. **Remove stream-chunk parsing from ContentProcessor**: Eliminate `_handle_stream_chunk()` and the raw-parsing codepath. A single `process_event()` method handles all rendering.
4. **Standardize subagent inner-agent tabs**: Show agent names + model names, allow cycling/filtering.

## Impact
- Affected specs: textual-tui
- Affected code: `chat_agent.py`, `backend/*.py` (event emission), `TimelineEventAdapter`, `ContentProcessor`, `CoordinationUI`, subagent UI tabs
- Risk: Content currently only visible via stream parsing could be lost if event emission is incomplete. Mitigate with an audit-first approach.

## Known Bug Motivating This Work
**TaskPlanCard inconsistency**: The stream-chunk path in `ContentProcessor` has an `is_planning_tool` exemption in its `is_filtered_tool` check, but the structured-event path does not. This means `task_plan` tools render correctly for main agents but may be filtered out for subagents. This is exactly the class of drift that unification eliminates.
