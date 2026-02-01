# Phase 1 Audit: Structured Event Emission

## Task 1.1: `update_agent_content()` call sites with tool content

All in `massgen/coordination_ui.py`:

| Pattern | Lines | content_type | Structured data available | What's lost |
|---------|-------|-------------|--------------------------|-------------|
| MCP/Custom tool status chunks | 395-400, 1003-1008, 1511-1516 | `"tool"` | `chunk.tool_call_id` passed as kwarg; `chunk.status`, `chunk.source` available | tool_name embedded in content string; status/source discarded |
| Compression status | 411, 1019, 1527 | `"tool"` | None | Plain string, no tool_call_id |
| Workspace actions | 1980, 2142, 2155 | `"tool"` | `action_type`, `params` parsed from JSON | Flattened to `"🔧 Calling workspace/{action_type} {params}"` |
| `_emit_agent_content` tool routing | 2040 | `"tool"` | Only `agent_id` + content string | No tool_call_id, no tool_name, no structured args |

## Task 1.2: `emit_text()`/`emit_thinking()`/`emit_status()` call sites

Centralized in `coordination_ui.py` `_emit_agent_content()` (lines 2010-2057):

| Method | Line | Duplicates stream chunks? |
|--------|------|--------------------------|
| `emit_thinking()` | 2030 | YES — reasoning content already sent via `update_agent_content` |
| `emit_text()` | 2032 | YES — text content already sent via `update_agent_content` |
| `emit_text()` | 2036 | YES — presentation/final_answer content |
| `emit_status()` | 2034 | YES — status content |
| `emit_status()` | 355 | Partial — `agent_status` chunks go to `update_agent_status()` not `update_agent_content()` |
| `emit_status()` | orchestrator.py:3042, 7253 | NO — unique orchestrator-level events |

Tool content is **excluded** from emit calls (line 2028: `if not is_tool_content`) but still goes to `update_agent_content`. So tool content has NO structured event emitted from this path — it only reaches the TUI via the buffer/flush pipeline.

## Task 1.3: Backend tool event emission audit

**File**: `massgen/backend/base_with_custom_tool_and_mcp.py`

### emit_tool_start (line ~1563)
- Fields: `tool_id`, `tool_name`, `args` (dict), `server_name`, `agent_id`
- **Complete** — all needed metadata present.

### emit_tool_complete
- Lines: ~1708 (MCP failure), ~1945 (success), ~2021 (exception)
- Fields: `tool_id`, `tool_name`, `result`, `elapsed_seconds`, `status`, `is_error`, `agent_id`
- **Complete** — all needed metadata present.

### Do events reach the TUI?

Only when `_use_event_pipeline=True` (off by default). Gate at `textual_terminal_display.py:3152`. TOOL_START/TOOL_COMPLETE are **not** type-filtered — they pass through when the gate is open. Processing in `content_processor.py:508-668` correctly handles both event types with full metadata.

**Key finding**: The backend already emits complete structured tool events. They just don't reach the TUI for main agents because the event pipeline gate is off by default.

## Task 1.4: Full MCP tool call data flow trace

### Path: Backend → coordination_ui → display → TUI

1. **Backend** (`base_with_custom_tool_and_mcp.py:1467-1578`):
   - Has: `tool_name`, `call_id`, `args_dict`, `tool_type`, `source_prefix`
   - Yields `StreamChunk` with `tool_call_id` as field but `tool_name` only embedded in `content`/`source` strings
   - Also calls `emit_tool_start`/`emit_tool_complete` with full structured data

2. **coordination_ui** (`coordination_ui.py:395-400`):
   - Receives StreamChunk
   - Passes `tool_call_id` to display via kwargs
   - **Discards** `chunk.status` and `chunk.source` (which contained tool_name prefix)

3. **_emit_agent_content** (`coordination_ui.py:2018-2040`):
   - Detects tool content via emoji string matching (`"🔧"`, `"✅"`, `"❌"`)
   - Calls `update_agent_content` with `"tool"` type but **no tool_call_id**
   - Skips `emit_text`/`emit_thinking` for tool content (line 2028)

4. **Buffer/flush** (`textual_terminal_display.py:778-3683`):
   - Preserves `tool_call_id` through buffer → flush → `update_agent_widget` → `adapter.handle_stream_content`

5. **TimelineEventAdapter** (`tui_event_pipeline.py:62-85`):
   - Wraps content into `STREAM_CHUNK` event
   - Routes to `process_line_buffered`

6. **ContentNormalizer.detect_tool_event** (`content_normalizer.py:297-348`):
   - Re-parses string via regex (`TOOL_START_PATTERNS`, `TOOL_COMPLETE_PATTERNS`) to extract tool_name
   - Attaches `tool_call_id` if available from kwargs

### Where metadata is lost

| Stage | What's lost | Why |
|-------|------------|-----|
| `StreamChunk` (base.py:37-67) | `tool_name`, `tool_type` | No fields for these on the dataclass |
| `coordination_ui` (line 395-400) | `chunk.status`, `chunk.source` | Passed to display but not forwarded |
| `_emit_agent_content` (line 2040) | `tool_call_id` | Never passed to update_agent_content from this path |
| `ContentNormalizer` (line 297-348) | Accuracy | Reconstructs tool_name via fragile regex from display strings |

### Key Finding: Dual-path duplication

`_use_event_pipeline` defaults to `True` (line 534), so the structured event path is **already active**. Both paths run simultaneously:

1. **Structured path**: `_handle_event_from_emitter` → `adapter.handle_event()` → `process_event()` handles `TOOL_START`/`TOOL_COMPLETE` with full metadata
2. **Buffer/flush path**: `update_agent_widget` → `adapter.handle_stream_content()` → wraps as `STREAM_CHUNK` → `_handle_stream_chunk()` → string-parses tool content via regex

Both feed into the **same** `TimelineEventAdapter` per agent, creating duplicate tool cards.

### Key Finding: claude_code backend missing structured events

The `claude_code` backend (`claude_code.py`) handles tools via SDK `ToolUseBlock`/`ToolResultBlock` objects — it does NOT use `_execute_tool_with_logging` from the base class. It was missing `emit_tool_start`/`emit_tool_complete` calls entirely. Fixed by adding structured event emission alongside the existing emoji StreamChunk yields, with `_tool_start_times` dict for elapsed_seconds tracking.

### Resolution: Dual-path gating

Rather than removing the old path immediately, both paths are now **mutually exclusive**:
- `update_agent_widget()` has two gates:
  1. `content_type == "tool"` — catches mcp_status/custom_tool_status chunks from standard backends
  2. Emoji-pattern check when `_use_event_pipeline=True` — catches tool content from claude_code and any backend that yields tool emoji as `type="content"`
- When `_use_event_pipeline=False`, the old STREAM_CHUNK path works as before
- Phase 4 will remove the old path entirely once structured events are validated
