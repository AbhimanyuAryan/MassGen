# Implementation Tasks

## Approval Workflow

**IMPORTANT**: After completing each phase, stop and ask the user to run the TUI for visual approval before proceeding to the next phase.

```
Phase N complete → User runs TUI → User approves → Proceed to Phase N+1
                                 → User requests changes → Iterate → Re-approve
```

Each phase section ends with a **CHECKPOINT** task to remind you to pause for approval.

---

## 1. Phase 1: Input Bar + Mode Toggles ✓ COMPLETED

### 1.1 Mode Toggle Redesign
- [x] 1.1.1 Update `ModeToggle.ICONS` to use radio indicators (◉/○) instead of emoji
- [x] 1.1.2 Update `ModeToggle.LABELS` - kept "Refine OFF" per user preference
- [x] 1.1.3 Update `ModeToggle.render()` to display cleaner format
- [x] 1.1.4 Update CSS for `.state-*` classes with softer colors

### 1.2 Unified Input Card
- [~] 1.2.1 SKIPPED: Keep existing ModeBar + Input structure (simpler)
- [x] 1.2.2 Update CSS to use `border: round` for rounded corners
- [~] 1.2.3 SKIPPED: Keep mode toggles as separate widget (cleaner separation)
- [~] 1.2.4 SKIPPED: Keep existing hint layout
- [~] 1.2.5 SKIPPED: Existing padding is adequate

### 1.3 Input Styling
- [x] 1.3.1 Update `#input_area` CSS - transparent background for clean look
- [x] 1.3.2 Update `#question_input` CSS - rounded border, transparent background
- [x] 1.3.3 Update `#mode_bar` CSS - transparent background
- [~] 1.3.4 Placeholder text unchanged (existing is fine)
- [x] **1.3.5 CHECKPOINT: User approval for input bar + mode toggles ✓**

**Implementation Notes:**
- Files modified: `mode_bar.py`, `dark.tcss`, `light.tcss`
- Key change: Transparent backgrounds for `#input_area`, `#mode_bar`, and `#question_input`
- Mode toggles use softer colors: #1a3a2a (green), #3d3520 (warning), #2d2d2d (off)
- User preferred keeping "Refine OFF" label over "Skip"

## 2. Phase 2: Agent Tabs

### 2.1 Tab Indicator Redesign
- [ ] 2.1.1 Replace emoji status icons with dot indicators in `tab_bar.py`
- [ ] 2.1.2 Add model name subtitle display to tabs
- [ ] 2.1.3 Update CSS for new tab styling with underline indicator

### 2.2 Tab Spacing
- [ ] 2.2.1 Increase horizontal spacing between tabs
- [ ] 2.2.2 Remove bracket notation `[1]` from tabs
- [ ] **2.2.3 CHECKPOINT: User approval for agent tabs**

## 3. Phase 3: Tool Cards

### 3.1 Collapsible Implementation
- [ ] 3.1.1 Add `collapsed` state to `ToolCallCard`
- [ ] 3.1.2 Implement collapsed rendering (tool name + status + time only)
- [ ] 3.1.3 Add click handler to expand/collapse
- [ ] 3.1.4 Default to collapsed state

### 3.2 Visual Styling
- [ ] 3.2.1 Update CSS for rounded card appearance
- [ ] 3.2.2 Soften category colors (less saturated)
- [ ] 3.2.3 Remove emoji icons, use text prefixes
- [ ] **3.2.4 CHECKPOINT: User approval for tool cards**

## 4. Phase 4: Welcome Screen

### 4.1 Layout Improvements
- [ ] 4.1.1 Keep ASCII logo (user preference)
- [ ] 4.1.2 Center input prompt area
- [ ] 4.1.3 Add subtle tagline below logo

### 4.2 Help Hints
- [ ] 4.2.1 Make keyboard hints smaller/muted
- [ ] 4.2.2 Use bullet separators (•) instead of pipes
- [ ] **4.2.3 CHECKPOINT: User approval for welcome screen**

## 5. Phase 5: Task Lists + Progress

### 5.1 Progress Bar
- [ ] 5.1.1 Add visual progress bar to task section
- [ ] 5.1.2 Show "X of Y" count display

### 5.2 Task Indicators
- [ ] 5.2.1 Update task indicators (● in-progress, ○ pending, ✓ done)
- [ ] 5.2.2 Add "← current" marker for active task
- [ ] 5.2.3 Implement smart truncation with ellipsis
- [ ] **5.2.4 CHECKPOINT: User approval for task lists + progress**

## 6. Phase 6: Modals + Enhanced Previews

### 6.1 Modal Visual Redesign
- [ ] 6.1.1 Update all modal containers to use rounded borders
- [ ] 6.1.2 Remove emoji from modal titles
- [ ] 6.1.3 Use bullet separators in modal headers
- [ ] 6.1.4 Soften border colors across all modals
- [ ] 6.1.5 Improve internal padding and margins
- [ ] 6.1.6 Unify button styling across modals
- [ ] 6.1.7 Polish close button with softer hover states

### 6.2 Diff View for File Edits
- [ ] 6.2.1 Create `DiffView` widget for displaying file changes
- [ ] 6.2.2 Implement colored diff rendering (green +, red -)
- [ ] 6.2.3 Add line numbers to diff display
- [ ] 6.2.4 Show context lines around changes
- [ ] 6.2.5 Add "+X -Y lines" summary header
- [ ] 6.2.6 Integrate diff view into tool result display for write_file/edit operations

### 6.3 Workspace Modal Improvements
- [ ] 6.3.1 Implement tree view for directory structure (replace flat list)
- [ ] 6.3.2 Add collapsible directory nodes
- [ ] 6.3.3 Show file statistics (number of files, +X -Y lines)
- [ ] 6.3.4 Add simple text-based file/folder icons
- [ ] 6.3.5 Show summary line (agents, turns, consensus status)

### 6.4 Better Tool Result Previews
- [ ] 6.4.1 Create formatted preview renderer for common result types
- [ ] 6.4.2 Replace raw dict display with readable formatting
- [ ] 6.4.3 Implement smart truncation with "show more" expansion
- [ ] 6.4.4 Add basic syntax highlighting for code in results
- [ ] **6.4.5 CHECKPOINT: User approval for modals + enhanced previews**

## 7. Phase 7: Header + Final Polish

### 7.1 Header Simplification
- [ ] 7.1.1 Remove emoji from HeaderWidget
- [ ] 7.1.2 Use bullet separator (•) instead of pipe

### 7.2 Color Refinements
- [ ] 7.2.1 Slightly desaturate accent colors in dark.tcss
- [ ] 7.2.2 Update light.tcss to match new aesthetic
- [ ] 7.2.3 Add softer border colors

### 7.3 New CSS Classes
- [ ] 7.3.1 Add `.rounded-card` class
- [ ] 7.3.2 Add `.input-hero` class
- [ ] 7.3.3 Add `.mode-pill` class
- [ ] 7.3.4 Add `.progress-bar` class
- [ ] 7.3.5 Add `.diff-add` and `.diff-remove` classes
- [ ] 7.3.6 Add `.tree-node` class for workspace tree
- [ ] **7.3.7 CHECKPOINT: User approval for header + final polish**

## 8. Phase 8: Professional Visual Polish

### 8.1 Animation & Feedback System (Phase 8a)
- [ ] 8.1.1 Implement pulsing dot animation for active agent tabs (800ms cycle, opacity 0.5↔1.0)
- [ ] 8.1.2 Add blinking cursor `▌` at end of streaming text (530ms cycle)
- [ ] 8.1.3 Implement tool card time ticking during execution (`⟳ 0.1s → 0.2s...`)
- [ ] 8.1.4 Add fade-in transitions for tool results (150ms)
- [ ] 8.1.5 Add fade-in/out for modal open/close (150ms)
- [ ] 8.1.6 Implement phase indicator highlight pulse on change (300ms)
- [ ] 8.1.7 Add round separator fade-in (200ms)
- [ ] 8.1.8 Implement error toast with auto-dismiss (3s)
- [ ] **8.1.9 CHECKPOINT: User approval for animations**

### 8.2 Professional Color Palette (Phase 8b)
- [ ] 8.2.1 Define CSS variables for background layers ($bg-base, $bg-surface, $bg-card, $bg-elevated)
- [ ] 8.2.2 Define CSS variables for borders ($border-subtle, $border-default, $border-focus)
- [ ] 8.2.3 Define CSS variables for text hierarchy ($text-primary, $text-secondary, $text-muted)
- [ ] 8.2.4 Define CSS variables for semantic accents ($accent-blue, $accent-green, $accent-yellow, $accent-red, $accent-purple)
- [ ] 8.2.5 Update dark.tcss with new color palette
- [ ] 8.2.6 Update light.tcss with corresponding light theme colors
- [ ] 8.2.7 Apply new colors to all existing widgets
- [ ] **8.2.8 CHECKPOINT: User approval for color palette**

### 8.3 Agent Status Ribbon (Phase 8c)
- [ ] 8.3.1 Create new `AgentStatusRibbon` widget
- [ ] 8.3.2 Implement activity indicator display (◉ Streaming, ○ Idle, ⏳ Thinking, ⏹ Canceled, ✗ Error)
- [ ] 8.3.3 Add elapsed time display with real-time ticking updates
- [ ] 8.3.4 Add compact tasks progress display (X/Y with mini progress bar `━━░░`)
- [ ] 8.3.5 Add token count display
- [ ] 8.3.6 Add cost estimate display
- [ ] 8.3.7 Make Tasks segment clickable → opens Task Plan Modal
- [ ] 8.3.8 Wire ribbon to update when switching agent tabs
- [ ] 8.3.9 Position ribbon below tab bar in layout
- [ ] **8.3.10 CHECKPOINT: User approval for status ribbon**

### 8.4 Phase Indicator Bar (Phase 8d)
- [ ] 8.4.1 Create new `PhaseIndicatorBar` widget
- [ ] 8.4.2 Implement phase states: Initial Answer → Voting → Consensus → Presentation
- [ ] 8.4.3 Add visual indicators: ○ pending, ● current (with pulse), ✓ completed
- [ ] 8.4.4 Add arrow separators (→) between phases
- [ ] 8.4.5 Wire to orchestrator phase changes
- [ ] 8.4.6 Add highlight pulse animation on phase change (300ms)
- [ ] 8.4.7 Only show in multi-agent mode
- [ ] **8.4.8 CHECKPOINT: User approval for phase indicator**

### 8.5 Session Info Panel (Phase 8e)
- [ ] 8.5.1 Create new `SessionInfoPanel` widget
- [ ] 8.5.2 Add turn counter display (Turn X of Y)
- [ ] 8.5.3 Add elapsed time with real-time updates
- [ ] 8.5.4 Add total cost estimate (aggregated across agents)
- [ ] 8.5.5 Add total token count (aggregated across agents)
- [ ] 8.5.6 Position in header area (top of screen)
- [ ] 8.5.7 Style with rounded borders, subtle background
- [ ] **8.5.8 CHECKPOINT: User approval for session info panel**

### 8.6 Improved Round Separators (Phase 8f)
- [ ] 8.6.1 Replace box-style round indicators with dashed line separators (┄┄┄)
- [ ] 8.6.2 Center "Round X Complete" text in separator
- [ ] 8.6.3 Add summary line below (vote count, consensus status)
- [ ] 8.6.4 Add fade-in animation when separator appears (200ms)
- [ ] 8.6.5 Add breathing room (padding) around separators
- [ ] **8.6.6 CHECKPOINT: User approval for round separators**

### 8.7 Final Answer Card Redesign (Phase 8g)
- [ ] 8.7.1 Update final answer card with rounded corners (╭╮╰╯)
- [ ] 8.7.2 Add left accent border (▌) for visual weight
- [ ] 8.7.3 Add summary footer (consensus status, rounds, agents, cost)
- [ ] 8.7.4 Improve internal padding and whitespace
- [ ] 8.7.5 Apply proper markdown rendering
- [ ] **8.7.6 CHECKPOINT: User approval for final answer card**

### 8.8 Enhanced Tab Design (Phase 8h)
- [ ] 8.8.1 Implement two-line tab display (agent name bold + model name muted)
- [ ] 8.8.2 Add rounded corners for selected tab (╭╮╰╯), square for unselected
- [ ] 8.8.3 Add underline indicator (════) below selected tab
- [ ] 8.8.4 Implement status-specific indicator colors:
  - `◉` Streaming/Active (accent-blue, pulsing)
  - `○` Idle/Waiting (text-muted)
  - `✓` Done (accent-green)
  - `⏹` Canceled (accent-yellow)
  - `✗` Error (accent-red)
- [ ] 8.8.5 Update tab spacing for breathing room
- [ ] **8.8.6 CHECKPOINT: User approval for tab design**

### 8.9 Visual Depth Through Layering (Phase 8i)
- [ ] 8.9.1 Apply $bg-card to main card elements
- [ ] 8.9.2 Apply $bg-elevated to nested/inset content
- [ ] 8.9.3 Add left accent borders where appropriate
- [ ] 8.9.4 Add focus ring ($border-focus) to interactive elements
- [ ] 8.9.5 Ensure consistent layering across all widgets
- [ ] **8.9.6 CHECKPOINT: User approval for visual depth**

### 8.10 Improved Task Modal (Phase 8j)
- [ ] 8.10.1 Update task modal with rounded corners
- [ ] 8.10.2 Add progress bar in modal header (━━━━░░░░)
- [ ] 8.10.3 Add fraction display (X/Y) with visual bar
- [ ] 8.10.4 Implement task indicators (✓ done, ● current, ○ pending)
- [ ] 8.10.5 Add "← current" marker for active task
- [ ] 8.10.6 Ensure full task names displayed (not truncated)
- [ ] 8.10.7 Add close button and click-outside-to-dismiss
- [ ] 8.10.8 Modal fade-in animation (150ms)
- [ ] **8.10.9 CHECKPOINT: User approval for task modal**

---

## 9. Testing & Verification

- [ ] 9.1 Run MassGen with multi-agent config, verify welcome screen
- [ ] 9.2 Test mode toggle interactions
- [ ] 9.3 Verify tool cards collapse/expand behavior
- [ ] 9.4 Test task list progress display
- [ ] 9.5 Verify all keyboard shortcuts still work
- [ ] 9.6 Test both dark and light themes
- [ ] 9.7 Verify modal styling consistency
- [ ] 9.8 Test diff view with file edit operations
- [ ] 9.9 Test workspace modal tree view navigation
- [ ] 9.10 Verify tool result preview formatting
- [ ] 9.11 Test agent status ribbon updates during execution
- [ ] 9.12 Verify phase indicator bar shows correct coordination state
- [ ] 9.13 Test session info panel updates
- [ ] 9.14 Verify activity pulse animation works
- [ ] 9.15 Test final answer card with consensus results
