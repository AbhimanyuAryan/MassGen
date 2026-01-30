## ADDED Requirements

### Requirement: Shared TUI Host Composition
The TUI SHALL compose core layout using shared host widgets for both main and subagent views.

#### Scenario: Shared timeline host used in main and subagent views
- **WHEN** the main TUI and subagent TUI render timeline content
- **THEN** both use the same TimelineHost implementation for pinned content, timeline, and final answer layout

#### Scenario: Shared header host used in main and subagent views
- **WHEN** the main TUI and subagent TUI render header/status content
- **THEN** both use the same HeaderHost implementation for tabs, session info, and status indicators

### Requirement: Unified Special Tool Routing
The TUI SHALL route special tool outputs (planning, reminders, injections, subagent spawning) through shared helpers so behavior is identical in main and subagent views.

#### Scenario: Planning tool updates pinned task plan in both views
- **WHEN** a planning MCP tool returns task data
- **THEN** the pinned task plan updates identically in main and subagent TUIs

#### Scenario: Reminder content is attached consistently
- **WHEN** a reminder or task priority update is emitted
- **THEN** it attaches to the pinned task plan (if present) in both views

### Requirement: Unified Event Attribution
The TUI SHALL apply a shared event filtering/attribution strategy for agent-specific views.

#### Scenario: Tool calls are attributed to the correct inner agent
- **WHEN** tool call events include agent attribution or tool_call_id mappings
- **THEN** the subagent view shows the tool calls only under the correct inner agent tab

### Requirement: Horizontal Subagent Overview Card
The TUI SHALL display a horizontal subagent overview card that splits subagents into per-agent columns.

#### Scenario: Per-agent columns with current tool highlight
- **WHEN** subagent status is displayed in the main timeline
- **THEN** each agent column shows a compact summary line above the tool lines, with the current tool prominently and 1-2 recent tools in a faded style

#### Scenario: Task plan summary in each column
- **WHEN** a subagent has an active task plan
- **THEN** the column shows a compact progress summary (e.g., "3/7 done") above the tool lines

#### Scenario: Horizontal scroll for more agents
- **WHEN** the number of subagents exceeds available width
- **THEN** the overview card uses horizontal scrolling to access additional agent columns

### Requirement: Right-Panel Subagent Detail Entry
The TUI SHALL open subagent details in the right panel and deprecate the modal entry path.

#### Scenario: Column click opens right-panel view
- **WHEN** a user activates a subagent column in the overview card
- **THEN** the subagent view opens in the right panel with a back action to return to the main timeline
