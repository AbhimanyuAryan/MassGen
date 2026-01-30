# -*- coding: utf-8 -*-
"""Shared TUI components and utilities.

This module provides single-source-of-truth implementations for TUI display
components that are used across both main MassGen runs and subprocess displays.

Before this consolidation, tool categories, status indicators, and display
utilities were duplicated across 3+ locations. This created maintenance burden
and risked visual inconsistencies between main and subprocess displays.

Architecture:
- tool_registry.py: Tool categorization, icons, and colors
- status_registry.py: Status indicators and formatting
- file_preview.py: File rendering with syntax highlighting
- tui_debug.py: Debug logging utilities
- event_stream.py: Event delivery abstraction (polling/streaming)
- subprocess_display_controller.py: Unified subprocess display controller
"""

from .event_stream import EventStream, PollingEventStream, StreamingEventStream
from .file_preview import BINARY_EXTENSIONS, FILE_LANG_MAP, render_file_preview
from .status_registry import (
    STATUS_COLORS,
    STATUS_ICONS,
    format_elapsed_time,
    get_status_icon_and_color,
)
from .subprocess_display_controller import StatusInfo, SubprocessDisplayController
from .tool_registry import (
    TOOL_CATEGORIES,
    clean_tool_arguments,
    clean_tool_result,
    format_tool_display_name,
    get_tool_category,
)
from .tui_debug import get_tui_debug_logger, tui_log

__all__ = [
    # Tool registry
    "TOOL_CATEGORIES",
    "get_tool_category",
    "format_tool_display_name",
    "clean_tool_arguments",
    "clean_tool_result",
    # Status registry
    "STATUS_ICONS",
    "STATUS_COLORS",
    "get_status_icon_and_color",
    "format_elapsed_time",
    # File preview
    "FILE_LANG_MAP",
    "BINARY_EXTENSIONS",
    "render_file_preview",
    # Debug utilities
    "get_tui_debug_logger",
    "tui_log",
    # Event streaming
    "EventStream",
    "PollingEventStream",
    "StreamingEventStream",
    # Subprocess display controller
    "SubprocessDisplayController",
    "StatusInfo",
]
