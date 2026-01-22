# Design: TUI Visual Redesign - Conversational AI Aesthetic

## Context

The MassGen TUI currently has a utilitarian, developer-focused aesthetic. While functional, it lacks the visual polish expected of modern AI tools. Users have expressed that the interface feels "functional but not polished" compared to tools like Claude.ai, Linear, or Warp terminal.

### Stakeholders
- End users who interact with MassGen daily
- Demo audiences who form first impressions from the TUI

### Constraints
- Must work within Textual's widget system and CSS capabilities
- Must maintain all existing keyboard shortcuts and functionality
- Must support both dark and light themes
- ASCII logo must be preserved (per user preference)

## Goals / Non-Goals

### Goals
- Create a modern, approachable "Conversational AI" aesthetic
- Make the input area the visual hero/focal point
- Reduce visual noise through simplified indicators
- Improve information hierarchy with adaptive density
- Maintain full backward compatibility with existing functionality

### Non-Goals
- Adding new features or functionality
- Changing keyboard shortcuts or bindings
- Rewriting the widget architecture
- Creating new themes (only updating existing dark/light)

## Decisions

### Decision 1: Radio-Style Mode Indicators
**What**: Replace emoji icons (📋, 👥, 🔄) with simple radio indicators (◉/○)

**Why**:
- Emoji rendering varies across terminals and platforms
- Radio indicators are universally understood and render consistently
- Cleaner, more professional appearance
- Reduces visual noise

**Alternatives considered**:
- Keep emoji but standardize: Rejected - inconsistent rendering is inherent
- Use ASCII symbols like [x]/[ ]: Rejected - less visually appealing
- Use colored dots: Considered but ◉/○ is more accessible

### Decision 2: Unified Input Card
**What**: Integrate mode toggles into the input area as a single cohesive card

**Why**:
- Creates clear visual hierarchy with input as hero
- Reduces fragmentation of related UI elements
- Follows modern chat interface patterns (Claude.ai, ChatGPT)

**Alternatives considered**:
- Keep mode bar separate: Rejected - fragments the UI
- Put mode toggles inside input: Rejected - too cramped
- Floating mode pills: Considered but adds complexity

### Decision 3: Rounded Box-Drawing Characters
**What**: Use ╭╮╰╯ instead of ┌┐└┘ for card borders

**Why**:
- Softer, more modern appearance
- Well-supported in modern terminals
- Consistent with "Conversational AI" aesthetic

**Alternatives considered**:
- Keep square corners: Rejected - too harsh
- No borders (spacing only): Rejected - loses structure
- Double-line borders: Rejected - too heavy

### Decision 4: Collapsed Tool Cards by Default
**What**: Tool cards show only name + status + time, expand on click

**Why**:
- Reduces visual density during active sessions
- Users can expand when they need details
- Matches adaptive density principle

**Alternatives considered**:
- Always expanded: Current state - too dense
- Never show details: Rejected - loses functionality
- Hover to expand: Rejected - click is more intentional

### Decision 5: Dot-Based Agent Tab Indicators
**What**: Replace emoji status (⏳, 🔄, ✅, ❌) with dots (◉, ○, ✓)

**Why**:
- Consistent with mode toggle redesign
- Cleaner appearance
- Faster visual parsing

**Implementation**:
- ◉ = active/streaming (filled dot)
- ○ = waiting/inactive (empty dot)
- ✓ = completed successfully
- ✗ = error state

## Risks / Trade-offs

### Risk 1: Terminal Compatibility
**Risk**: Rounded box-drawing characters may not render on all terminals
**Mitigation**: These characters are part of the Unicode box-drawing block, widely supported since the 1990s. Fall back gracefully is unlikely to be needed.

### Risk 2: User Adjustment Period
**Risk**: Existing users may be momentarily confused by new indicators
**Mitigation**: The radio-style indicators (◉/○) are universally understood. Brief adjustment period expected.

### Risk 3: Accessibility
**Risk**: Removing emoji may reduce accessibility for some users
**Mitigation**: The text labels remain ("Normal", "Multi", "Refine"). Color is not the only differentiator.

## Implementation Approach

### Phase Order Rationale
1. **Input Bar + Mode Toggles**: Highest impact, touches every session
2. **Agent Tabs**: Navigation clarity, builds on phase 1 patterns
3. **Tool Cards**: Information density, requires collapse/expand logic
4. **Welcome Screen**: First impression, quick win after core work
5. **Task Lists**: Progressive enhancement
6. **Final Polish**: Refinement pass

### CSS Strategy
- Add new CSS classes rather than modifying existing ones where possible
- Use CSS variables for colors to maintain theme flexibility
- Test both dark and light themes after each phase

### Testing Strategy
- Manual testing with `uv run massgen --config massgen/configs/basic/multi/two_agents.yaml`
- Verify all keyboard shortcuts work
- Check both welcome screen and active session states
- Test tool card expand/collapse interactions

## Open Questions

1. **Should collapsed be the permanent default or a user preference?**
   - Current decision: Permanent default, can revisit if users request toggle

2. **Should we add subtle animations for state changes?**
   - Current decision: Out of scope for this change, could be future enhancement
