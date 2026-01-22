# TUI Visual Design Specification

## ADDED Requirements

### Requirement: Conversational AI Visual Aesthetic
The TUI SHALL follow a "Conversational AI" visual aesthetic that prioritizes approachability, modern design, and clear visual hierarchy.

#### Scenario: Input area is the visual hero
- **WHEN** the user views any TUI screen (welcome or active session)
- **THEN** the input area SHALL be the most visually prominent element
- **AND** mode toggles SHALL be integrated into the input card

#### Scenario: Rounded corners for softer appearance
- **WHEN** displaying card-like elements (input card, tool cards)
- **THEN** the system SHALL use rounded box-drawing characters (╭╮╰╯)

#### Scenario: Generous whitespace
- **WHEN** displaying content
- **THEN** the system SHALL provide adequate spacing between elements
- **AND** avoid cramped or overly dense layouts

### Requirement: Radio-Style Mode Indicators
The TUI SHALL use radio-style indicators (◉/○) for mode toggles instead of emoji icons.

#### Scenario: Active state indicator
- **WHEN** a mode is active/enabled
- **THEN** the indicator SHALL display as ◉ (filled circle)

#### Scenario: Inactive state indicator
- **WHEN** a mode is inactive/disabled
- **THEN** the indicator SHALL display as ○ (empty circle)

#### Scenario: Mode labels without suffixes
- **WHEN** displaying mode labels
- **THEN** labels SHALL NOT include "ON/OFF" suffixes
- **AND** the state SHALL be indicated by the radio symbol only

### Requirement: Unified Input Card
The TUI SHALL display the input area as a unified card that integrates mode toggles, text input, and submit hint.

#### Scenario: Mode toggles in input card
- **WHEN** the input card is displayed
- **THEN** mode toggles SHALL appear at the top of the card
- **AND** be visually connected to the input area

#### Scenario: Submit hint integration
- **WHEN** the input card is displayed
- **THEN** a submit hint (e.g., "⌘⏎ Send") SHALL appear integrated in the bottom-right

#### Scenario: Input card focus state
- **WHEN** the input area receives focus
- **THEN** the card border SHALL change to indicate focus

### Requirement: Dot-Based Agent Tab Indicators
The TUI SHALL use dot-based indicators for agent tab status instead of emoji.

#### Scenario: Active agent indicator
- **WHEN** an agent is actively streaming or processing
- **THEN** the tab SHALL display ◉ (filled dot)

#### Scenario: Waiting agent indicator
- **WHEN** an agent is waiting/inactive
- **THEN** the tab SHALL display ○ (empty dot)

#### Scenario: Completed agent indicator
- **WHEN** an agent has completed successfully
- **THEN** the tab SHALL display ✓ (checkmark)

#### Scenario: Agent model subtitle
- **WHEN** displaying agent tabs
- **THEN** the model name SHALL appear as a subtitle below the agent name

### Requirement: Collapsible Tool Cards
The TUI SHALL display tool execution cards in a collapsed state by default, with the ability to expand for details.

#### Scenario: Collapsed tool card display
- **WHEN** a tool card is in collapsed state
- **THEN** it SHALL display only: tool name, status indicator, and execution time

#### Scenario: Expand tool card on click
- **WHEN** the user clicks on a collapsed tool card
- **THEN** the card SHALL expand to show parameters and results

#### Scenario: Default collapsed state
- **WHEN** a new tool execution completes
- **THEN** the tool card SHALL be displayed in collapsed state by default

### Requirement: Task List Progress Visualization
The TUI SHALL display task lists with visual progress indicators.

#### Scenario: Progress bar display
- **WHEN** a task list has multiple items
- **THEN** a progress bar SHALL be displayed showing completion status

#### Scenario: Task count display
- **WHEN** displaying task progress
- **THEN** the format SHALL be "X of Y" (e.g., "2 of 8")

#### Scenario: Current task indicator
- **WHEN** a task is in progress
- **THEN** it SHALL be marked with ● and "← current" indicator

#### Scenario: Completed task indicator
- **WHEN** a task is completed
- **THEN** it SHALL be marked with ✓

#### Scenario: Pending task indicator
- **WHEN** a task is pending
- **THEN** it SHALL be marked with ○

### Requirement: Simplified Header Display
The TUI header SHALL use a simplified format without emoji.

#### Scenario: Header separator style
- **WHEN** displaying header elements
- **THEN** bullet separators (•) SHALL be used instead of pipes (|)

#### Scenario: No emoji in header
- **WHEN** displaying the header
- **THEN** emoji SHALL NOT be used in the header text

### Requirement: Consistent Modal Styling
All TUI modals SHALL follow the Conversational AI visual aesthetic with rounded borders and consistent styling.

#### Scenario: Modal rounded borders
- **WHEN** a modal is displayed
- **THEN** the modal container SHALL use rounded box-drawing characters (╭╮╰╯)

#### Scenario: Modal header without emoji
- **WHEN** a modal header is displayed
- **THEN** emoji SHALL NOT be used in the modal title

#### Scenario: Modal button consistency
- **WHEN** buttons are displayed in a modal
- **THEN** all buttons SHALL use consistent styling across all modals

#### Scenario: Modal close button styling
- **WHEN** a close button is displayed
- **THEN** it SHALL have softer styling with visible hover state

### Requirement: Diff View for File Edits
The TUI SHALL display file edit operations using a colored diff view showing additions and deletions.

#### Scenario: Colored diff display
- **WHEN** a file edit tool result is displayed
- **THEN** additions SHALL be shown in green with + prefix
- **AND** deletions SHALL be shown in red with - prefix

#### Scenario: Diff line numbers
- **WHEN** displaying a diff view
- **THEN** line numbers SHALL be shown for context

#### Scenario: Diff summary statistics
- **WHEN** displaying a diff view
- **THEN** a summary SHALL show "+X -Y lines" count

#### Scenario: Diff context lines
- **WHEN** displaying a diff view
- **THEN** surrounding unchanged lines SHALL be shown for context

### Requirement: Workspace Tree View
The workspace modal SHALL display directory structure as a hierarchical tree instead of a flattened list.

#### Scenario: Tree structure display
- **WHEN** the workspace modal is opened
- **THEN** files and directories SHALL be displayed in a tree hierarchy
- **AND** subdirectories SHALL be indented under their parent

#### Scenario: File statistics in tree
- **WHEN** displaying files in the workspace tree
- **THEN** changed files SHALL show "+X -Y" line statistics

#### Scenario: Workspace summary
- **WHEN** the workspace modal header is displayed
- **THEN** it SHALL show total file count and aggregate line changes (e.g., "8 files • +156 -42")

#### Scenario: Directory icons
- **WHEN** displaying tree nodes
- **THEN** directories SHALL be prefixed with 📁
- **AND** files SHALL be prefixed with 📄

### Requirement: Formatted Tool Result Previews
Tool results SHALL be displayed with formatted, readable output instead of raw dictionary representations.

#### Scenario: Formatted result display
- **WHEN** a tool result is displayed
- **THEN** it SHALL be formatted for human readability
- **AND** SHALL NOT display raw Python dict/JSON syntax

#### Scenario: Long result truncation
- **WHEN** a tool result exceeds display limits
- **THEN** it SHALL be truncated with a "show more" option

#### Scenario: Code syntax highlighting
- **WHEN** tool results contain code
- **THEN** basic syntax highlighting SHALL be applied

### Requirement: Agent Status Ribbon
The TUI SHALL display an agent status ribbon showing real-time information about the currently selected agent.

#### Scenario: Status ribbon content
- **WHEN** an agent is selected
- **THEN** the status ribbon SHALL display: agent name, model name, current activity, elapsed time, task progress, token count, and cost estimate

#### Scenario: Task progress clickable
- **WHEN** the user clicks on the Tasks segment in the status ribbon
- **THEN** the Task Plan Modal SHALL open with the full task list

#### Scenario: Activity states displayed
- **WHEN** displaying agent activity
- **THEN** the ribbon SHALL show one of: "Idle", "Thinking...", "Streaming...", "Canceled", or "Error"

### Requirement: Activity Pulse Animation
The TUI SHALL provide visual feedback when an agent is actively working through a pulse animation.

#### Scenario: Pulse during streaming
- **WHEN** an agent is actively streaming content
- **THEN** the agent indicator (◉) SHALL pulse with a 0.5s cycle

#### Scenario: No pulse when idle
- **WHEN** an agent is idle or waiting
- **THEN** the indicator SHALL NOT pulse

### Requirement: Phase Indicator Bar
The TUI SHALL display a phase indicator bar showing coordination flow progress in multi-agent mode.

#### Scenario: Phase bar display
- **WHEN** running in multi-agent mode
- **THEN** a phase indicator bar SHALL show: Initial Answer → Voting → Consensus → Presentation

#### Scenario: Current phase highlighting
- **WHEN** displaying the phase bar
- **THEN** the current phase SHALL be highlighted with ● and accent color
- **AND** completed phases SHALL show ✓

#### Scenario: Phase bar visibility
- **WHEN** running in single-agent mode
- **THEN** the phase indicator bar SHALL NOT be displayed

### Requirement: Session Info Panel
The TUI SHALL display a session info panel in the header area showing session statistics.

#### Scenario: Session info content
- **WHEN** a session is active
- **THEN** the panel SHALL display: turn number, elapsed time, estimated cost, and token count

#### Scenario: Dynamic updates
- **WHEN** session statistics change
- **THEN** the panel SHALL update in real-time

### Requirement: Round Separators
The TUI SHALL use lightweight dashed separators between coordination rounds instead of heavy boxes.

#### Scenario: Round separator style
- **WHEN** displaying a round boundary
- **THEN** dashed/dotted line separators SHALL be used

#### Scenario: Round summary info
- **WHEN** a round completes
- **THEN** summary info (vote count, consensus status) SHALL be displayed below the separator

### Requirement: Final Answer Card
The TUI SHALL display final answers in a visually distinct card with session summary.

#### Scenario: Final answer visual design
- **WHEN** displaying a final answer
- **THEN** the card SHALL have a left accent border (▌) for visual weight
- **AND** rounded corners

#### Scenario: Final answer summary footer
- **WHEN** displaying a final answer
- **THEN** the card SHALL include a footer with: consensus status, round count, agent count, and cost

### Requirement: Visual Depth Through Layering
The TUI SHALL establish visual hierarchy through background color layering.

#### Scenario: Background layer hierarchy
- **WHEN** displaying UI elements
- **THEN** cards SHALL use bg-card color
- **AND** nested content SHALL use bg-elevated color
- **AND** the main background SHALL use bg-base color

#### Scenario: Focus state visual feedback
- **WHEN** an element receives focus
- **THEN** a subtle glow or ring effect SHALL be applied

### Requirement: Animation & Feedback Philosophy
The TUI SHALL follow a "calm presence with purposeful signals" animation philosophy where animation serves information, not decoration.

#### Scenario: Default calm state
- **WHEN** no activity is occurring
- **THEN** all UI elements SHALL be static and calm

#### Scenario: Single animated element
- **WHEN** activity is occurring
- **THEN** only ONE element SHALL be animated at a time to guide user attention

#### Scenario: Streaming cursor
- **WHEN** an agent is actively streaming text
- **THEN** a blinking cursor (▌) SHALL appear at the end of the text
- **AND** the cursor SHALL blink with a 530ms cycle
- **AND** the cursor SHALL disappear when streaming completes

#### Scenario: Active agent pulse
- **WHEN** an agent is thinking or streaming
- **THEN** the agent indicator (◉) SHALL pulse with opacity 0.5↔1.0
- **AND** the pulse cycle SHALL be 800ms

#### Scenario: Tool execution time ticking
- **WHEN** a tool is actively executing
- **THEN** the elapsed time SHALL tick in real-time (0.1s → 0.2s → 0.3s...)
- **AND** a spinner icon (⟳) SHALL be displayed

#### Scenario: Result fade-in
- **WHEN** a tool result or new content appears
- **THEN** it SHALL fade in with a 150ms duration
- **AND** SHALL NOT appear abruptly

#### Scenario: Modal transitions
- **WHEN** a modal opens or closes
- **THEN** it SHALL fade in/out with a 150ms duration

#### Scenario: Phase change highlight
- **WHEN** the coordination phase changes
- **THEN** the new phase indicator SHALL briefly pulse/highlight
- **AND** the highlight duration SHALL be 300ms

#### Scenario: Round separator appearance
- **WHEN** a round completes and separator appears
- **THEN** the separator SHALL fade in with a 200ms duration

#### Scenario: Error notification
- **WHEN** an error occurs
- **THEN** a toast notification SHALL appear with red color indication
- **AND** the toast SHALL auto-dismiss after 3 seconds

#### Scenario: Silent background updates
- **WHEN** token counts or costs update
- **THEN** the values SHALL update silently without animation
- **AND** SHALL NOT draw attention from the main content

### Requirement: Professional Color Palette
The TUI SHALL use a modern, harmonious color palette with proper visual hierarchy.

#### Scenario: Background layers
- **WHEN** displaying the UI
- **THEN** backgrounds SHALL use these layers:
  - bg-base: #0D1117 (main background)
  - bg-surface: #161B22 (elevated surfaces)
  - bg-card: #21262D (cards, modals)
  - bg-elevated: #30363D (hover, selected)

#### Scenario: Border colors
- **WHEN** displaying borders
- **THEN** the following colors SHALL be used:
  - border-subtle: #30363D (most borders)
  - border-default: #484F58 (emphasized)
  - border-focus: #58A6FF (focus rings)

#### Scenario: Text hierarchy
- **WHEN** displaying text
- **THEN** the following colors SHALL be used:
  - text-primary: #E6EDF3 (main content)
  - text-secondary: #8B949E (labels, hints)
  - text-muted: #6E7681 (disabled, subtle)

#### Scenario: Semantic accent colors
- **WHEN** displaying status or actions
- **THEN** the following semantic colors SHALL be used:
  - accent-blue: #58A6FF (primary actions, active)
  - accent-green: #3FB950 (success, completed)
  - accent-yellow: #D29922 (warnings, in-progress)
  - accent-red: #F85149 (errors, canceled)
  - accent-purple: #A371F7 (AI/special indicators)
