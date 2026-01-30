# -*- coding: utf-8 -*-
"""Unified controller for subprocess display rendering.

Consolidates event reading, status tracking, and timeline updates from:
- SubagentCard (518 lines) - Manual tool extraction, custom JSON parsing
- SubagentTuiModal (846 lines) - ContentProcessor parsing, dormant streaming
- SubagentScreen (1045 lines) - TimelineEventAdapter, most sophisticated

This controller provides a single implementation that can be used by all three
subprocess display components, eliminating ~800 lines of duplication.

Architecture:
- SubprocessDisplayController: Main controller class
- StatusInfo: Formatted status information dataclass
- Uses PollingEventStream for event delivery
- Uses TimelineEventAdapter for timeline rendering (if panel provided)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from rich.text import Text

from massgen.events import EventReader, MassGenEvent
from massgen.subagent.models import SubagentDisplayData

from .event_stream import PollingEventStream
from .status_registry import format_elapsed_time, get_status_icon_and_color


@dataclass
class StatusInfo:
    """Formatted status information for display."""

    status: str
    icon: str
    color: str
    elapsed_seconds: float
    round_number: int
    tool_count: int

    def format_elapsed(self) -> str:
        """Format elapsed time as human-readable string.

        Returns:
            Formatted time (e.g., "45s", "2m15s", "1h5m")
        """
        return format_elapsed_time(self.elapsed_seconds)

    def format_ribbon_text(self) -> Text:
        """Format status ribbon text with icon and color.

        Returns:
            Rich Text object with formatted status
        """
        text = Text()
        text.append(f" {self.icon} ", style=f"bold {self.color}")
        text.append(self.status.capitalize())
        elapsed_str = self.format_elapsed()
        if elapsed_str:
            text.append(f" | {elapsed_str}")
        if self.round_number > 0:
            text.append(f" | Round {self.round_number}")
        return text


class SubprocessDisplayController:
    """Unified controller for subprocess display rendering.

    Manages event reading, status tracking, and timeline updates for all
    subprocess display components (Card, Modal, Screen).

    Attributes:
        subagent: Subprocess metadata
        panel: Optional panel with timeline (for Modal/Screen)
        poll_interval: Event polling interval in seconds
    """

    def __init__(
        self,
        subagent: SubagentDisplayData,
        panel: Optional[Any] = None,
        poll_interval: float = 0.5,
    ):
        """Initialize subprocess display controller.

        Args:
            subagent: Subprocess metadata with workspace path, status, etc.
            panel: Optional panel with timeline (None for SubagentCard)
            poll_interval: How often to poll for new events (seconds)
        """
        self.subagent = subagent
        self.panel = panel
        self.poll_interval = poll_interval

        # Event delivery
        self._event_stream: Optional[PollingEventStream] = None
        self._event_reader: Optional[EventReader] = None

        # Timeline integration (if panel provided)
        self._event_adapter: Optional[Any] = None  # TimelineEventAdapter

        # Status tracking
        self._status = subagent.status
        self._elapsed_seconds = subagent.elapsed_seconds
        self._round_number = 0
        self._tool_count = 0

        # Inner agent support (for nested subprocesses)
        self._inner_agents: List[str] = []
        self._tool_call_agent_map: Dict[str, str] = {}
        self._current_agent_filter: Optional[str] = None

    def initialize(self, events_path: Path) -> None:
        """Initialize event reader and load existing events.

        Args:
            events_path: Path to events.jsonl file
        """
        # Create event reader
        self._event_reader = EventReader(events_path)

        # Initialize timeline adapter if panel provided
        if self.panel:
            from massgen.frontend.displays.tui_event_pipeline import (
                TimelineEventAdapter,
            )

            self._event_adapter = TimelineEventAdapter(
                panel=self.panel,
                agent_id=self.subagent.id,
            )

        # Create polling stream
        self._event_stream = PollingEventStream(
            events_path=events_path,
            poll_interval=self.poll_interval,
            agent_filter=self._current_agent_filter,
        )

    def start_polling(self) -> None:
        """Start polling for new events.

        Only polls if status is running or pending. Completed/failed
        subprocesses don't need ongoing polling.
        """
        if not self._event_stream:
            return

        # Only poll if still active
        if self.subagent.status not in ("running", "pending"):
            return

        # Start event delivery with callback
        self._event_stream.start(callback=self._handle_event)

    def stop_polling(self) -> None:
        """Stop polling for events."""
        if self._event_stream:
            self._event_stream.stop()

    def poll_once(self) -> None:
        """Poll for new events once.

        This should be called by a timer in the TUI component.
        """
        if self._event_stream and self._event_stream.is_running():
            self._event_stream.poll_once()

        # Update status from subagent metadata
        self._update_status_from_metadata()

    def _handle_event(self, event: MassGenEvent) -> None:
        """Handle a single event.

        Args:
            event: Event to process
        """
        # Route to timeline adapter if available
        if self._event_adapter:
            self._event_adapter.handle_event(event)

        # Track metrics
        if event.event_type == "tool_start":
            self._tool_count += 1

        if event.round_number > 0:
            self._round_number = event.round_number

    def _update_status_from_metadata(self) -> None:
        """Update status tracking from subagent metadata.

        This refreshes status, elapsed time from the live SubagentDisplayData.
        """
        self._status = self.subagent.status
        self._elapsed_seconds = self.subagent.elapsed_seconds

    def get_status_info(self) -> StatusInfo:
        """Get current status information.

        Returns:
            StatusInfo with formatted status data
        """
        icon, color = get_status_icon_and_color(self._status)

        return StatusInfo(
            status=self._status,
            icon=icon,
            color=color,
            elapsed_seconds=self._elapsed_seconds,
            round_number=self._round_number,
            tool_count=self._tool_count,
        )

    def detect_inner_agents(self) -> Tuple[List[str], Dict[str, str]]:
        """Detect inner agents from execution metadata.

        Reads execution_metadata.yaml to find nested subagent spawns.

        Returns:
            Tuple of (agent_ids, tool_call_agent_map)
        """
        if not self.subagent.workspace_path:
            return [], {}

        metadata_path = Path(self.subagent.workspace_path) / "execution_metadata.yaml"
        if not metadata_path.exists():
            return [], {}

        try:
            with open(metadata_path, "r") as f:
                metadata = yaml.safe_load(f)

            agents_config = metadata.get("agents", [])
            agent_ids = [agent.get("id", "") for agent in agents_config if agent.get("id")]

            # Build tool call mapping (tool_call_id -> agent_id)
            tool_call_agent_map = {}
            # TODO: Extract from event data if needed

            self._inner_agents = agent_ids
            self._tool_call_agent_map = tool_call_agent_map

            return agent_ids, tool_call_agent_map

        except Exception:
            return [], {}

    def switch_agent(self, agent_id: Optional[str]) -> None:
        """Switch to viewing a specific inner agent.

        Args:
            agent_id: Agent ID to filter by (None for no filter)
        """
        self._current_agent_filter = agent_id

        # Update event stream filter
        if self._event_stream:
            self._event_stream.agent_filter = agent_id

        # Reset timeline and reload events with new filter
        if self._event_adapter and self._event_reader:
            # Clear timeline
            # NOTE: Actual timeline clearing depends on panel implementation
            # This is a placeholder for the interface

            # Reload all events with new filter
            if self._event_reader.exists():
                self._event_reader._last_position = 0  # Reset position
                events = self._event_reader.read_all()
                for event in events:
                    if not agent_id or event.agent_id == agent_id:
                        self._event_adapter.handle_event(event)

    def get_tool_summary(self) -> List[Dict[str, Any]]:
        """Get summary of tool calls from events.

        Returns:
            List of tool call summaries with name, status, args
        """
        if not self._event_reader or not self._event_reader.exists():
            return []

        events = self._event_reader.read_all()

        tool_starts = {}
        for event in events:
            if event.event_type == "tool_start":
                tool_id = event.data.get("tool_call_id", "")
                tool_starts[tool_id] = {
                    "name": event.data.get("tool_name", "unknown"),
                    "args": event.data.get("arguments", ""),
                    "status": "running",
                }
            elif event.event_type == "tool_complete":
                tool_id = event.data.get("tool_call_id", "")
                if tool_id in tool_starts:
                    tool_starts[tool_id]["status"] = "success"
                    tool_starts[tool_id]["result"] = event.data.get("result", "")

        return list(tool_starts.values())
