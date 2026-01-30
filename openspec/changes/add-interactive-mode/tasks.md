# Interactive Mode Implementation Tasks

## 1. Core Infrastructure

- [ ] 1.1 Create `massgen/interactive_session.py` with `InteractiveSession` class
  - [ ] 1.1.1 Implement session lifecycle management
  - [ ] 1.1.2 Implement `chat()` async generator for message processing
  - [ ] 1.1.3 Implement `_handle_launch_run()` for tool call handling
  - [ ] 1.1.4 Implement `_execute_run()` for orchestrator spawning
  - [ ] 1.1.5 Implement run history tracking
  - [ ] 1.1.6 Implement context compaction for long sessions

- [ ] 1.2 Create `massgen/tool/workflow_toolkits/launch_run.py`
  - [ ] 1.2.1 Implement `LaunchRunToolkit` inheriting from `BaseToolkit`
  - [ ] 1.2.2 Define tool schema with all run configuration parameters:
    - `task` (required): Description of what to accomplish
    - `context` (optional): Background information, constraints
    - `agent_mode` (optional): "single" | "multi" (default: "multi")
    - `agents` (optional): List of specific agent IDs
    - `refinement` (optional): Enable voting/refinement (default: mode-dependent)
    - `planning_mode` (optional): Plan without executing (default: false)
    - `execute_after_planning` (optional): Auto-execute after planning (default: false)
    - `coordination_overrides` (optional): Fine-grained config overrides
  - [ ] 1.2.3 Support all API formats (claude, chat_completions, response)
  - [ ] 1.2.4 Register toolkit in `__init__.py`

- [ ] 1.3 Add `InteractiveOrchestratorSection` to `system_prompt_sections.py`
  - [ ] 1.3.1 Create section class that explains interactive orchestrator role
  - [ ] 1.3.2 Document available agents and their capabilities (from config)
  - [ ] 1.3.3 Explain when to use `launch_run` vs answer directly
  - [ ] 1.3.4 Document all run configuration options (agent_mode, refinement, planning_mode)
  - [ ] 1.3.5 Explain context flow to runs and result handling

- [ ] 1.4 Update `SystemMessageBuilder` for interactive mode
  - [ ] 1.4.1 Add method to build interactive agent system prompt
  - [ ] 1.4.2 Include standard sections: CoreBehaviors, Skills, Memory, Filesystem, TaskPlanning
  - [ ] 1.4.3 Exclude coordination sections: MassGenCoordination, Broadcast, VotingGuidance
  - [ ] 1.4.4 Add InteractiveOrchestratorSection

- [ ] 1.5 Add config validation for `interactive_mode` section
  - [ ] 1.5.1 Add `InteractiveModeConfig` dataclass in `agent_config.py`
  - [ ] 1.5.2 Add `_validate_interactive_mode()` to `config_validator.py`
  - [ ] 1.5.3 Update YAML schema documentation

## 2. TUI Integration

- [ ] 2.1 Extend `TuiModeState` in `tui_modes.py`
  - [ ] 2.1.1 Add `interactive_mode: bool` field
  - [ ] 2.1.2 Add `interactive_session: Optional[InteractiveSession]` field
  - [ ] 2.1.3 Add `current_run_id: Optional[str]` field
  - [ ] 2.1.4 Add `pending_run_approval: bool` field
  - [ ] 2.1.5 Update `get_orchestrator_overrides()` for interactive mode

- [ ] 2.2 Create `massgen/frontend/displays/textual/run_approval_modal.py`
  - [ ] 2.2.1 Implement modal UI with task/context display
  - [ ] 2.2.2 Add agent list display
  - [ ] 2.2.3 Add Approve/Edit/Cancel buttons
  - [ ] 2.2.4 Handle button press events
  - [ ] 2.2.5 Return approval result to parent

- [ ] 2.3 Update `textual_terminal_display.py`
  - [ ] 2.3.1 Initialize `InteractiveSession` on mount when enabled
  - [ ] 2.3.2 Handle run approval callbacks
  - [ ] 2.3.3 Show run progress during execution
  - [ ] 2.3.4 Transition UI between interactive and running states
  - [ ] 2.3.5 Handle `InteractiveModeChanged` messages

- [ ] 2.4 Update `mode_bar.py`
  - [ ] 2.4.1 Add visual indicator for interactive mode state
  - [ ] 2.4.2 Add toggle for interactive mode on/off
  - [ ] 2.4.3 Show current session status

## 3. CLI & Polish

- [ ] 3.1 Update `cli.py`
  - [ ] 3.1.1 Add `--interactive` flag (default behavior when TUI enabled)
  - [ ] 3.1.2 Create `InteractiveSession` when flag enabled
  - [ ] 3.1.3 Pass session to TUI initialization

- [ ] 3.2 Add context compaction
  - [ ] 3.2.1 Implement conversation length threshold detection
  - [ ] 3.2.2 Implement automatic summarization for long conversations
  - [ ] 3.2.3 Preserve critical context during compaction

- [ ] 3.3 Write tests
  - [ ] 3.3.1 Unit test: `test_launch_run_tool_schema()` - all parameters present
  - [ ] 3.3.2 Unit test: `test_interactive_session_initialization()`
  - [ ] 3.3.3 Unit test: `test_context_compaction_trigger()`
  - [ ] 3.3.4 Unit test: `test_run_config_single_agent()` - agent_mode="single"
  - [ ] 3.3.5 Unit test: `test_run_config_multi_no_refine()` - refinement=false
  - [ ] 3.3.6 Unit test: `test_run_config_planning_mode()` - planning_mode=true
  - [ ] 3.3.7 Integration test: `test_interactive_launches_run()`
  - [ ] 3.3.8 Integration test: `test_context_passed_correctly()`
  - [ ] 3.3.9 Integration test: `test_results_returned()`
  - [ ] 3.3.10 Integration test: `test_planning_then_execute()`

## 4. Documentation

- [ ] 4.1 Add example configs
  - [ ] 4.1.1 Create `massgen/configs/interactive/basic_interactive.yaml`
  - [ ] 4.1.2 Create `massgen/configs/interactive/code_review_interactive.yaml`

- [ ] 4.2 Update user guide
  - [ ] 4.2.1 Add interactive mode section to docs

## 5. Future Enhancements (Deferred)

These are tracked but out of scope for initial implementation:

- [ ] 5.1 Meta-level task planning with high-level task lists
- [ ] 5.2 Parallel run orchestration
- [ ] 5.3 `ask_others` integration (pending broadcast refactoring)
- [ ] 5.4 Native MassGen project-based workspace support
