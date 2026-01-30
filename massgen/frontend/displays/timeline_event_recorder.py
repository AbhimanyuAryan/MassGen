# -*- coding: utf-8 -*-
"""Timeline event recorder for events.jsonl parity debugging."""

from __future__ import annotations

from typing import Callable, Optional

from massgen.events import EventType, MassGenEvent

from .content_processor import ContentOutput, ContentProcessor
from .timeline_transcript import format_text, render_output


class TimelineEventRecorder:
    """Record timeline transcript lines from MassGen events.

    Mirrors TimelineEventAdapter parsing (including line buffering) so the
    resulting transcript lines match what the TUI would render.
    """

    def __init__(self, line_callback: Callable[[str], None]) -> None:
        self._processor = ContentProcessor()
        self._round_number = 1
        self._line_callback = line_callback

    def reset(self) -> None:
        """Reset internal state for a fresh event stream."""
        self._processor.reset()
        self._round_number = 1

    def handle_event(self, event: MassGenEvent) -> None:
        """Process a single event and emit any resulting transcript lines."""
        if event.event_type == "timeline_entry":
            return
        if event.event_type == EventType.STREAM_CHUNK:
            self._handle_stream_chunk(event)
            return

        output = self._processor.process_event(event, self._round_number)
        self._record_output(output)

    def flush(self) -> None:
        """Flush buffered text or pending tool batches."""
        self._record_output(self._processor.flush_line_buffer(self._round_number))
        self._record_output(self._processor.flush_pending_batch(self._round_number))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_output(self, output: Optional[ContentOutput] | list[ContentOutput] | None) -> None:
        if output is None:
            return
        outputs = output if isinstance(output, list) else [output]
        for item in outputs:
            if item is None or item.output_type == "skip":
                continue
            if item.output_type == "separator" and item.round_number:
                self._round_number = item.round_number
            for line in render_output(item):
                self._line_callback(line)

    def _write_line(self, text: str, _style: str, text_class: str, round_number: int) -> None:
        self._line_callback(format_text(text, text_class, round_number))

    def _handle_stream_chunk(self, event: MassGenEvent) -> None:
        data = event.data or {}
        chunk = data.get("chunk")
        if isinstance(chunk, dict):
            chunk_dict = chunk
        elif isinstance(data, dict):
            chunk_dict = data
        else:
            return

        chunk_type = (chunk_dict.get("type") or "").lower()
        content = chunk_dict.get("content")
        status = chunk_dict.get("status")
        tool_call_id = chunk_dict.get("tool_call_id")

        if chunk_type == "done":
            self.flush()
            return

        # Skip non-display chunks, but still allow tool calls/outputs
        if not chunk_dict.get("display", True):
            if chunk_type != "tool_calls" and not (status == "function_call_output" and tool_call_id):
                return

        if chunk_type == "tool_calls" or (status == "function_call_output" and tool_call_id):
            output = self._processor.process_event(event, self._round_number)
            self._record_output(output)
            return

        raw_type = self._map_chunk_type(chunk_type)
        if raw_type is None or content is None:
            return

        output, _ = self._processor.process_line_buffered(
            str(content),
            raw_type,
            tool_call_id,
            self._round_number,
            write_callback=self._write_line,
        )
        self._record_output(output)

    def _map_chunk_type(self, chunk_type: str) -> Optional[str]:
        if not chunk_type:
            return None
        if chunk_type in ("mcp_status", "custom_tool_status", "tool"):
            return "tool"
        if "mcp_status" in chunk_type or "custom_tool_status" in chunk_type:
            return "tool"
        if chunk_type in (
            "reasoning",
            "reasoning_done",
            "reasoning_summary",
            "reasoning_summary_done",
            "thinking",
        ):
            return "thinking"
        if chunk_type in ("content", "text"):
            return "content"
        if chunk_type in ("status", "system_status", "backend_status", "agent_status", "compression_status", "error"):
            return "status"
        if chunk_type in ("presentation", "final_answer"):
            return "presentation"
        return None
