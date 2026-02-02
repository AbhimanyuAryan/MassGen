# Change: Refactor TUI Shared Hosts

## Why
Main and subagent TUIs currently assemble UI structure separately, which leads to drift and duplicated logic (e.g., task planning display). This violates the single source of truth goal and creates regressions whenever one view changes.

## What Changes
- Introduce shared host widgets for core TUI layout blocks (timeline, pinned UI, header/status).
- Centralize event filtering/attribution and special tool routing so both views behave identically.
- Refactor main and subagent views to compose these hosts instead of hand-rolling their own layout.
- Replace the legacy subagent modal with a right-panel subagent view entry point.
- Redesign subagent summary into a horizontal, per-agent overview card with live status and tool context.

## Impact
- Affected specs: textual-tui
- Affected code:
  - `massgen/frontend/displays/textual_terminal_display.py`
  - `massgen/frontend/displays/textual_widgets/subagent_screen.py`
  - `massgen/frontend/displays/textual_widgets/subagent_tui_modal.py`
  - `massgen/frontend/displays/base_tui_layout.py`
  - `massgen/frontend/displays/tui_event_pipeline.py`
  - `massgen/frontend/displays/content_processor.py`
  - `massgen/frontend/displays/textual_widgets/*` (new host widgets)
