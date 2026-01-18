## ADDED Requirements

### Requirement: TUI Mode State
The system SHALL maintain a centralized mode state in the Textual TUI that tracks plan mode, agent mode, refinement mode, and override state.

#### Scenario: Mode state initialization
- **WHEN** the TUI starts
- **THEN** mode state initializes with defaults: normal plan mode, multi-agent mode, refinement enabled

#### Scenario: Mode state generates orchestrator overrides
- **WHEN** a turn is submitted
- **THEN** mode state generates appropriate config overrides based on current settings

### Requirement: Mode Bar Widget
The system SHALL display a Mode Bar widget above the input area containing toggles for plan mode, agent mode, and refinement mode.

#### Scenario: Mode bar visibility
- **WHEN** the TUI is running
- **THEN** the Mode Bar is visible above the input area with clickable toggles

#### Scenario: Mode bar disabled during execution
- **WHEN** agents are executing
- **THEN** mode toggles are disabled to prevent inconsistent state

### Requirement: Plan Mode
The system SHALL support a plan mode where queries create plans for approval before execution.

#### Scenario: Enter plan mode
- **WHEN** user presses Shift+Tab
- **THEN** plan mode is activated and Mode Bar indicates plan mode is on

#### Scenario: Plan mode submission
- **WHEN** user submits a query in plan mode
- **THEN** the system runs planning phase (--plan internally)
- **AND** displays a plan approval modal with plan preview

#### Scenario: Plan approval with additions
- **WHEN** user approves plan with additional instructions
- **THEN** the system transitions to execute mode
- **AND** runs execute-plan with the approved plan and additions

#### Scenario: Plan execution display
- **WHEN** executing an approved plan
- **THEN** the TUI shows plan directory and "Executing Plan" status

### Requirement: Agent Mode Toggle
The system SHALL support switching between single-agent and multi-agent modes via the Mode Bar.

#### Scenario: Single-agent mode activation
- **WHEN** user switches to single-agent mode
- **THEN** one agent is active based on tab bar selection
- **AND** other agent tabs are greyed out (disabled visual)

#### Scenario: Tab bar agent selection
- **WHEN** user clicks a tab in single-agent mode
- **THEN** that agent becomes the active single agent
- **AND** other tabs remain greyed out

#### Scenario: Context preservation across agent switches
- **WHEN** user switches active agent between turns in single-agent mode
- **THEN** the new agent has access to full conversation history

### Requirement: Refinement Mode Toggle
The system SHALL support enabling/disabling refinement via the Mode Bar.

#### Scenario: Refinement off with single agent
- **WHEN** refinement is disabled and agent mode is single
- **THEN** voting is skipped entirely (skip_voting=True)
- **AND** agent goes directly from answer to presentation

#### Scenario: Refinement off with multi-agent
- **WHEN** refinement is disabled and agent mode is multi
- **THEN** max_new_answers_per_agent is set to 1
- **AND** agents vote after first answer

#### Scenario: Single agent with refinement on
- **WHEN** refinement is enabled and agent mode is single
- **THEN** voting is available (vote = "I'm done refining")
- **AND** agent can choose between new_answer or vote

### Requirement: Human Override
The system SHALL allow users to override the voted winner after voting completes but before final presentation.

#### Scenario: Override availability
- **WHEN** voting completes
- **THEN** TUI shows "Press Ctrl+O to override, Enter to continue" notification

#### Scenario: Override modal display
- **WHEN** user presses Ctrl+O after voting
- **THEN** OverrideModal displays all agents' recent answers with previews

#### Scenario: Override selection
- **WHEN** user selects a different agent in OverrideModal
- **THEN** that agent is set as the presenter
- **AND** that agent does the final presentation

### Requirement: Skip Voting Configuration
The orchestrator SHALL support a skip_voting config flag to bypass vote tool injection.

#### Scenario: Skip voting enabled
- **WHEN** skip_voting is True
- **THEN** vote tool is not injected into agent tools
- **AND** enforcement does not require vote tool call
- **AND** agent proceeds directly to presentation after new_answer
