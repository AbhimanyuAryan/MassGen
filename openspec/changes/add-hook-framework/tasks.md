# Tasks: Add Hook Framework

## 1. Core Infrastructure

- [x] 1.1 Extend `HookType` enum with `PRE_TOOL_USE` and `POST_TOOL_USE`
- [x] 1.2 Add `HookEvent` dataclass
- [x] 1.3 Enhance `HookResult` with new fields (backward compatible)
- [x] 1.4 Implement `PythonCallableHook` class
- [x] 1.5 Implement `ExternalCommandHook` class
- [x] 1.6 Implement `GeneralHookManager` class

## 2. Configuration

- [x] 2.1 Add `_validate_hooks()` to config_validator.py
- [ ] 2.2 Add `_setup_general_hooks()` to base.py (hooks initialized in backend.__init__)
- [x] 2.3 Add "hooks" to excluded config params in base.py
- [x] 2.4 Add "hooks" to excluded params in api_params_handler_base.py

## 3. Integration

- [x] 3.1 Add PreToolUse hook execution before tool calls
- [x] 3.2 Add PostToolUse hook execution after tool results
- [x] 3.3 Handle deny/ask decisions from PreToolUse
- [x] 3.4 Handle injection content from PostToolUse

## 4. Migration

- [x] 4.1 Create `MidStreamInjectionHook` built-in
- [x] 4.2 Create `ReminderExtractionHook` built-in
- [ ] 4.3 Migrate permission hooks to GeneralHookManager (deferred - existing pattern works)
- [ ] 4.4 Remove old mid-stream injection callback code (deferred - maintain backward compat)
- [ ] 4.5 Remove inline reminder extraction code (deferred - maintain backward compat)
- [ ] 4.6 Register built-in hooks in orchestrator (orchestrator can use set_general_hook_manager)

## 5. Testing & Documentation

- [x] 5.1 Unit tests for PythonCallableHook
- [x] 5.2 Unit tests for ExternalCommandHook
- [x] 5.3 Unit tests for GeneralHookManager
- [x] 5.4 Integration test with sample hooks
- [ ] 5.5 Migration tests for existing patterns
- [x] 5.6 Example YAML config in massgen/configs/hooks/
- [ ] 5.7 Update docs/source/reference/yaml_schema.rst

## Implementation Notes

### Completed

The core hook framework is fully implemented:

1. **HookEvent/HookResult**: Typed contracts for hook input/output
2. **PatternHook base class**: fnmatch-based tool name matching
3. **PythonCallableHook**: Lazy loading, async/sync support, timeout
4. **ExternalCommandHook**: JSON stdin/stdout protocol, env vars
5. **GeneralHookManager**: Global + per-agent hooks, override support
6. **Built-in hooks**: MidStreamInjectionHook, ReminderExtractionHook
7. **Config validation**: Validates hook configs at load time
8. **Integration**: Pre/PostToolUse hooks execute in tool pipeline

### Deferred

Migration of existing patterns (4.3-4.6) is deferred to maintain backward
compatibility. The new framework runs alongside existing code, allowing
gradual migration. Orchestrator can use `backend.set_general_hook_manager()`
to provide a shared manager with mid-stream injection hooks.
