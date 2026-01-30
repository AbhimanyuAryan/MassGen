## Phase 1: Audit & Event Emission
- [ ] 1.1 Audit all content types handled by `TimelineEventAdapter._handle_stream_chunk()` — document each `StreamChunk` type and what it renders
- [ ] 1.2 Audit all content types handled by `ContentProcessor.process_event()` — document which event types are supported
- [ ] 1.3 Identify gaps: content types present in stream-chunk path but missing from structured-event path
- [ ] 1.4 Wire `EventEmitter` calls into `chat_agent.py` for tool_start, tool_complete, thinking, text, and status events
- [ ] 1.5 Wire `EventEmitter` calls into backend streaming paths where needed
- [ ] 1.6 Verify `events.jsonl` contains complete structured events for a full main-agent run
- [ ] 1.7 Fix `is_filtered_tool` inconsistency (TaskPlanCard bug) — ensure `is_planning_tool` exemption exists in structured-event path

## Phase 2: Unify Rendering Path
- [ ] 2.1 Create in-memory event bus for main agents with same interface as `EventReader`
- [ ] 2.2 Route main TUI through `TimelineEventAdapter.handle_event()` → `ContentProcessor.process_event()`
- [ ] 2.3 Add feature flag to toggle between old (stream-chunk) and new (event-driven) rendering paths
- [ ] 2.4 Run both paths in parallel and diff outputs to verify parity
- [ ] 2.5 Remove `_handle_stream_chunk()` from `TimelineEventAdapter` once parity confirmed
- [ ] 2.6 Remove stream-chunk parsing logic from `ContentProcessor`

## Phase 3: Cleanup & Polish
- [ ] 3.1 Remove dead code from old stream-chunk handling
- [ ] 3.2 Standardize subagent inner-agent tabs to show agent_id + model name
- [ ] 3.3 Add tests validating identical timeline output for shared event sequences
- [ ] 3.4 Document the unified pipeline in `docs/modules/` or design notes
