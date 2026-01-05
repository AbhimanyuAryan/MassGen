# Subagent Orchestration

## ADDED Requirements

### Requirement: Path Structure Understanding

Subagents have two relevant directory structures:

1. **Runtime workspace** (`.massgen/workspaces/workspace{N}_{hash}/subagents/{id}/workspace/`)
   - Where the subagent actually executes
   - May be cleaned up after completion
   - Contains agent workspaces like `agent_1_{hash}/`

2. **Log directory** (`.massgen/massgen_logs/log_{timestamp}/turn_1/attempt_1/subagents/{id}/`)
   - Persists after completion
   - Contains `full_logs/status.json` with orchestrator state (phase, votes, costs, historical_workspaces)
   - Contains `full_logs/{agentId}/{timestamp}/answer.txt` for each agent's answer snapshot
   - Contains `workspace/` symlink or copy of runtime workspace files

The recovery logic MUST check the **log directory** (`log_path` parameter) for `full_logs/status.json` since this is where the orchestrator writes its state. The runtime workspace may be cleaned up by the time recovery runs.

#### Answer Location Priority

When extracting answers, the system SHALL check locations in this order:
1. `log_path/full_logs/{agentId}/{timestamp}/answer.txt` - Answer snapshots in log directory
2. Parent of `workspacePath` from `historical_workspaces` - Runtime snapshot location
3. Inside `workspacePath` - Agent workspace files

The `historical_workspaces` in status.json contains:
- `agentId`: Agent identifier (e.g., `research_agent_1`)
- `answerLabel`: Vote-compatible label (e.g., `agent2.1`)
- `timestamp`: Snapshot timestamp (e.g., `20260102_190131_938811`)
- `workspacePath`: Path to agent workspace (may point to cleaned-up runtime directory)

### Requirement: Cancellation Recovery

The system SHALL recover completed work from cancelled subagents by reading the subagent's log directory before returning a cancellation response. This follows the same graceful selection pattern used by the orchestrator's `_handle_orchestrator_timeout()`.

#### Scenario: Subagent cancelled after full completion (presentation phase)
- **GIVEN** a subagent's `status.json` has `coordination.phase` set to `presentation`
- **AND** `results.winner` identifies the winning agent
- **WHEN** the subagent is cancelled due to timeout
- **THEN** the system SHALL extract the winner's answer from the workspace
- **AND** the status SHALL be `completed_but_timeout`
- **AND** the `success` field SHALL be `true`

#### Scenario: Subagent cancelled during voting (enforcement phase)
- **GIVEN** a subagent's `status.json` has `coordination.phase` set to `enforcement`
- **AND** at least one agent has submitted an answer
- **WHEN** the subagent is cancelled due to timeout
- **THEN** the system SHALL select an answer using the same logic as `_determine_final_agent_from_votes()` (most votes, ties broken by registration order)
- **AND** the status SHALL be `partial`

#### Scenario: Subagent cancelled with answers but no votes
- **GIVEN** a subagent's `status.json` has agents with answers but no votes recorded
- **WHEN** the subagent is cancelled due to timeout
- **THEN** the system SHALL return the first registered agent's answer
- **AND** the status SHALL be `partial`

#### Scenario: Subagent cancelled with no recoverable answer
- **GIVEN** a subagent has no `status.json` or no agents have submitted answers
- **WHEN** the subagent is cancelled due to timeout
- **THEN** the system SHALL return `timeout` status with `answer: null`
- **AND** the `success` field SHALL be `false`
- **AND** the `workspace_path` SHALL still be provided so the parent agent can inspect partial work

### Requirement: Workspace Access

The system SHALL always provide the workspace path in cancellation responses, regardless of whether an answer was recovered. This enables parent agents to inspect logs, partial files, and debug information.

#### Scenario: Workspace path always returned
- **GIVEN** a subagent was spawned and created a workspace
- **WHEN** the subagent is cancelled for any reason (timeout, error, cancellation)
- **THEN** the response SHALL include `workspace_path` pointing to the subagent's workspace directory

#### Scenario: Parent agent can read workspace files
- **GIVEN** a subagent returned with `answer: null` but `workspace_path` is set
- **WHEN** the parent agent uses filesystem tools to read files in the workspace
- **THEN** the parent agent SHALL be able to access any files created by the subagent

### Requirement: Token Usage Preservation

The system SHALL always return accurate token usage for cancelled subagents by reading cost data from the workspace's `status.json`.

#### Scenario: Token usage extracted from status.json
- **GIVEN** a subagent's `status.json` has `costs.total_input_tokens`, `costs.total_output_tokens`, and `costs.total_estimated_cost`
- **WHEN** the subagent is cancelled
- **THEN** the response SHALL include `token_usage` with `input_tokens`, `output_tokens`, and `estimated_cost` populated from the status file

#### Scenario: No cost data available
- **GIVEN** a subagent has no `status.json` or no `costs` section
- **WHEN** the subagent is cancelled
- **THEN** the response SHALL include empty `token_usage: {}`

### Requirement: Completion Percentage Reporting

The system SHALL include completion percentage in cancellation responses when available from the subagent's `status.json`.

#### Scenario: Completion percentage available
- **GIVEN** a subagent's `status.json` has `coordination.completion_percentage`
- **WHEN** the subagent is cancelled
- **THEN** the response SHALL include `completion_percentage` field with the value from status.json

#### Scenario: Completion percentage unavailable
- **GIVEN** a subagent has no `coordination.completion_percentage` in `status.json`
- **WHEN** the subagent is cancelled
- **THEN** the response SHALL omit the `completion_percentage` field

### Requirement: Status File Consistency

The system SHALL write the correct status to the outer `status.json` file based on recovery results, not hardcode "timeout" or "failed".

#### Scenario: Status reflects recovery result
- **GIVEN** a subagent times out
- **AND** recovery successfully extracts a complete answer
- **WHEN** the system writes the outer `status.json`
- **THEN** the status SHALL be `completed_but_timeout` (not `timeout` or `failed`)
- **AND** the `token_usage` SHALL contain the recovered cost data
- **AND** the `answer` SHALL contain the recovered answer

#### Scenario: Partial recovery status
- **GIVEN** a subagent times out
- **AND** recovery finds partial work but no complete answer
- **WHEN** the system writes the outer `status.json`
- **THEN** the status SHALL be `partial` (not `failed`)

#### Scenario: No recovery status
- **GIVEN** a subagent times out
- **AND** recovery finds no usable work
- **WHEN** the system writes the outer `status.json`
- **THEN** the status SHALL be `timeout`

### Requirement: Configurable Timeout Bounds

The system SHALL allow YAML configuration of minimum and maximum timeout values, instead of using hardcoded constants.

#### Scenario: Timeout clamping
- **GIVEN** a YAML config with `subagent_min_timeout: 60` and `subagent_max_timeout: 600`
- **WHEN** a timeout value is applied to a subagent
- **THEN** the value SHALL be clamped to the `[60, 600]` range
- **AND** values below 60 SHALL become 60
- **AND** values above 600 SHALL become 600

#### Scenario: Default timeout bounds
- **GIVEN** no custom timeout bounds in YAML config
- **WHEN** a subagent is spawned
- **THEN** the system SHALL use default bounds: min=60, max=600, default=300
