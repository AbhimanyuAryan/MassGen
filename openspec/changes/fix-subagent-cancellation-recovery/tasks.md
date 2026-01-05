# Tasks: Fix Subagent Cancellation Recovery

## 1. Write Unit Tests First (TDD)
- [x] 1.1 Write tests for `SubagentResult` new factory methods and status values
- [x] 1.2 Write tests for workspace status.json parsing (various completion states)
- [x] 1.3 Write tests for answer extraction from workspace (answer.txt, winner selection)
- [x] 1.4 Write tests for token usage extraction from status.json costs
- [x] 1.5 Write tests for timeout recovery in SubagentManager

## 2. SubagentResult Model Changes (`massgen/subagent/models.py`)
- [x] 2.1 Add `completion_percentage` optional field to SubagentResult
- [x] 2.2 Extend status Literal to include `completed_but_timeout` and `partial`
- [x] 2.3 Add `create_timeout_with_recovery()` factory method
- [x] 2.4 Ensure `to_dict()` includes new fields

## 3. Workspace Recovery Logic (`massgen/subagent/manager.py`)
- [x] 3.1 Add `_extract_status_from_workspace()` to read status.json
- [x] 3.2 Add `_extract_answer_from_workspace()` to read answer.txt or select from agents
- [x] 3.3 Add `_extract_costs_from_status()` to get token usage
- [x] 3.4 Add `_create_timeout_result_with_recovery()` to create recovered results

## 4. Integration
- [x] 4.1 Wire up recovery in `_execute_subagent()` timeout handler
- [x] 4.2 Wire up recovery in `_execute_with_orchestrator()` timeout handler
- [x] 4.3 Wire up recovery in `_execute_with_orchestrator()` cancellation handler
- [x] 4.4 Wire up recovery in `spawn_subagent()` timeout handler
- [x] 4.5 Wire up recovery in `spawn_parallel()` background task timeout handler

## 5. Validation
- [x] 5.1 Run all existing subagent tests to ensure no regression (35 tests pass)
- [x] 5.2 Run new cancellation recovery tests (22 tests pass)
- [x] 5.3 Validate with `openspec validate --strict`
- [ ] 5.4 Manual test with a config that triggers subagent timeout (optional)

## 6. Documentation
- [x] 6.1 Update MCP tool docstring with new status values and recovery behavior
- [x] 6.2 Update system prompt result format documentation
