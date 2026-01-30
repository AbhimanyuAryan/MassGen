# -*- coding: utf-8 -*-
"""Event stream abstraction for subprocess displays.

Provides a unified interface for delivering events from subprocess executions
to TUI components. Supports both polling-based (current) and streaming-based
(future) event delivery mechanisms.

Architecture:
- EventStream: Abstract base class defining event delivery interface
- PollingEventStream: File-based polling implementation using EventReader
- StreamingEventStream: Real-time streaming (future enhancement)

This abstraction consolidates the polling logic previously duplicated across:
- SubagentCard (manual tool extraction from events.jsonl)
- SubagentTuiModal (ContentProcessor-based polling)
- SubagentScreen (TimelineEventAdapter-based polling)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional

from massgen.events import EventReader, MassGenEvent


class EventStream(ABC):
    """Abstract interface for event delivery.

    Subclasses implement different delivery mechanisms (polling, streaming)
    but provide a consistent callback-based interface for event consumers.
    """

    @abstractmethod
    def start(self, callback: Callable[[MassGenEvent], None]) -> None:
        """Start delivering events to the callback.

        Args:
            callback: Function to call for each event. Should accept a MassGenEvent.
        """

    @abstractmethod
    def stop(self) -> None:
        """Stop event delivery and cleanup resources."""

    @abstractmethod
    def is_running(self) -> bool:
        """Check if event delivery is currently active.

        Returns:
            True if events are being delivered, False otherwise.
        """


class PollingEventStream(EventStream):
    """File-based polling implementation for event delivery.

    Polls events.jsonl file at regular intervals and delivers new events
    to the callback. This is the current implementation used across all
    subprocess displays.

    Attributes:
        events_path: Path to events.jsonl file to poll
        poll_interval: Polling interval in seconds (default 0.5s)
        agent_filter: Optional agent ID to filter events (for inner agents)
    """

    def __init__(
        self,
        events_path: Path,
        poll_interval: float = 0.5,
        agent_filter: Optional[str] = None,
    ):
        """Initialize polling event stream.

        Args:
            events_path: Path to events.jsonl file
            poll_interval: How often to poll for new events (seconds)
            agent_filter: Optional agent ID to filter by
        """
        self.events_path = events_path
        self.poll_interval = poll_interval
        self.agent_filter = agent_filter
        self._callback: Optional[Callable[[MassGenEvent], None]] = None
        self._reader: Optional[EventReader] = None
        self._timer = None
        self._running = False

    def start(self, callback: Callable[[MassGenEvent], None]) -> None:
        """Start polling and delivering events.

        Args:
            callback: Function to call for each new event
        """
        if self._running:
            return

        self._callback = callback
        self._reader = EventReader(self.events_path)
        self._running = True

        # Initial load of all existing events
        if self._reader.exists():
            events = self._reader.read_all()
            for event in events:
                if self._should_include_event(event):
                    self._callback(event)

    def stop(self) -> None:
        """Stop polling."""
        self._running = False
        if self._timer:
            try:
                self._timer.cancel()
            except Exception:
                pass
            self._timer = None
        self._reader = None
        self._callback = None

    def is_running(self) -> bool:
        """Check if polling is active."""
        return self._running

    def poll_once(self) -> None:
        """Poll for new events once and deliver via callback.

        This is meant to be called by a timer or event loop.
        """
        if not self._running or not self._reader or not self._callback:
            return

        # Get new events since last poll
        new_events = self._reader.get_new_events()
        for event in new_events:
            if self._should_include_event(event):
                self._callback(event)

    def _should_include_event(self, event: MassGenEvent) -> bool:
        """Check if event should be included based on filter.

        Args:
            event: Event to check

        Returns:
            True if event matches filter, False otherwise
        """
        if not self.agent_filter:
            return True
        return event.agent_id == self.agent_filter


class StreamingEventStream(EventStream):
    """Real-time streaming from subprocess stdout.

    Future enhancement to support real-time event delivery without
    file polling. Would read events directly from subprocess.stdout
    and deliver immediately.

    This is a placeholder for future implementation.
    """

    def __init__(self, process):
        """Initialize streaming event delivery.

        Args:
            process: Subprocess with stdout producing JSONL events
        """
        self.process = process
        self._running = False
        # TODO: Implement streaming infrastructure

    def start(self, callback: Callable[[MassGenEvent], None]) -> None:
        """Start streaming events from subprocess stdout.

        Args:
            callback: Function to call for each event
        """
        # TODO: Implement background thread reading from process.stdout
        raise NotImplementedError("Streaming event delivery not yet implemented")

    def stop(self) -> None:
        """Stop streaming."""
        self._running = False

    def is_running(self) -> bool:
        """Check if streaming is active."""
        return self._running
