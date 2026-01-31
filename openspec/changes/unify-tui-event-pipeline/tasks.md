## Phase 1: Audit & Event Emission ✅

- [x] 1.1 Audit all content types handled by `TimelineEventAdapter._handle_stream_chunk()` — document each `StreamChunk` type and what it renders
- [x] 1.2 Audit all content types handled by `ContentProcessor.process_event()` — document which event types are supported
- [x] 1.3 Identify gaps: content types present in stream-chunk path but missing from structured-event path
- [x] 1.4 Wire `EventEmitter` calls into `base_with_custom_tool_and_mcp.py` for tool_start and tool_complete events
- [x] 1.5 Wire `EventEmitter` calls into `coordination_ui._emit_agent_content()` for thinking, text, and status events
- [x] 1.6 Wire `EventEmitter` calls into `orchestrator.py` for status (voting complete) and final_answer events
- [x] 1.7 Fix `is_filtered_tool` inconsistency (TaskPlanCard bug) — add `is_planning_tool` exemption in `_handle_event_tool_start` and `_handle_event_tool_complete`
- [x] 1.8 Verify `events.jsonl` contains structured events for a full main-agent run (confirmed: text, status, final_answer, round_start all present)

## Phase 2: Unify Rendering Path (infrastructure done, activation deferred)

- [x] 2.1 Register main TUI as event listener on `EventEmitter` via `_register_event_listener()` in `MassGenApp.on_mount()`
- [x] 2.2 Add `_handle_event_from_emitter()` to receive events from backend threads and marshal to Textual main thread via `call_from_thread()`
- [x] 2.3 Add `_route_event_to_adapter()` to route events by `agent_id` to per-agent `TimelineEventAdapter`
- [x] 2.4 Add `_use_event_pipeline` feature flag (default `False`) to toggle between old and new rendering paths
- [x] 2.5 Fill remaining event emission gaps before activation:
  - Coordination-level tool messages (workspace actions, emoji-based tool detection in `_emit_agent_content`)
  - Vote/answer tool display events
  - Status change events from `update_agent_status()`
  - Post-evaluation and restart separator content
- [x] 2.6 Run both paths in parallel and diff outputs to verify parity
- [x] 2.7 Set `_use_event_pipeline` default to `True` once parity confirmed
- [ ] 2.8 Remove `_handle_stream_chunk()` from `TimelineEventAdapter` once old path is no longer needed

## Phase 3: Cleanup & Polish

- [ ] 3.1 Remove dead code from old stream-chunk handling (`process_line_buffered`, `_handle_event_stream_chunk`, `_map_chunk_type`)
- [ ] 3.2 Remove feature flag — event pipeline becomes the only path
- [ ] 3.3 Standardize subagent inner-agent tabs to show agent_id + model name
- [ ] 3.4 Add tests validating identical timeline output for shared event sequences
- [ ] 3.5 Document the unified pipeline in `docs/dev_notes/`
