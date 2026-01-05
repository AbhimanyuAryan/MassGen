# Hook Framework Specification

## ADDED Requirements

### Requirement: Hook Event Types

The system SHALL support `PreToolUse` and `PostToolUse` hook events for intercepting tool execution.

#### Scenario: PreToolUse fires before tool execution
- **WHEN** an agent invokes a tool (MCP or custom)
- **THEN** all registered PreToolUse hooks matching the tool name SHALL execute before the tool runs

#### Scenario: PostToolUse fires after tool execution
- **WHEN** a tool execution completes successfully
- **THEN** all registered PostToolUse hooks matching the tool name SHALL execute with the tool result

### Requirement: Global Hook Registration via YAML

The system SHALL support registering hooks at the top-level that apply to ALL agents.

#### Scenario: Register global Python callable hook
- **WHEN** config contains top-level `hooks.PreToolUse` with `handler: "module.function"` and `type: "python"`
- **THEN** the system SHALL register the hook for ALL agents

#### Scenario: Register global external command hook
- **WHEN** config contains top-level `hooks.PostToolUse` with `handler: "path/to/script.py"` and `type: "command"`
- **THEN** the system SHALL register the hook for ALL agents

### Requirement: Per-Agent Hook Registration via YAML

The system SHALL support registering hooks per-agent that can extend or override global hooks.

#### Scenario: Per-agent hook extends global hooks
- **WHEN** agent config contains `backend.hooks.PreToolUse` with additional hooks
- **THEN** the agent SHALL execute BOTH global hooks AND per-agent hooks

#### Scenario: Per-agent hook overrides global hooks
- **WHEN** agent config contains `backend.hooks.PreToolUse` with `override: true`
- **THEN** the agent SHALL execute ONLY per-agent hooks (global hooks disabled for this event)

### Requirement: Pattern-Based Hook Matching

Hooks SHALL support pattern matching on tool names using glob syntax.

#### Scenario: Wildcard matching
- **WHEN** a hook has `matcher: "*"`
- **THEN** the hook SHALL execute for all tool calls

#### Scenario: Specific tool matching
- **WHEN** a hook has `matcher: "Write|Edit"`
- **THEN** the hook SHALL execute only for Write or Edit tools

#### Scenario: No matcher defaults to all
- **WHEN** a hook has no `matcher` field
- **THEN** the hook SHALL match all tools

### Requirement: PreToolUse Can Block or Modify

PreToolUse hooks SHALL be able to block tool execution or modify tool input.

#### Scenario: Hook denies tool execution
- **WHEN** a PreToolUse hook returns `decision: "deny"`
- **THEN** the tool SHALL NOT execute AND the agent SHALL receive an error message with the reason

#### Scenario: Hook modifies tool input
- **WHEN** a PreToolUse hook returns `updated_input: {...}`
- **THEN** the tool SHALL execute with the modified input

#### Scenario: Hook allows execution
- **WHEN** a PreToolUse hook returns `decision: "allow"` or empty result
- **THEN** the tool SHALL execute normally

### Requirement: PostToolUse Can Inject Content

PostToolUse hooks SHALL be able to inject content into the tool result.

#### Scenario: Hook injects into tool result
- **WHEN** a PostToolUse hook returns `inject: {content: "...", strategy: "tool_result"}`
- **THEN** the content SHALL be appended to the tool result

#### Scenario: Hook injects as user message
- **WHEN** a PostToolUse hook returns `inject: {content: "...", strategy: "user_message"}`
- **THEN** a user message with the content SHALL be added after the tool result

### Requirement: External Command Hook Protocol

External command hooks SHALL communicate via JSON stdin/stdout protocol.

#### Scenario: Hook receives event via stdin
- **WHEN** an external command hook executes
- **THEN** it SHALL receive a JSON-encoded HookEvent on stdin

#### Scenario: Hook returns result via stdout
- **WHEN** an external command hook completes
- **THEN** it SHALL write a JSON-encoded HookResult to stdout

#### Scenario: Environment variables provided
- **WHEN** an external command hook executes
- **THEN** the environment SHALL include `MASSGEN_HOOK_TYPE`, `MASSGEN_TOOL_NAME`, `MASSGEN_SESSION_ID`, `MASSGEN_AGENT_ID`

### Requirement: Hook Timeout Enforcement

Hooks SHALL have configurable timeouts with sensible defaults.

#### Scenario: Default timeout
- **WHEN** a hook has no `timeout` field
- **THEN** the hook SHALL timeout after 30 seconds

#### Scenario: Custom timeout
- **WHEN** a hook has `timeout: 60`
- **THEN** the hook SHALL timeout after 60 seconds

#### Scenario: Timeout behavior
- **WHEN** a hook exceeds its timeout
- **THEN** the hook SHALL be terminated AND execution SHALL continue (fail open)

### Requirement: Hook Error Handling

Hook errors SHALL be handled gracefully without crashing the agent.

#### Scenario: Python hook raises exception
- **WHEN** a Python callable hook raises an exception
- **THEN** the error SHALL be logged AND execution SHALL continue (fail open)

#### Scenario: External hook returns invalid JSON
- **WHEN** an external command hook returns invalid JSON
- **THEN** the error SHALL be logged AND execution SHALL continue (fail open)

#### Scenario: Import error for Python hook
- **WHEN** a Python callable hook cannot be imported
- **THEN** an error SHALL be logged AND the tool call SHALL be denied (fail closed)

### Requirement: Multiple Hook Aggregation

When multiple hooks match, their results SHALL be aggregated.

#### Scenario: Any deny results in denial
- **WHEN** multiple PreToolUse hooks match AND any returns `decision: "deny"`
- **THEN** the tool call SHALL be denied

#### Scenario: Modified inputs chain
- **WHEN** multiple PreToolUse hooks return `updated_input`
- **THEN** each hook SHALL receive the previously modified input

#### Scenario: Multiple injections combine
- **WHEN** multiple PostToolUse hooks return `inject`
- **THEN** all injection content SHALL be included
