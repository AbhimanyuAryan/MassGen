# Tasks: Add Hook Framework

## 1. Core Infrastructure ✅

- [x] 1.1 Extend `HookType` enum with `PRE_TOOL_USE` and `POST_TOOL_USE`
- [x] 1.2 Add `HookEvent` dataclass
- [x] 1.3 Enhance `HookResult` with new fields (backward compatible)
- [x] 1.4 Implement `PythonCallableHook` class
- [x] 1.5 Implement `ExternalCommandHook` class
- [x] 1.6 Implement `GeneralHookManager` class

## 2. Configuration ✅

- [x] 2.1 Add `_validate_hooks()` to config_validator.py
- [x] 2.2 Add "hooks" to excluded config params in base.py
- [x] 2.3 Add "hooks" to excluded params in api_params_handler_base.py

## 3. Integration ✅

- [x] 3.1 Add PreToolUse hook execution before tool calls
- [x] 3.2 Add PostToolUse hook execution after tool results
- [x] 3.3 Handle deny/ask decisions from PreToolUse
- [x] 3.4 Handle injection content from PostToolUse

## 4. Built-in Hooks ✅

- [x] 4.1 Create `MidStreamInjectionHook` built-in class
- [x] 4.2 Create `ReminderExtractionHook` built-in class

## 5. Testing & Documentation ✅

- [x] 5.1 Unit tests for PythonCallableHook
- [x] 5.2 Unit tests for ExternalCommandHook
- [x] 5.3 Unit tests for GeneralHookManager
- [x] 5.4 Unit tests for built-in hooks
- [x] 5.5 Example YAML config in massgen/configs/hooks/

## 6. Migration of Existing Patterns ✅

This phase migrates the existing ad-hoc injection patterns to use the hook framework,
removing duplicate code and unifying the approach.

### 6.1 Mid-Stream Injection Migration ✅

**Current state**: ~~`orchestrator.py:3977-4034`~~
- ~~Orchestrator defines `get_injection_content()` closure~~
- ~~Calls `backend.set_mid_stream_injection_callback(get_injection_content)`~~
- ~~Backend calls `self.get_mid_stream_injection()` in tool execution (line 1692)~~

**Target state** (IMPLEMENTED):
- Orchestrator creates `GeneralHookManager` with a `MidStreamInjectionHook`
- Sets callback on the hook: `hook.set_callback(get_injection_content)`
- Registers hook: `manager.register_global_hook(HookType.POST_TOOL_USE, hook)`
- Passes manager to backend: `backend.set_general_hook_manager(manager)`
- Remove `get_mid_stream_injection()` call from tool execution (hook handles it)

**Tasks**:
- [x] 6.1.1 Add imports to orchestrator: `GeneralHookManager`, `MidStreamInjectionHook`, `HookType`
- [x] 6.1.2 Create `_setup_hook_manager_for_agent()` method in orchestrator
- [x] 6.1.3 Move `get_injection_content()` logic into the new method
- [x] 6.1.4 Create `MidStreamInjectionHook` and register with manager
- [x] 6.1.5 Call `backend.set_general_hook_manager(manager)` instead of `set_mid_stream_injection_callback`
- [x] 6.1.6 Remove `get_mid_stream_injection()` call from `base_with_custom_tool_and_mcp.py:1691-1699`
- [x] 6.1.7 Remove `set_mid_stream_injection_callback` and `get_mid_stream_injection` methods from `base.py`

### 6.2 Reminder Extraction Migration ✅

**Current state**: ~~`base_with_custom_tool_and_mcp.py:1755-1799`~~
- ~~Inline code parses JSON tool results looking for "reminder" field~~
- ~~If found, injects as user message with `⚠️ SYSTEM REMINDER` header~~

**Target state** (IMPLEMENTED):
- `ReminderExtractionHook` registered as PostToolUse hook handles this
- Hook returns `inject: {content: formatted_reminder, strategy: "user_message"}`
- PostToolUse hook integration code handles the injection

**Tasks**:
- [x] 6.2.1 Register `ReminderExtractionHook` as a default PostToolUse hook in `_setup_hook_manager_for_agent()`
- [x] 6.2.2 Update `ReminderExtractionHook` to format reminders with `⚠️ SYSTEM REMINDER` header
- [x] 6.2.3 Remove inline reminder extraction code (lines 1755-1799)
- [x] 6.2.4 Unify reminder formatting (both use same `⚠️ SYSTEM REMINDER` header)

### 6.3 Cleanup Old Code ✅

- [x] 6.3.1 Remove `set_mid_stream_injection_callback` method from `base.py:825-839`
- [x] 6.3.2 Remove `get_mid_stream_injection` method from `base.py:841-848`
- [x] 6.3.3 Remove `_mid_stream_injection_callback` attribute initialization (not present)
- [x] 6.3.4 Update any other references to the old injection pattern
- [x] 6.3.5 Clean up orchestrator code that clears the callback (line 4624-4625)

### 6.4 Testing Migration ✅

- [x] 6.4.1 Unit tests for hook framework (32 tests passing)
- [x] 6.4.2 Unit test for `ReminderExtractionHook` with formatting
- [x] 6.4.3 Verify existing tests still pass (orchestrator, hook, backend tests)
- [x] 6.4.4 Created integration test script at `scripts/test_hook_backends.py`
- [x] 6.4.5 Added `--e2e` mode for end-to-end testing with real API calls

**E2E Testing Features**:
- `--e2e` flag runs tests with real API calls across all 5 standard backends
- Tests full hook flow: PreToolUse → tool execution → PostToolUse → injection
- Custom tool returns reminder field to verify ReminderExtractionHook
- Logging hooks verify PreToolUse and PostToolUse fire correctly
- Follow-up question verifies model actually received and understood injected reminder
- `--verbose` flag shows detailed hook execution logs

**Note**: Claude Code backend deferred - will handle hooks internally with a different API

## Migration Architecture

```
BEFORE:
┌─────────────┐         ┌─────────────┐         ┌─────────────────────┐
│ Orchestrator│─────────│   Backend   │─────────│ Tool Execution      │
└─────────────┘         └─────────────┘         └─────────────────────┘
       │                       │                         │
       │ set_mid_stream_       │ get_mid_stream_         │
       │ injection_callback()  │ injection()             │
       └───────────────────────┴─────────────────────────┘
                   Direct callback pattern

AFTER:
┌─────────────┐         ┌─────────────────┐         ┌─────────────────────┐
│ Orchestrator│─────────│ HookManager     │─────────│ Tool Execution      │
└─────────────┘         └─────────────────┘         └─────────────────────┘
       │                       │                         │
       │ set_general_          │ execute_hooks()         │
       │ hook_manager()        │ (POST_TOOL_USE)         │
       │                       │                         │
       │ MidStreamInjection    │ Returns injection       │
       │ Hook.set_callback()   │ via HookResult.inject   │
       └───────────────────────┴─────────────────────────┘
                   Unified hook pattern
```

## File Changes Summary

| File | Changes |
|------|---------|
| `massgen/orchestrator.py` | Add `_setup_hook_manager_for_agent()`, replace callback with hook manager |
| `massgen/backend/base.py` | Remove `set_mid_stream_injection_callback`, `get_mid_stream_injection` |
| `massgen/backend/base_with_custom_tool_and_mcp.py` | Remove `get_mid_stream_injection()` call, remove inline reminder code |
| `massgen/mcp_tools/hooks.py` | Enhance `ReminderExtractionHook` to handle MCP objects |

## Risks and Mitigations

1. **Risk**: Breaking existing multi-agent coordination
   - **Mitigation**: Run integration tests with multi-agent configs before/after

2. **Risk**: Reminder extraction regression (MCP vs custom tool handling)
   - **Mitigation**: Ensure `ReminderExtractionHook` handles both MCP `CallToolResult` and dict results

3. **Risk**: Hook execution order affecting injection timing
   - **Mitigation**: Mid-stream hook should be registered first to maintain current behavior
