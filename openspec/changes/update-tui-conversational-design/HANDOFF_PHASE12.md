# Handoff: Phase 12 - View-Based Round & Final Answer Navigation

## Context

Phases 9, 11, and 13 are complete. Phase 12 is the next major feature - implementing view-based navigation for rounds and final answers, replacing inline separators with a dropdown-based navigation system.

## Current State

The TUI now has:
- Edge-to-edge layout (Phase 9)
- Scroll indicators in TimelineSection (Phase 11.2)
- Inline reasoning with subtle styling (Phase 11.1 - simplified)
- Token/cost display in AgentStatusRibbon (Phase 13.1)
- ExecutionStatusLine with agent colors and pulsing animation (Phase 13.2)
- Mode bar + helper text on same line above input
- Blue separator line above mode bar

## Phase 12 Overview

**Goal**: Replace inline round separators and final answer cards with a view-based navigation system via dropdown in the AgentStatusRibbon.

### 12.1 View Dropdown in Status Ribbon
Current: `Round N ▾` dropdown exists but only for rounds.
Target: Full view selector with Final Answer option at top.

**Tasks:**
1. Update AgentStatusRibbon to handle "Final Answer" as a special view
2. Show separator between Final Answer and rounds in dropdown
3. Display indicators: `◉ Round N (current)`, `↻ Round N` (context reset)
4. Update label dynamically: "Round 2 ▾" or "✓ Final Answer ▾"

### 12.2 Round View Content
Current: Content appends to timeline linearly with RestartBanner separators.
Target: Per-round content storage with view switching.

**Tasks:**
1. Create data structure: `agent_views[agent_id]["rounds"][round_num]`
2. Store content by round as it arrives
3. Implement `switch_to_round(agent_id, round_num)` method
4. Clear and repopulate panel when switching views
5. Remove RestartBanner widget (no longer needed)

### 12.3 Final Answer View
Current: FinalPresentationCard inline in timeline.
Target: Dedicated full-screen view.

**Design:**
```
─────────────────────────────────────────────────────────────────
                         Final Answer
─────────────────────────────────────────────────────────────────

[Markdown-rendered final answer content]

─────────────────────────────────────────────────────────────────
Consensus reached • Presented by Agent A • 3 rounds • 2/3 agreed
                    [Copy] [Workspace] [Voting Details]
─────────────────────────────────────────────────────────────────
                     Type below to continue...
```

**Tasks:**
1. Create `FinalAnswerView` widget (or repurpose FinalPresentationCard)
2. Centered layout with generous whitespace
3. Markdown rendering for content
4. Metadata footer with consensus info
5. Action buttons: Copy, Workspace, Voting Details

### 12.4 Auto-Navigation
**Tasks:**
1. On consensus, add "Final Answer" to dropdown
2. Auto-switch presenting agent to Final Answer view
3. Keep other agents on their current round
4. Allow navigation back to any round

### 12.5 Cleanup
**Tasks:**
1. Remove RestartBanner class
2. Remove inline FinalPresentationCard usage
3. Clean up related CSS
4. Update exports in __init__.py

## Key Files to Modify

| File | Changes |
|------|---------|
| `textual_widgets/agent_status_ribbon.py` | View selector dropdown, Final Answer option |
| `textual_terminal_display.py` | Per-round content storage, view switching logic |
| `textual_widgets/content_sections.py` | Remove RestartBanner, update FinalPresentationCard |
| `textual_themes/dark.tcss` | Final Answer view styling |
| `textual_themes/light.tcss` | Final Answer view styling |

## Testing Commands

```bash
# Multi-round session to test view switching
uv run massgen --display textual --config massgen/configs/basic/multi/two_agents.yaml "Write a haiku about coding"

# Force multiple rounds by asking for refinement
uv run massgen --display textual --config massgen/configs/basic/multi/three_agents.yaml "Explain quantum entanglement"
```

## Implementation Notes

- The AgentStatusRibbon already has a round selector with RoundSelected message
- Content is currently stored in TimelineSection - need to restructure for per-round storage
- RestartBanner adds visual separators between rounds - these go away with view-based nav
- FinalPresentationCard exists but needs to become a full-screen view
- Consider using Textual's Screen switching or a visibility toggle approach

## Dependencies

- Phase 8.3 AgentStatusRibbon (done)
- Phase 10 content area cleanup (done)
- Understanding of orchestrator round/consensus events
