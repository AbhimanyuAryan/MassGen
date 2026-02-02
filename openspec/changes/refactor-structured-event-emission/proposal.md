# Change: Replace string-parsed tool display with structured event emission

## Why

The TUI currently emits tool lifecycle data as emoji-prefixed strings (`"🔧 Calling mcp__filesystem__write_file..."`, `"✅ completed"`, etc.) through `coordination_ui._emit_agent_content()`, then parses those strings back into structured data in `ContentNormalizer.detect_tool_event()`. This round-trip through string serialization:

1. **Loses metadata** — `tool_call_id` is only available on the stream chunk, not on the duplicate `text` event emitted alongside it
2. **Creates dual-path conflicts** — with `_use_event_pipeline=True`, both the old buffer/flush path AND the new event listener process the same content, causing tools to display twice or not at all
3. **Causes timer bugs** — tool cards start counting up but `set_result()` never fires because the completion event can't be matched back to the start (missing tool_call_id)
4. **Is fundamentally backwards** — we control the emission points (backend tool handlers, orchestrator) where all structured data is available, yet we serialize to strings and re-parse

## What Changes

- Emit `TOOL_START`, `TOOL_COMPLETE`, `THINKING`, `TEXT`, `STATUS`, `FINAL_ANSWER` structured events directly from the source (backend tool handlers, `coordination_ui`) with all metadata intact (tool_call_id, tool_name, args, result, elapsed_seconds)
- Stop emitting duplicate `text` events for content that's already covered by stream chunks
- Remove string-based tool detection from the display hot path (`ContentNormalizer.detect_tool_event()`, emoji pattern matching in `_emit_agent_content`)
- Make the event pipeline the single rendering path (no dual-path execution)
- Remove `process_line_buffered` and `_handle_stream_chunk` once structured events cover all content types

## Impact

- Affected specs: `unify-tui-event-pipeline` (this is the completion of that work)
- Affected code:
  - `massgen/backend/base_with_custom_tool_and_mcp.py` — already emits tool events, verify coverage
  - `massgen/frontend/coordination_ui.py` — stop emitting text events for tool content, emit structured events from tool lifecycle points
  - `massgen/frontend/displays/content_processor.py` — simplify `process_event()` handlers, remove string parsing fallbacks
  - `massgen/frontend/displays/tui_event_pipeline.py` — remove `_handle_stream_chunk`, `_map_chunk_type`, stream chunk processing
  - `massgen/frontend/displays/content_normalizer.py` — remove `detect_tool_event()` and emoji pattern matching (or keep only for log replay)
  - `massgen/frontend/displays/content_handlers.py` — `ToolHandler` string parsing becomes unused for live display
