#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Replay events.jsonl through the TUI pipeline for debugging.

Replays events through the same pipeline as the live TUI, including
agent_id filtering, round-banner dedup, and status filtering.

Two modes:
  Text mode (default) — dumps a transcript of what the TUI renders:
    uv run python scripts/dump_timeline_from_events.py /path/to/events.jsonl [agent_id]

  TUI mode — visual replay with real Textual widgets:
    uv run python scripts/dump_timeline_from_events.py --tui /path/to/events.jsonl [agent_id]

If agent_id is omitted, auto-detects real agents (excludes orchestrator/None).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

from massgen.events import MassGenEvent
from massgen.frontend.displays.timeline_event_recorder import TimelineEventRecorder


def load_events(path: Path) -> list[MassGenEvent]:
    events = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(
                MassGenEvent(
                    timestamp=payload.get("timestamp"),
                    event_type=payload.get("event_type"),
                    agent_id=payload.get("agent_id"),
                    round_number=payload.get("round_number"),
                    data=payload.get("data"),
                ),
            )
    return events


def detect_agent_ids(events: list[MassGenEvent]) -> set[str]:
    """Find real agent IDs (excluding orchestrator/None)."""
    agents: set[str] = set()
    for event in events:
        aid = event.agent_id
        if aid and aid not in ("orchestrator",):
            agents.add(aid)
    return agents


# ─── Text mode ───────────────────────────────────────────────────────────


def run_text(events: list[MassGenEvent], agent_ids: set[str]) -> int:
    agents = sorted(agent_ids)
    multi = len(agents) > 1
    print(f"# Agents: {', '.join(agents)}", file=sys.stderr)

    # Per-agent recorders, mirroring the live TUI's per-agent adapters
    recorders: dict[str, TimelineEventRecorder] = {}
    for aid in agents:

        def make_cb(prefix: str):
            return lambda line: print(f"{prefix} {line}" if multi else line)

        recorders[aid] = TimelineEventRecorder(make_cb(f"[{aid}]"), agent_ids={aid})

    for event in events:
        if event.event_type == "timeline_entry":
            line = (event.data or {}).get("line")
            if line:
                print(line)
            continue
        aid = event.agent_id
        if aid and aid in recorders:
            recorders[aid].handle_event(event)

    for rec in recorders.values():
        rec.flush()
    return 0


# ─── TUI mode ────────────────────────────────────────────────────────────


def run_tui(events: list[MassGenEvent], agent_ids: set[str]) -> int:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Button, Footer, Header, Static

    from massgen.frontend.displays.textual_widgets.content_sections import (
        TimelineSection,
    )
    from massgen.frontend.displays.tui_event_pipeline import TimelineEventAdapter

    agents = sorted(agent_ids)

    class _FakePanel:
        """Minimal panel interface for TimelineEventAdapter."""

        def __init__(self, agent_id: str, timeline: TimelineSection):
            self.agent_id = agent_id
            self._timeline = timeline

        def _get_timeline(self) -> TimelineSection:
            return self._timeline

        def _hide_loading(self) -> None:
            pass

        def start_new_round(self, round_number: int, is_context_reset: bool = False) -> None:
            self._timeline.add_separator(
                f"Round {round_number}",
                round_number=round_number,
            )

    class EventReplayApp(App):
        CSS = """
        Screen { layout: vertical; }
        #tab-bar { height: 3; dock: top; background: $surface; }
        #tab-bar Button { min-width: 20; margin: 0 1; }
        #tab-bar Button.active { background: $accent; }
        #info-bar { height: 1; dock: top; background: $surface-darken-2; color: $text-muted; padding: 0 2; }
        #timeline-container { height: 1fr; }
        TimelineSection { height: 1fr; }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("tab", "next_agent", "Next Agent"),
            ("shift+tab", "prev_agent", "Prev Agent"),
        ]

        def __init__(self):
            super().__init__()
            self._agents = agents
            self._current_idx = 0
            self._timelines: dict[str, TimelineSection] = {}
            self._adapters: dict[str, TimelineEventAdapter] = {}

        def compose(self) -> ComposeResult:
            yield Header()
            with Horizontal(id="tab-bar"):
                for i, aid in enumerate(self._agents):
                    btn = Button(aid, id=f"tab-{aid}", classes="active" if i == 0 else "")
                    yield btn
            yield Static(
                f"{len(events)} events  |  {len(self._agents)} agents",
                id="info-bar",
            )
            with Vertical(id="timeline-container"):
                for aid in self._agents:
                    tl = TimelineSection(id=f"timeline-{aid}")
                    tl.display = aid == self._agents[0]
                    self._timelines[aid] = tl
                    yield tl
            yield Footer()

        def on_mount(self) -> None:
            self.title = "Event Replay"
            # Build per-agent adapters and replay with agent_id filtering
            for aid in self._agents:
                tl = self._timelines[aid]
                panel = _FakePanel(aid, tl)
                adapter = TimelineEventAdapter(panel, agent_id=aid)
                self._adapters[aid] = adapter

                # Replay events, applying same agent_id gate as live TUI
                for event in events:
                    if event.event_type in ("timeline_entry", "stream_chunk"):
                        continue
                    if not event.agent_id or event.agent_id not in agent_ids:
                        continue
                    # Only route to this agent's adapter if event is for this agent
                    if event.agent_id == aid:
                        adapter.handle_event(event)
                adapter.flush()

        def _switch_to(self, idx: int) -> None:
            old_aid = self._agents[self._current_idx]
            self._current_idx = idx % len(self._agents)
            new_aid = self._agents[self._current_idx]
            self._timelines[old_aid].display = False
            self._timelines[new_aid].display = True
            for i, aid in enumerate(self._agents):
                btn = self.query_one(f"#tab-{aid}", Button)
                btn.set_classes("active" if i == self._current_idx else "")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            bid = event.button.id or ""
            if bid.startswith("tab-"):
                aid = bid[4:]
                if aid in self._agents:
                    self._switch_to(self._agents.index(aid))

        def action_next_agent(self) -> None:
            self._switch_to(self._current_idx + 1)

        def action_prev_agent(self) -> None:
            self._switch_to(self._current_idx - 1)

    EventReplayApp().run()
    return 0


# ─── Main ─────────────────────────────────────────────────────────────────


def main() -> int:
    args = sys.argv[1:]
    tui_mode = False

    if "--tui" in args:
        tui_mode = True
        args.remove("--tui")

    if not args:
        print(
            "Usage: dump_timeline_from_events.py [--tui] /path/to/events.jsonl [agent_id]",
            file=sys.stderr,
        )
        return 1

    path = Path(args[0])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    target_agent: Optional[str] = args[1] if len(args) > 1 else None

    events = load_events(path)
    agent_ids = {target_agent} if target_agent else detect_agent_ids(events)

    if not agent_ids:
        print("No agents found in events.", file=sys.stderr)
        return 1

    if tui_mode:
        return run_tui(events, agent_ids)
    else:
        return run_text(events, agent_ids)


if __name__ == "__main__":
    raise SystemExit(main())
