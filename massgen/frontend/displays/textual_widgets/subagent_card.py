# -*- coding: utf-8 -*-
"""
Subagent Card Widget for MassGen TUI.

Horizontal overview for spawned subagents with per-agent columns.
Shows a compact summary line and recent tool context for each subagent,
and opens the subagent view on click.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.message import Message
from textual.timer import Timer
from textual.widgets import Static

from massgen.frontend.displays.content_handlers import format_tool_display_name
from massgen.subagent.models import SubagentDisplayData, SubagentResult


@dataclass
class _ToolCache:
    path: Optional[Path]
    size: int
    tools: List[str]


@dataclass
class _PlanCache:
    path: Optional[Path]
    mtime: float
    summary: Optional[str]


class SubagentColumn(Vertical):
    """Single subagent column inside the overview card."""

    DEFAULT_CSS = """
    SubagentColumn {
        width: 1fr;
        min-width: 28;
        height: auto;
        padding: 0 1;
        border-right: solid #30363d;
    }

    SubagentColumn:last-of-type {
        border-right: none;
        margin-right: 0;
    }

    SubagentColumn .agent-header {
        text-style: bold;
    }

    SubagentColumn .summary-line {
        color: #8b949e;
    }

    SubagentColumn .tool-current {
        color: #a371f7;
        text-style: bold;
    }

    SubagentColumn .tool-recent {
        color: #6e7681;
    }
    """

    def __init__(
        self,
        subagent: SubagentDisplayData,
        all_subagents: List[SubagentDisplayData],
        summary: str,
        tools: List[str],
        open_callback: Callable[[SubagentDisplayData, List[SubagentDisplayData]], None],
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._subagent = subagent
        self._all_subagents = all_subagents
        self._summary = summary
        self._tools = tools
        self._open_callback = open_callback

    def compose(self) -> ComposeResult:
        yield Static("", classes="agent-header", id="agent_header")
        yield Static("", classes="summary-line", id="summary_line")
        yield Static("", classes="tool-current", id="tool_current")
        yield Static("", classes="tool-recent", id="tool_recent_1")
        yield Static("", classes="tool-recent", id="tool_recent_2")

    def on_mount(self) -> None:
        self._update_display()

    def on_click(self) -> None:
        self._open_callback(self._subagent, self._all_subagents)

    def update_content(self, subagent: SubagentDisplayData, summary: str, tools: List[str]) -> None:
        self._subagent = subagent
        self._summary = summary
        self._tools = tools
        self._update_display()

    def _update_display(self) -> None:
        header = self._build_header()
        summary = self._summary or ""
        current_tool, recent_tools = self._split_tools(self._tools)

        try:
            self.query_one("#agent_header", Static).update(header)
            self.query_one("#summary_line", Static).update(summary)
            self.query_one("#tool_current", Static).update(current_tool)
            self.query_one("#tool_recent_1", Static).update(recent_tools[0] if recent_tools else "")
            self.query_one("#tool_recent_2", Static).update(recent_tools[1] if len(recent_tools) > 1 else "")
        except Exception:
            pass

    def _build_header(self) -> Text:
        text = Text()
        icon, style = SubagentCard.status_icon_and_style(self._subagent.status)
        label = self._truncate(self._subagent.id, 24)
        text.append(f"{icon} ", style=style)
        text.append(label, style=style)
        return text

    def _split_tools(self, tools: List[str]) -> Tuple[str, List[str]]:
        if not tools:
            return "idle", []
        current = tools[0]
        recent = tools[1:3]
        return current, recent

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."


class SubagentCard(Vertical, can_focus=True):
    """Overview card displaying spawned subagents with per-agent columns."""

    BINDINGS = [
        ("enter", "open_selected", "Open"),
    ]

    class OpenModal(Message):
        """Message posted when user clicks to open subagent view."""

        def __init__(self, subagent: SubagentDisplayData, all_subagents: List[SubagentDisplayData]) -> None:
            self.subagent = subagent
            self.all_subagents = all_subagents
            super().__init__()

    DEFAULT_CSS = """
    SubagentCard {
        width: 100%;
        height: auto;
        min-height: 6;
        padding: 1 1;
        margin: 0 0 1 1;
        background: #1a1f2e;
        border-left: thick #7c3aed;
    }

    SubagentCard:hover {
        background: #1e2436;
    }

    SubagentCard #subagent-scroll {
        width: 100%;
        height: auto;
        max-height: 8;
        overflow-x: auto;
        overflow-y: hidden;
    }

    SubagentCard #subagent-columns {
        layout: horizontal;
        height: auto;
        width: 100%;
    }
    """

    STATUS_ICONS = {
        "completed": "✓",
        "running": "●",
        "pending": "○",
        "error": "✗",
        "timeout": "⏱",
        "failed": "✗",
    }

    STATUS_STYLES = {
        "completed": "#7ee787",
        "running": "bold #a371f7",
        "pending": "#6e7681",
        "error": "#f85149",
        "timeout": "#d29922",
        "failed": "#f85149",
    }

    POLL_INTERVAL = 0.5

    _IGNORED_TOOL_NAMES = {
        "new_answer",
        "final_answer",
    }

    def __init__(
        self,
        subagents: Optional[List[SubagentDisplayData]] = None,
        tool_call_id: Optional[str] = None,
        status_callback: Optional[Callable[[str], Optional[SubagentDisplayData]]] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(id=id)
        self._subagents = subagents or []
        self._tool_call_id = tool_call_id
        self._status_callback = status_callback
        self._poll_timer: Optional[Timer] = None
        self._tool_cache: Dict[str, _ToolCache] = {}
        self._plan_cache: Dict[str, _PlanCache] = {}
        self._columns: Dict[str, SubagentColumn] = {}
        self._selected_index = 0

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="subagent-scroll"):
            with Horizontal(id="subagent-columns"):
                for sa in self._subagents:
                    summary = self._get_summary_line(sa)
                    tools = self._get_tool_lines(sa)
                    column = SubagentColumn(
                        subagent=sa,
                        all_subagents=self._subagents,
                        summary=summary,
                        tools=tools,
                        open_callback=self._request_open,
                        id=f"subagent_col_{sa.id}",
                    )
                    self._columns[sa.id] = column
                    yield column

    def on_mount(self) -> None:
        self._start_polling_if_needed()

    def on_unmount(self) -> None:
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None

    def _request_open(self, subagent: SubagentDisplayData, all_subagents: List[SubagentDisplayData]) -> None:
        try:
            self._selected_index = self._subagents.index(subagent)
        except ValueError:
            pass
        self.post_message(self.OpenModal(subagent, all_subagents))

    def _start_polling_if_needed(self) -> None:
        if self._poll_timer is not None:
            return
        if any(sa.status in ("running", "pending") for sa in self._subagents):
            self._poll_timer = self.set_interval(self.POLL_INTERVAL, self._poll_status)

    def _poll_status(self) -> None:
        updated = False
        new_subagents: List[SubagentDisplayData] = []

        if self._status_callback:
            for sa in self._subagents:
                if sa.status in ("running", "pending"):
                    new_data = self._status_callback(sa.id)
                    if new_data:
                        new_subagents.append(new_data)
                        updated = True
                    else:
                        new_subagents.append(sa)
                else:
                    new_subagents.append(sa)
            if updated:
                self._subagents = new_subagents

        # Always refresh tool lines for running subagents
        if any(sa.status in ("running", "pending") for sa in self._subagents):
            self._refresh_columns()
        else:
            if self._poll_timer:
                self._poll_timer.stop()
                self._poll_timer = None

    def _refresh_columns(self) -> None:
        try:
            columns_container = self.query_one("#subagent-columns", Horizontal)
        except Exception:
            return

        if len(self._columns) != len(self._subagents) or any(sa.id not in self._columns for sa in self._subagents):
            columns_container.remove_children()
            self._columns = {}
            for sa in self._subagents:
                summary = self._get_summary_line(sa)
                tools = self._get_tool_lines(sa)
                column = SubagentColumn(
                    subagent=sa,
                    all_subagents=self._subagents,
                    summary=summary,
                    tools=tools,
                    open_callback=self._request_open,
                    id=f"subagent_col_{sa.id}",
                )
                self._columns[sa.id] = column
                columns_container.mount(column)
            return

        for sa in self._subagents:
            column = self._columns.get(sa.id)
            if column:
                summary = self._get_summary_line(sa)
                tools = self._get_tool_lines(sa)
                column.update_content(sa, summary, tools)

    def _get_summary_line(self, sa: SubagentDisplayData) -> str:
        # If completed, show final answer preview
        if sa.status == "completed" and sa.answer_preview:
            # Truncate answer to fit in summary line
            answer = sa.answer_preview.strip()
            if len(answer) > 50:
                answer = answer[:47] + "..."
            return f"✓ {answer}"

        plan_summary = self._get_plan_summary(sa)
        if plan_summary:
            return plan_summary

        status_label = sa.status
        if status_label == "completed":
            status_label = "done"
        elif status_label == "failed":
            status_label = "failed"
        elif status_label == "timeout":
            status_label = "timeout"

        elapsed = int(sa.elapsed_seconds)
        if elapsed <= 0:
            return status_label
        if elapsed >= 60:
            elapsed_str = f"{elapsed // 60}m"
        else:
            elapsed_str = f"{elapsed}s"
        return f"{status_label} | {elapsed_str}"

    def _get_plan_summary(self, sa: SubagentDisplayData) -> Optional[str]:
        if not sa.workspace_path:
            return None
        workspace = Path(sa.workspace_path)
        plan_path = workspace / "tasks" / "plan.json"
        if not plan_path.exists():
            return None

        try:
            mtime = plan_path.stat().st_mtime
        except (OSError, IOError):
            return None

        cached = self._plan_cache.get(sa.id)
        if cached and cached.path == plan_path and cached.mtime == mtime:
            return cached.summary

        summary = None
        try:
            data = json.loads(plan_path.read_text())
            tasks = data.get("tasks", []) if isinstance(data, dict) else []
            total = len(tasks)
            if total > 0:
                completed = sum(1 for t in tasks if t.get("status") in ("completed", "verified"))
                summary = f"{completed}/{total} done"
        except (OSError, IOError, json.JSONDecodeError, TypeError):
            summary = None

        self._plan_cache[sa.id] = _PlanCache(path=plan_path, mtime=mtime, summary=summary)
        return summary

    def _get_tool_lines(self, sa: SubagentDisplayData) -> List[str]:
        events_path = self._resolve_events_path(sa)
        if not events_path or not events_path.exists():
            return []

        try:
            size = events_path.stat().st_size
        except (OSError, IOError):
            return []

        cached = self._tool_cache.get(sa.id)
        if cached and cached.path == events_path and cached.size == size:
            return cached.tools

        tools = self._extract_tools_from_events(events_path)
        self._tool_cache[sa.id] = _ToolCache(path=events_path, size=size, tools=tools)
        return tools

    def _resolve_events_path(self, sa: SubagentDisplayData) -> Optional[Path]:
        if not sa.log_path:
            return None
        log_path = Path(sa.log_path)
        if not log_path.is_absolute():
            log_path = (Path.cwd() / log_path).resolve()
        if log_path.is_dir():
            resolved = SubagentResult.resolve_events_path(log_path)
            return Path(resolved) if resolved else None
        return log_path

    def _extract_tools_from_events(self, path: Path, max_tools: int = 3) -> List[str]:
        try:
            tail_lines: deque[str] = deque(maxlen=200)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.strip():
                        tail_lines.append(line)
        except (OSError, IOError):
            return []

        tools: List[str] = []
        seen: set[str] = set()

        for line in reversed(tail_lines):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("event_type") != "stream_chunk":
                continue

            chunk = (event.get("data") or {}).get("chunk") or {}
            if chunk.get("type") != "tool_calls":
                continue

            for tc in reversed(chunk.get("tool_calls") or []):
                name = (tc.get("function") or {}).get("name")
                if not name or name in self._IGNORED_TOOL_NAMES:
                    continue
                display_name = format_tool_display_name(name)
                if display_name in seen:
                    continue
                tools.append(self._truncate(display_name, 26))
                seen.add(display_name)
                if len(tools) >= max_tools:
                    return tools

        return tools

    @staticmethod
    def status_icon_and_style(status: str) -> Tuple[str, str]:
        icon = SubagentCard.STATUS_ICONS.get(status, "○")
        style = SubagentCard.STATUS_STYLES.get(status, "#6e7681")
        return icon, style

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."

    @property
    def subagents(self) -> List[SubagentDisplayData]:
        return self._subagents

    def update_subagents(self, subagents: List[SubagentDisplayData]) -> None:
        self._subagents = subagents
        self._refresh_columns()
        self._start_polling_if_needed()

    def update_subagent(self, subagent_id: str, data: SubagentDisplayData) -> None:
        for i, sa in enumerate(self._subagents):
            if sa.id == subagent_id:
                self._subagents[i] = data
                break
        self._refresh_columns()

    def set_status_callback(self, callback: Callable[[str], Optional[SubagentDisplayData]]) -> None:
        self._status_callback = callback
        self._start_polling_if_needed()

    def action_open_selected(self) -> None:
        if not self._subagents:
            return
        selected = self._subagents[self._selected_index % len(self._subagents)]
        self._request_open(selected, self._subagents)

    @classmethod
    def from_spawn_result(
        cls,
        result: Dict[str, Any],
        tool_call_id: Optional[str] = None,
        status_callback: Optional[Callable[[str], Optional[SubagentDisplayData]]] = None,
    ) -> "SubagentCard":
        subagents = []
        spawned = result.get("results", result.get("spawned_subagents", result.get("subagents", [])))
        for sa_data in spawned:
            subagents.append(
                SubagentDisplayData(
                    id=sa_data.get("subagent_id", sa_data.get("id", "unknown")),
                    task=sa_data.get("task", ""),
                    status=sa_data.get("status", "running"),
                    progress_percent=0,
                    elapsed_seconds=sa_data.get("execution_time_seconds", 0.0),
                    timeout_seconds=sa_data.get("timeout_seconds", 300),
                    workspace_path=sa_data.get("workspace", ""),
                    workspace_file_count=0,
                    last_log_line="",
                    error=sa_data.get("error"),
                    answer_preview=(sa_data.get("answer", "") or "")[:200] or None,
                    log_path=sa_data.get("log_path"),
                ),
            )
        return cls(subagents=subagents, tool_call_id=tool_call_id, status_callback=status_callback)
