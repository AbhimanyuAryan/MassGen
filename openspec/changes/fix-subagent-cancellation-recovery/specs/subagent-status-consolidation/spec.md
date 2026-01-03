# Subagent Status File Consolidation

## Problem Statement

Currently, subagents create two separate `status.json` files:

1. **Outer status.json** at `subagents/{id}/status.json` - Written by `SubagentManager._write_status()`
2. **Inner status.json** at `subagents/{id}/full_logs/status.json` - Written by subagent's Orchestrator

This duplication causes:
- **Sync bugs**: Outer file overwrites recovered data with stale "timeout"/"failed" status
- **Data inconsistency**: Outer has simple status, inner has rich coordination data
- **Maintenance burden**: Two code paths to update and keep in sync
- **Confusion**: Users/developers unsure which file to trust

## Solution

Consolidate to a **single authoritative status file**: the inner `full_logs/status.json` written by the Orchestrator.

### REMOVED Requirements

#### Requirement: Remove Outer status.json Writing

The system SHALL NOT write a separate outer `status.json` file in `subagents/{id}/`.

##### Scenario: No outer status.json created
- **GIVEN** a subagent is spawned
- **WHEN** the subagent executes
- **THEN** the system SHALL NOT create `subagents/{id}/status.json`
- **AND** the system SHALL only create `subagents/{id}/full_logs/status.json` via the Orchestrator

##### Scenario: _write_status removed or no-op
- **GIVEN** the `SubagentManager._write_status()` method exists
- **WHEN** implementation is updated
- **THEN** the method SHALL be removed or converted to a no-op
- **AND** all call sites SHALL be removed

### ADDED Requirements

#### Requirement: Read Status from Inner File

All status queries SHALL read from the inner `full_logs/status.json`.

##### Scenario: check_subagent_status reads from full_logs
- **GIVEN** a model calls `check_subagent_status(subagent_id)`
- **WHEN** the system retrieves status
- **THEN** it SHALL read from `subagents/{id}/full_logs/status.json`
- **AND** it SHALL return a simplified view suitable for the model

##### Scenario: get_subagent_status reads from full_logs
- **GIVEN** Python code calls `manager.get_subagent_status(subagent_id)`
- **WHEN** the system retrieves status
- **THEN** it SHALL read from `subagents/{id}/full_logs/status.json`

##### Scenario: Recovery reads from full_logs
- **GIVEN** a subagent times out
- **WHEN** the system attempts recovery
- **THEN** it SHALL read from `subagents/{id}/full_logs/status.json`
- **AND** this is already the current behavior (no change needed)

#### Requirement: Simplified Status View for Models

When returning status to models, the system SHALL transform the rich Orchestrator status into a simplified view.

##### Scenario: Status transformation
- **GIVEN** the inner `full_logs/status.json` contains:
  ```json
  {
    "costs": {"total_input_tokens": 50000, "total_output_tokens": 3000, "total_estimated_cost": 0.05},
    "coordination": {"phase": "enforcement", "completion_percentage": 75},
    "agents": {...},
    "results": {"winner": null, "votes": {"agent2.1": 1}}
  }
  ```
- **WHEN** the model queries status via `check_subagent_status`
- **THEN** the system SHALL return:
  ```json
  {
    "subagent_id": "research",
    "status": "running",
    "phase": "enforcement",
    "completion_percentage": 75,
    "token_usage": {"input_tokens": 50000, "output_tokens": 3000, "estimated_cost": 0.05},
    "elapsed_seconds": 192.5
  }
  ```

##### Scenario: Derive status from coordination phase
- **GIVEN** the inner status has `coordination.phase`
- **WHEN** deriving the simplified `status` field
- **THEN** the mapping SHALL be:
  | coordination.phase | Derived status |
  |-------------------|----------------|
  | `initial_answer` | `running` |
  | `enforcement` | `running` |
  | `presentation` | `running` |
  | (file missing) | `pending` |
  | (with error) | `failed` |

#### Requirement: Handle Missing Status File

The system SHALL gracefully handle cases where `full_logs/status.json` doesn't exist yet.

##### Scenario: Status file not yet created
- **GIVEN** a subagent was just spawned
- **AND** the Orchestrator hasn't written `full_logs/status.json` yet
- **WHEN** the model queries status
- **THEN** the system SHALL return status from in-memory state:
  ```json
  {
    "subagent_id": "research",
    "status": "pending",
    "task": "Research movies...",
    "started_at": "2026-01-02T21:48:21"
  }
  ```

#### Requirement: SubagentResult Unchanged

The `SubagentResult` returned by `spawn_subagents` SHALL remain unchanged.

##### Scenario: spawn_subagents return value
- **GIVEN** `spawn_subagents` completes (success or timeout)
- **WHEN** results are returned to the model
- **THEN** the return format SHALL remain:
  ```json
  {
    "subagent_id": "research",
    "status": "completed" | "completed_but_timeout" | "partial" | "timeout" | "error",
    "success": true | false,
    "answer": "...",
    "workspace": "/path/to/workspace",
    "execution_time_seconds": 145.3,
    "token_usage": {...},
    "completion_percentage": 100
  }
  ```
- **AND** this data comes from `SubagentResult.to_dict()`, not from any status file

### MODIFIED Requirements

#### Requirement: Log Directory Structure

The subagent log directory structure SHALL be simplified.

##### Scenario: New directory structure
- **GIVEN** a subagent executes
- **WHEN** logs are written
- **THEN** the structure SHALL be:
  ```
  subagents/{id}/
  ├── conversation.jsonl          # Conversation history (unchanged)
  ├── workspace/                   # Symlink to runtime workspace (unchanged)
  └── full_logs/
      ├── status.json             # Single authoritative status (Orchestrator writes)
      ├── {agent_1_id}/
      │   └── {timestamp}/
      │       ├── answer.txt
      │       └── workspace/
      └── {agent_2_id}/
          └── ...
  ```
- **AND** there SHALL be no `subagents/{id}/status.json` file

## Migration

### Backward Compatibility

- Tools/scripts reading outer `status.json` will need updating
- The inner file location is already documented and used by recovery

### Implementation Steps

1. Remove `_write_status()` method and all call sites
2. Update `get_subagent_status()` to read from `full_logs/status.json`
3. Update `check_subagent_status` MCP tool to use updated `get_subagent_status()`
4. Add status derivation logic (phase → status mapping)
5. Handle missing file case with in-memory fallback
6. Update documentation

## Benefits

1. **Single source of truth**: No sync bugs possible
2. **Richer data available**: Full coordination state accessible
3. **Less code**: Remove `_write_status()` and sync logic
4. **Consistent**: Same file used for recovery and status queries
