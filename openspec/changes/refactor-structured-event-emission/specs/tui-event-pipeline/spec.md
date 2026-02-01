## ADDED Requirements

### Requirement: Structured Tool Event Emission
The backend SHALL emit `TOOL_START` and `TOOL_COMPLETE` structured events with all metadata (tool_call_id, tool_name, args, result, elapsed_seconds, server_name) for every MCP and custom tool invocation, without relying on string serialization.

#### Scenario: MCP tool call emits structured events
- **WHEN** an MCP tool (e.g., `mcp__filesystem__write_file`) is invoked
- **THEN** a `TOOL_START` event is emitted with tool_call_id, tool_name, args dict, and server_name
- **AND** upon completion, a `TOOL_COMPLETE` event is emitted with tool_call_id, result, elapsed_seconds, and is_error flag

### Requirement: Single Rendering Path for Tool Display
The TUI SHALL consume structured `TOOL_START`/`TOOL_COMPLETE` events directly from the EventEmitter, without parsing emoji-prefixed strings or running dual old/new display paths simultaneously.

#### Scenario: Tool card lifecycle from structured events
- **WHEN** a `TOOL_START` event arrives at the TUI
- **THEN** a tool card is created with the correct tool name, args, and a running timer
- **AND** when the matching `TOOL_COMPLETE` event arrives, the timer stops and the result is displayed

#### Scenario: No duplicate text events for tool content
- **WHEN** `coordination_ui._emit_agent_content()` processes content containing tool markers
- **THEN** it SHALL NOT emit a duplicate `text` event for that content

### Requirement: No String-Based Tool Detection in Display Hot Path
The TUI display pipeline SHALL NOT use `ContentNormalizer.detect_tool_event()` or emoji pattern matching to classify tool content during live rendering. String-based detection MAY be retained for log replay of older event formats.

#### Scenario: Tool card created without string parsing
- **WHEN** a structured `TOOL_START` event is processed by `ContentProcessor.process_event()`
- **THEN** the tool_name, tool_call_id, and args are read directly from the event data fields
- **AND** `ContentNormalizer.detect_tool_event()` is NOT invoked

### Requirement: STREAM_CHUNK Event Type Removal
The system SHALL NOT use `STREAM_CHUNK` as an event type. All content previously carried as stream chunks SHALL be emitted as typed structured events (`TOOL_START`, `TOOL_COMPLETE`, `TEXT`, `THINKING`, `STATUS`, `FINAL_ANSWER`).

**Status: DONE** — `STREAM_CHUNK` removed from `EventType` enum, `emit_stream_chunk()` deleted, all code uses string literal `"stream_chunk"` for old log backward compat.

#### Scenario: No STREAM_CHUNK events in events.jsonl
- **WHEN** a full MassGen run completes
- **THEN** the `events.jsonl` file SHALL contain zero events with `event_type: "stream_chunk"`
- **AND** all content is represented by typed structured events

#### Scenario: STREAM_CHUNK removed from EventType enum
- **WHEN** code references `EventType.STREAM_CHUNK`
- **THEN** it SHALL fail at import/compile time because the constant no longer exists

#### Scenario: Old log files with stream_chunk events
- **WHEN** replaying an `events.jsonl` containing `"stream_chunk"` events from a pre-refactor run
- **THEN** the system SHALL skip them gracefully via string comparison (not enum)

### Requirement: Agent Output File Writing Without Buffer Path
The system SHALL continue writing agent output content to log files (`agent_outputs/agent_N.txt`) after the old buffer/flush path is removed. A lightweight write path SHALL exist that is independent of the TUI rendering pipeline.

#### Scenario: Agent output log contains all content
- **WHEN** a full MassGen run completes
- **THEN** the `agent_outputs/agent_1.txt` file SHALL contain all tool invocations, thinking content, and text output for that agent
- **AND** this writing SHALL NOT depend on `update_agent_content()` or the buffer/flush pipeline

### Requirement: Event Ordering for Tool Batch Tracking
The `ToolBatchTracker` SHALL receive structured events in chronological order so that consecutive MCP tools from the same server are batched correctly, and non-tool content between tools breaks the batch.

#### Scenario: Text between tools breaks batch
- **WHEN** a `TOOL_COMPLETE` event arrives, followed by a `TEXT` event, followed by a `TOOL_START` event
- **THEN** the second tool SHALL NOT be batched with the first tool
- **AND** each tool appears as a separate card

#### Scenario: Consecutive tools from same server are batched
- **WHEN** two `TOOL_START` events arrive consecutively from the same MCP server with no intervening `TEXT`/`THINKING`/`STATUS` events
- **THEN** they SHALL be displayed in a single batch card

### Requirement: Subagent Log Replay Compatibility
Subagent event replay from `events.jsonl` SHALL work with both old-format logs (containing `STREAM_CHUNK` events) and new-format logs (containing only typed structured events). The system SHALL gracefully handle either format.

#### Scenario: Replay old-format subagent log
- **WHEN** a subagent `events.jsonl` contains `STREAM_CHUNK` events from a pre-refactor run
- **THEN** the replay system SHALL still render tool cards, thinking, and text content correctly
- **AND** no errors are raised due to the presence of `STREAM_CHUNK` events

#### Scenario: Replay new-format subagent log
- **WHEN** a subagent `events.jsonl` contains only typed structured events
- **THEN** the replay system SHALL render all content correctly using `process_event()` directly

### Requirement: Event Pipeline Thread Batching
The TUI event pipeline SHALL batch events from backend threads before marshaling to the Textual main thread, to reduce per-token `call_from_thread()` overhead.

**Status: DONE** — Events accumulate in a thread-safe deque for ~16ms before a single `call_from_thread()` dispatches the batch.

#### Scenario: High-frequency token events are batched
- **WHEN** multiple structured events arrive within a 16ms window from backend threads
- **THEN** they SHALL be delivered to the Textual main thread in a single `call_from_thread()` call
- **AND** each event is routed to the correct agent's `TimelineEventAdapter` in order

### Requirement: Single Emission Point for Buffered Content
Content that flows through the `update_agent_content()` → buffer/flush → `_emit_agent_content()` path SHALL only be emitted as structured events from `_emit_agent_content()`. Upstream chunk handlers (reasoning, tool status, compression) SHALL NOT add duplicate `emit_*()` calls for the same content.

**Status: DONE** — Learned via dual-emission bugs (double thinking blocks, raw tool text duplicating tool cards).

#### Scenario: Reasoning content emitted once
- **WHEN** reasoning content arrives as a chunk and flows through `update_agent_content()` to `_emit_agent_content()`
- **THEN** exactly one `THINKING` event SHALL be emitted (from `_emit_agent_content`)
- **AND** the upstream reasoning chunk handler SHALL NOT emit a separate `THINKING` event

#### Scenario: Tool status chunks not emitted as status events
- **WHEN** `mcp_status` or `custom_tool_status` chunks arrive in the coordination stream
- **THEN** they SHALL NOT be emitted as `STATUS` events
- **AND** tool display SHALL rely exclusively on `TOOL_START`/`TOOL_COMPLETE` events from the backend
