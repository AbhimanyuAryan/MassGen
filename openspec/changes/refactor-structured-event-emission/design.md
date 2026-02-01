## Context

The TUI display pipeline has two paths for rendering tool calls:

1. **Old path** (buffer/flush): `coordination_ui._emit_agent_content()` → `update_agent_content(content, "tool")` → buffer → `_flush_buffers` → `update_agent_widget` → `handle_stream_content` → `ContentNormalizer.detect_tool_event()` (string parsing)
2. **New path** (event pipeline): `EventEmitter.emit_tool_start()` → `_handle_event_from_emitter()` → `TimelineEventAdapter.handle_event()` → `ContentProcessor.process_event()`

Both paths run simultaneously when `_use_event_pipeline=True`, causing conflicts. The old path carries `tool_call_id` (from stream chunks) but the new path's duplicate `text` events don't, breaking tool card matching and timing.

## Goals / Non-Goals

**Goals:**
- Single rendering path: structured events flow from source → TUI with no string serialization round-trip
- All tool metadata (tool_call_id, args, result, elapsed, server_name) available without parsing
- Tool cards display correctly: show args, stop timer on complete, show result
- Tool batching works: consecutive MCP tools from same server batch correctly

**Non-Goals:**
- Changing the events.jsonl format (it already supports structured events)
- Changing subagent event handling (subagents already use structured events from events.jsonl)
- Removing ContentNormalizer entirely (still needed for text/thinking filtering)

## Decisions

### Emit from the source, not the relay

Tool events should be emitted by the code that has the structured data:
- `base_with_custom_tool_and_mcp.py` already emits `TOOL_START`/`TOOL_COMPLETE` — verify these reach the TUI
- `coordination_ui` should NOT re-emit tool content as `text` events

**Alternative considered:** Parse tool_call_id from text events. Rejected — this is the exact pattern we're eliminating.

### Keep ContentNormalizer for non-tool content

`ContentNormalizer` still serves a purpose for:
- Filtering thinking content (coordination markers, system prompts)
- Detecting injection/reminder content
- Presentation content handling

Only the tool-specific parsing (`detect_tool_event`, emoji patterns) becomes unnecessary for live display.

### Keep string parsing for log replay

Subagent event replay from `events.jsonl` may encounter older logs without structured tool events. Keep `detect_tool_event()` available but move it out of the hot path.

## Data Flow (Target State)

```
Backend (tool call)
  ├── emit TOOL_START {tool_call_id, tool_name, args, server_name}
  ├── ... tool executes ...
  └── emit TOOL_COMPLETE {tool_call_id, tool_name, result, elapsed_seconds}
        │
        ▼
EventEmitter.emit() → listeners
        │
        ▼
TUI._handle_event_from_emitter(event)
        │
        ▼ (call_from_thread)
TUI._route_event_to_adapter(event)
        │
        ▼
TimelineEventAdapter.handle_event(event)
        │
        ▼
ContentProcessor.process_event(event) → ContentOutput
        │
        ▼
TimelineEventAdapter._apply_tool_output(output) → timeline.add_tool() / update_tool()
```

No string serialization. No emoji parsing. No dual paths.

## Risks / Trade-offs

- **Risk:** Breaking subagent display if it relies on stream chunks.
  → Mitigation: Subagents already use events.jsonl with structured events. Keep stream chunk handling as fallback for legacy logs.

- **Risk:** Missing tool events for some backends.
  → Mitigation: Phase 1 audit maps all emission points. Phase 2 verifies events.jsonl coverage.

## Open Questions

- Should we keep `update_agent_content` at all for tool content, or remove it entirely? (It still writes to agent output files — may need a separate file-writing path)
- Should the event pipeline handle the `coordination_ui` buffer/flush path's debouncing, or rely on Textual's own batching?
