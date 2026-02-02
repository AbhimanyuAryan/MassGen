## ADDED Requirements

### Requirement: Interactive Session Lifecycle
The system SHALL provide a persistent `InteractiveSession` class that manages conversations across multiple runs.

#### Scenario: Session initialization
- **WHEN** the TUI starts with `interactive_mode.enabled: true`
- **THEN** an `InteractiveSession` is created and becomes the primary entry point for user interactions

#### Scenario: Session persistence across runs
- **WHEN** a run completes and returns results
- **THEN** the `InteractiveSession` retains context and can reference previous run results in subsequent conversations

#### Scenario: Session context compaction
- **WHEN** the conversation exceeds the configured `threshold_tokens`
- **THEN** the system SHALL automatically summarize earlier context while preserving recent exchanges per `preserve_recent` config

### Requirement: Launch Run Tool
The system SHALL provide a `launch_run` workflow tool that allows the interactive agent to spawn MassGen runs with configurable agent modes, refinement settings, and planning options.

#### Scenario: Tool schema definition
- **WHEN** the interactive agent is initialized
- **THEN** it SHALL have access to a `launch_run` tool with parameters:
  - `task` (required): Description of what to accomplish
  - `context` (optional): Background information, constraints, or previous decisions
  - `agent_mode` (optional): "single" | "multi" - whether to use one agent or multiple (default: "multi")
  - `agents` (optional): List of specific agent IDs to use (defaults to all configured agents)
  - `refinement` (optional): true | false - whether to enable voting/refinement cycles (default: true for multi, false for single)
  - `planning_mode` (optional): true | false - if true, agents plan without executing actions (default: false)
  - `execute_after_planning` (optional): true | false - if planning_mode=true, whether to spawn a follow-up run to execute the plan (default: false)
  - `coordination_overrides` (optional): Additional config overrides for fine-grained control

#### Scenario: Single agent run
- **WHEN** the interactive agent invokes `launch_run` with `agent_mode: "single"`
- **THEN** the system SHALL spawn an orchestrator with one agent and skip multi-agent coordination overhead

#### Scenario: Multi-agent run with refinement
- **WHEN** the interactive agent invokes `launch_run` with `agent_mode: "multi"` and `refinement: true`
- **THEN** the system SHALL spawn an orchestrator where agents coordinate, vote, and refine answers

#### Scenario: Multi-agent run without refinement
- **WHEN** the interactive agent invokes `launch_run` with `agent_mode: "multi"` and `refinement: false`
- **THEN** the system SHALL spawn an orchestrator where agents work independently and the best initial answer wins

#### Scenario: Planning mode run
- **WHEN** the interactive agent invokes `launch_run` with `planning_mode: true`
- **THEN** agents SHALL describe their approach without executing actions, producing a plan rather than implementation

#### Scenario: Planning then execution
- **WHEN** the interactive agent invokes `launch_run` with `planning_mode: true` and `execute_after_planning: true`
- **THEN** after planning completes, the system SHALL automatically spawn a follow-up run to execute the winning plan

#### Scenario: Run execution via tool
- **WHEN** the interactive agent invokes `launch_run` with a task
- **THEN** the system SHALL spawn an orchestrator with the provided configuration and inject the task + context as the initial user message

#### Scenario: Results returned to agent
- **WHEN** a spawned run completes
- **THEN** the `RunResult` (final_answer, workspace_path, coordination_summary) SHALL be returned to the interactive agent for further processing

### Requirement: Interactive Agent System Prompt
The system SHALL reuse existing MassGen system prompt sections but exclude coordination-specific sections and add interactive orchestrator guidance.

#### Scenario: Reused system prompt sections
- **WHEN** the interactive agent's system prompt is built
- **THEN** it SHALL include standard MassGen sections that apply:
  - `AgentIdentitySection` (if custom identity configured)
  - `CoreBehaviorsSection` (default to action, parallel tools)
  - `SkillsSection` (if skills enabled)
  - `MemoryFilesystemSection` (if memory enabled)
  - `FilesystemWorkspaceSection` (if workspace configured)
  - `TaskPlanningSection` (if task planning enabled)
  - Model-specific guidance sections (GPT5, Grok, etc.)

#### Scenario: Excluded system prompt sections
- **WHEN** the interactive agent's system prompt is built
- **THEN** it SHALL NOT include coordination-specific sections:
  - `MassGenCoordinationSection` (vote/new_answer workflow)
  - `BroadcastCommunicationSection` (ask_others)
  - `VotingGuidanceSection` (voting criteria)
  - Any section that references `new_answer`, `vote`, or coordination primitives

#### Scenario: Added interactive orchestrator section
- **WHEN** the interactive agent's system prompt is built
- **THEN** it SHALL include an `InteractiveOrchestratorSection` explaining:
  - Its role as the entry point for MassGen
  - Available agents and their capabilities (from config)
  - When to use `launch_run` vs answer directly
  - How to configure runs (agent_mode, refinement, planning_mode)
  - How context flows to runs and results flow back

#### Scenario: No coordination tools
- **WHEN** the interactive agent's tool set is assembled
- **THEN** it SHALL NOT include `new_answer`, `vote`, or `ask_others` tools (those are for coordination agents only)

### Requirement: Run Approval Flow
The system SHALL optionally display an approval modal before executing a run when `require_approval: true`.

#### Scenario: Approval required
- **WHEN** the interactive agent calls `launch_run` and `require_approval: true`
- **THEN** the TUI SHALL display a modal showing the task, context, and selected agents, with Approve/Edit/Cancel buttons

#### Scenario: Approval granted
- **WHEN** the user clicks Approve in the modal
- **THEN** the run SHALL proceed with the displayed configuration

#### Scenario: Approval cancelled
- **WHEN** the user clicks Cancel in the modal
- **THEN** the system SHALL return a cancellation result to the interactive agent without executing the run

#### Scenario: Approval not required
- **WHEN** `require_approval: false`
- **THEN** runs SHALL execute immediately without showing the approval modal

### Requirement: Interactive Mode Configuration
The system SHALL support `orchestrator.interactive_mode` configuration section in YAML configs.

#### Scenario: Config structure
- **WHEN** a config file includes `orchestrator.interactive_mode`
- **THEN** the validator SHALL accept fields: `enabled` (bool), `require_approval` (bool), `backend` (optional backend config), `append_system_prompt` (optional string), `context_compaction` (optional object)

#### Scenario: Default values
- **WHEN** `interactive_mode` is specified but fields are omitted
- **THEN** defaults SHALL be: `enabled: true`, `require_approval: true`, `backend: null` (use first agent's backend), `context_compaction.enabled: true`

#### Scenario: Validation errors
- **WHEN** invalid values are provided (e.g., negative timeout)
- **THEN** the config validator SHALL report a clear error with location and suggestion

### Requirement: TUI Mode State Extension
The system SHALL extend `TuiModeState` to track interactive mode state.

#### Scenario: State fields
- **WHEN** `TuiModeState` is instantiated
- **THEN** it SHALL include: `interactive_mode` (bool), `interactive_session` (Optional[InteractiveSession]), `current_run_id` (Optional[str]), `pending_run_approval` (bool)

#### Scenario: Mode indicator
- **WHEN** interactive mode is active
- **THEN** the mode bar SHALL display a visual indicator showing interactive mode status

### Requirement: Context Flow Between Interactive and Runs
The system SHALL support one-way context flow from interactive session to spawned runs.

#### Scenario: Context injection
- **WHEN** a run is spawned via `launch_run`
- **THEN** the `context` parameter (if provided) SHALL be injected into the run's initial user message along with the `task`

#### Scenario: Results consumption
- **WHEN** a run completes
- **THEN** the interactive agent SHALL receive: `final_answer`, `workspace_path`, and `coordination_summary` (including votes, winner, rounds)

### Requirement: Project-Based Workspace
The system SHALL support a project-based workspace structure for managing context across runs.

#### Scenario: Workspace structure
- **WHEN** a project workspace is created
- **THEN** it SHALL contain: `CONTEXT.md` (project context), `filepaths.json` (key file descriptions), `runs/` (run log references), `deliverables/` (output files)

#### Scenario: Run association
- **WHEN** a run is executed within a project
- **THEN** the run logs SHALL be linked to the project's `runs/` directory

### Requirement: Interactive Agent Delegation Behavior
The interactive agent SHALL delegate complex work to multi-agent runs while handling simple tasks directly.

#### Scenario: Simple task handling
- **WHEN** a user asks a simple question that the interactive agent can answer directly
- **THEN** the agent SHALL respond without spawning a run

#### Scenario: Complex task delegation
- **WHEN** a user requests complex work requiring multi-agent coordination
- **THEN** the interactive agent SHALL use `launch_run` to delegate the work

#### Scenario: Context-efficient operation
- **WHEN** large outputs or files need to be passed between runs
- **THEN** the interactive agent SHALL summarize and filter context rather than passing everything verbatim
