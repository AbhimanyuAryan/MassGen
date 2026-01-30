## Context
The main TUI (AgentPanel) and subagent TUI (SubagentScreen/Modal) compose their UI independently, causing layout divergence and multiple sources of truth for feature behavior (e.g., task planning cards). The event pipeline is already shared, but UI structure and special tool routing are not.

## Goals / Non-Goals
- Goals:
  - Single source of truth for TUI structure and special-case tool behavior.
  - Identical layout and behavior between main and subagent views.
  - Clear separation of concerns: parsing vs. layout vs. event filtering.
  - Replace the subagent modal with a right-panel subagent view entry point.
  - Provide a horizontal, per-agent subagent overview card that surfaces live status.
- Non-Goals:
  - Full visual redesign or theming changes outside the subagent overview card.
  - Changes to the underlying coordination or tool APIs.

## Decisions
- Decision: Create shared host widgets for common UI blocks.
  - `TimelineHost`: pinned area + TimelineSection + FinalAnswerView + footer.
  - `HeaderHost`: tab bar + status ribbon/line + session info.
- Decision: Extract event filtering/attribution into a shared helper.
  - Use `event.agent_id` and `tool_call_id` mapping consistently across views.
- Decision: Centralize special tool routing (planning, subagent, reminders/injections) in shared helpers.
- Decision: Replace the subagent modal with right-panel navigation.
  - Clicking a subagent column opens the subagent view in the right panel.
  - A back action returns to the main timeline.
- Decision: Horizontal Subagent Overview Card layout.
  - Split into per-agent columns (agent_1 | agent_2 | agent_3).
  - Use horizontal scroll when agents exceed available width.
  - Each column shows a compact summary line above tool lines (task plan progress, or status/elapsed if no plan).
  - Current tool is highlighted; 1-2 recent tools appear below in a faded style.
  - Avoid explicit labels like "Now" / "Recent" and rely on visual hierarchy.

## Risks / Trade-offs
- Risk: Large refactor could introduce regressions in the main TUI.
  - Mitigation: Migrate in phases and keep old layout behind a feature flag during transition.
- Risk: Subagent modal and screen might diverge if only one is refactored.
  - Mitigation: Deprecate the modal and use the right-panel subagent view as the single path.

## Migration Plan
1. Introduce host widgets and wire into main TUI first.
2. Switch subagent screen to use the same hosts.
3. Remove modal entry points and route clicks to the right-panel subagent view.
4. Remove duplicated layout code after parity verification.

## Open Questions
- Do we want a feature flag to toggle legacy layout during migration?
