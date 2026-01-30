## ADDED Requirements

### Requirement: Unified Event Rendering Pipeline
The TUI SHALL render timeline content exclusively from structured MassGen events using `ContentProcessor.process_event()` for both main and subagent views. The stream-chunk parsing path (`_handle_stream_chunk()`) SHALL be removed.

#### Scenario: Main and subagent views render identical output
- **WHEN** the main TUI and a subagent view are given the same ordered event sequence
- **THEN** both views render the same timeline cards and text content in the same order

#### Scenario: Live event streaming updates the timeline
- **WHEN** new events are emitted during an active run
- **THEN** the TUI updates the timeline via the event-driven path without raw stream parsing

#### Scenario: All content types are emitted as structured events
- **WHEN** an agent produces thinking, text, tool_start, tool_complete, or status content
- **THEN** a corresponding structured event is emitted via `EventEmitter` and consumed by `ContentProcessor.process_event()`

### Requirement: Complete Event Emission
`chat_agent.py` and backend streaming paths SHALL emit structured events via `EventEmitter` for all timeline-relevant content types: thinking, text, tool_start, tool_complete, status, round_start, and final_answer.

#### Scenario: Event emission covers all content types
- **WHEN** a full agent run completes
- **THEN** the `events.jsonl` (or in-memory event bus) contains structured events for every piece of content that was previously only available via `StreamChunk` parsing

### Requirement: Consistent Tool Filtering
Tool filtering logic (including `is_filtered_tool` and `is_planning_tool` exemptions) SHALL be identical regardless of whether content arrives via the main or subagent rendering path.

#### Scenario: TaskPlanCard renders consistently
- **WHEN** a `task_plan` tool call is emitted
- **THEN** it renders as a `TaskPlanCard` in both main and subagent views, regardless of the rendering path

### Requirement: Subagent View Parity
The subagent view SHALL use the same timeline rendering behavior and formatting as the main TUI for tools, thinking, status, and final answer content.

#### Scenario: Tool and thinking content match main TUI
- **WHEN** a subagent emits tool_start/tool_complete and thinking/text events
- **THEN** the subagent view displays the same tool cards and thinking/text styles as the main TUI

### Requirement: Subagent Inner-Agent Tabs
The subagent view SHALL display inner-agent tabs with agent_id and model name and allow cycling/filtering the timeline by inner agent.

#### Scenario: Inner-agent tabs render with model names
- **WHEN** execution metadata includes multiple inner agents with model names
- **THEN** the subagent view shows a tab for each inner agent with its name and model

#### Scenario: Selecting an inner agent filters timeline
- **WHEN** a user selects an inner-agent tab
- **THEN** the timeline updates to show only events for that agent
