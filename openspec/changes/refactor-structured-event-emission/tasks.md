## Phase 1: Audit current emission points

- [x] 1.1 Map every place `update_agent_content()` is called with tool content — document what data is available at each call site vs what's serialized to string
- [x] 1.2 Map every place `emit_text()`/`emit_thinking()`/`emit_status()` is called — identify which ones duplicate stream chunk content
- [x] 1.3 Audit `base_with_custom_tool_and_mcp.py` tool event emission — verify `TOOL_START`/`TOOL_COMPLETE` events carry all needed fields (tool_call_id, tool_name, args, result, elapsed_seconds, server_name)
- [x] 1.4 Document the full data flow for a single MCP tool call from backend → coordination_ui → display, showing where metadata is available and where it's lost

## Phase 2: Emit structured events from source

- [x] 2.1 ~~Ensure `TOOL_START` events are emitted from the backend with: tool_call_id, tool_name, args (dict), server_name~~ — **already complete** (audit 1.3: `base_with_custom_tool_and_mcp.py:~1563`)
- [x] 2.2 ~~Ensure `TOOL_COMPLETE` events are emitted from the backend with: tool_call_id, tool_name, result, elapsed_seconds, is_error, server_name~~ — **already complete** (audit 1.3: lines ~1708, ~1945, ~2021)
- [x] 2.3 In `update_agent_widget()`, skip tool-type content so it's only handled via structured `TOOL_START`/`TOOL_COMPLETE` events from `_handle_event_from_emitter` — preventing duplicate tool cards from the old STREAM_CHUNK string-parsing path
- [x] 2.4 ~~In `coordination_ui._emit_agent_content()`, stop emitting `text` events for content that contains tool markers~~ — **already satisfied**: line 2028 guard `if _emitter and not is_tool_content` prevents tool-marker content from being emitted as text/thinking/status events. `display.update_agent_content` call kept for non-Textual displays and logging.
- [x] 2.5 For non-tool content (thinking, text, status, presentation), ensure structured events carry the correct `agent_id` and `chunk_type` without string re-parsing — fixed: presentation/final_answer content now uses `emit_final_answer()` instead of generic `emit_text()`
- [x] 2.6 Create lightweight agent output file writer that writes to `agent_outputs/agent_N.txt` from structured events, independent of the buffer/flush pipeline
- [x] 2.7 Verify events.jsonl contains clean structured events for a full run — **verified**: TOOL_START/TOOL_COMPLETE events now present (12 starts, 11 completes in test run). Note: tool content still also appears as TEXT events via the old StreamChunk path — that duplication will be removed in Phase 4. **Fix applied**: `claude_code.py` backend was missing `emit_tool_start`/`emit_tool_complete` calls (it has its own tool handling via `ToolUseBlock`/`ToolResultBlock`, bypassing `_execute_tool_with_logging`).

## Phase 3: Consume structured events in TUI

- [x] 3.1 ~~Update `_handle_event_from_emitter()` to process `TOOL_START`/`TOOL_COMPLETE` events from main agents~~ — **already complete**: `_use_event_pipeline` defaults to `True` (line 534), events pass through the STREAM_CHUNK filter at line ~3158
- [x] 3.2 ~~Update `ContentProcessor.process_event()` tool handlers to use event metadata directly~~ — **already complete**: `_handle_event_tool_start/complete` extract metadata directly from `event.data` (no string parsing)
- [x] 3.3 ~~In `_apply_tool_output()`, use `tool_call_id` from the event for card matching~~ — **already complete**: `_event_tool_states` dict uses `tool_id` as key
- [x] 3.4 Verify tool cards show correct timing — **verified**: tool cards display in TUI with timing from structured events
- [x] 3.5 Verify tool batching works with structured events — **verified**: consecutive tool calls batch correctly in live run
- [x] 3.6 Verify event ordering — **verified**: TEXT/THINKING events between tools break batches correctly via `mark_content_arrived()`
- [x] 3.7 Gate old STREAM_CHUNK path for tool content when structured events are active — added emoji-pattern check in `update_agent_widget()` (`textual_terminal_display.py:~3727`): when `_use_event_pipeline=True`, content containing tool markers (`🔧 Calling`, `✅`, `❌`, `Arguments for Calling`, `Results for Calling`) is skipped so tool cards come exclusively from structured events. Both paths remain intact — the gate makes them mutually exclusive.

## Phase 4: Remove old string-parsing path and STREAM_CHUNK

- [x] 4.1 Remove `_handle_stream_chunk()` from `TimelineEventAdapter` — **done**: method no longer exists (removed in prior phases)
- [x] 4.2 Remove `_map_chunk_type()` from `TimelineEventAdapter` — **done**: method no longer exists (removed in prior phases)
- [x] 4.3 Remove `handle_stream_content()` from `TimelineEventAdapter` — **done**: method no longer exists (removed in prior phases)
- [x] 4.4 Remove `process_line_buffered()` from `ContentProcessor` — **done**: method no longer exists (removed in prior phases)
- [x] 4.5 Remove `detect_tool_event()` from `ContentNormalizer` — **done**: method no longer exists (removed in prior phases)
- [x] 4.6 Remove `ToolHandler` string parsing from `content_handlers.py` — **done**: no string-parsing ToolHandler exists (removed in prior phases)
- [x] 4.7 Remove `_use_event_pipeline` feature flag — **done**: flag no longer exists (removed in prior phases)
- [x] 4.8 Remove emoji pattern constants (`TOOL_PATTERNS`, etc.) from `textual_terminal_display.py` — **done**: `TOOL_PATTERNS` dict, `_parse_tool_message()`, `_handle_tool_content()`, `_format_tool_line()`, `_make_full_width_bar()`, and `_format_restart_banner()` all removed
- [x] 4.9 Add backward-compatible `STREAM_CHUNK` handling for subagent log replay (old events.jsonl files may still contain them) — **done**: `content_processor.py`, `timeline_event_recorder.py`, and `textual_terminal_display.py` now use string literal `"stream_chunk"` comparison instead of `EventType.STREAM_CHUNK`
- [x] 4.10 Remove `_handle_event_stream_chunk()` from `ContentProcessor.process_event()` — **done**: method no longer exists (removed in prior phases; legacy replay uses string literal comparison)
- [x] 4.11 Stop writing `STREAM_CHUNK` events to `events.jsonl` — **already done**: `emit_stream_chunk()` was a no-op, now removed entirely
- [x] 4.12 Remove the old buffer/flush path in `update_agent_widget()` — **done**: `update_agent_widget` no longer calls `handle_stream_content()` (already a no-op in prior phases)
- [x] 4.13 Remove `STREAM_CHUNK` from `EventType` enum in `events.py` — **done**: removed from enum, `emit_stream_chunk()` method deleted, all code references updated to use string literal `"stream_chunk"` for old log compat

## Phase 4b: Event pipeline performance (NEW)

- [x] 4b.1 Batch `call_from_thread()` — events from backend threads are accumulated in a thread-safe deque for ~16ms before being marshaled to the Textual main thread in a single `call_from_thread()` call, reducing per-token thread sync overhead. Implemented via `_event_batch`, `_event_batch_lock`, `_event_batch_timer` in `MassGenApp`, with `_flush_event_batch()` and `_route_event_batch()` replacing the per-event `_route_event_to_adapter()`.

## Phase 4c: Lessons learned — dual-path emission pitfalls (NEW)

The following Phase 1 additions from the original plan were **reverted** because they caused duplicate content:

- **`emit_status()` for `mcp_status`/`custom_tool_status` chunks** (6 call sites): These raw strings ("Arguments for Calling...", "Results for Calling...") duplicated the structured `TOOL_START`/`TOOL_COMPLETE` events already emitted by the backend. The event pipeline rendered them as ugly plain text alongside the proper tool cards. **Root cause**: the backend already emits structured tool events — the coordination_ui chunk handlers only need `update_agent_content()` for the old display path.

- **`emit_status()` for `compression_status` chunks** (3 call sites): Same duplication issue.

- **`emit_thinking()` for reasoning chunks** (3 call sites): The reasoning content already flows through `update_agent_content()` → buffer/flush → `_emit_agent_content()` which calls `emit_thinking()`. Adding emission at the reasoning handler created double thinking blocks. **Root cause**: `_emit_agent_content()` is the canonical event emission point for all content that flows through the buffer/flush path.

- **`emit_workspace_action()` for buffer flush** (2 call sites): Kept — these are genuinely new events not emitted elsewhere.

**Key principle**: Do NOT add `emit_*()` calls at coordination_ui chunk handler sites if the content will also flow through `_emit_agent_content()` downstream. That method is the single point of structured event emission for buffered content.

## Phase 5: Testing & validation

- [x] 5.1 Update `test_event_pipeline_parity.py` — **done**: file already contains structured-event-only tests (THINKING, TEXT, STATUS, TOOL_START/COMPLETE, WORKSPACE_ACTION, etc.) with a legacy `stream_chunk` graceful-ignore test
- [x] 5.2 Update `test_tui_event_pipeline.py` — updated `STREAM_CHUNK` test to use string literal `"stream_chunk"` instead of removed enum constant
- [x] 5.3 Test subagent log replay with old-format events.jsonl (containing STREAM_CHUNK) — graceful handling via string literal comparison
- [x] 5.4 Test subagent log replay with new-format events.jsonl (typed events only) — **done**: added `TestNewFormatEventsReplay` class in `test_event_pipeline_parity.py` with 4 tests: full session replay, multi-tool batch, adapter pipeline replay, and no-stream_chunk verification
- [x] 5.5 Run full integration test with MCP tools (filesystem, command_line) and verify all tool cards display correctly with timing — **verified manually**: tool cards, thinking, text all render correctly in Textual TUI
- [ ] 5.6 Verify agent_outputs/agent_N.txt files are complete after a run
- [ ] 5.7 Run pre-commit checks
