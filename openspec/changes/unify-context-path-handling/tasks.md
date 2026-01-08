# Tasks: Unify Context Path Handling

## Phase 1: Inline File Picker (CLI)

### 1.1 Create Custom Path Completer
- [x] Create `massgen/path_completer.py` with `AtPathCompleter` class
- [x] Detect `@` character and switch to path completion mode
- [x] Use `prompt_toolkit.completion.PathCompleter` for file suggestions
- [x] Handle `:w` suffix display in completions (show as option)
- [x] Support `~/` expansion and relative paths

### 1.2 Replace `input()` with `prompt_toolkit.prompt()`
- [x] Update `read_multiline_input()` to use `prompt_toolkit`
- [x] Integrate `AtPathCompleter` as completer
- [x] Preserve multiline input behavior (triple-quote or Shift+Enter)
- [x] Test backward compatibility with existing prompts

### 1.3 Fix None Agent Guards
- [x] Fix `/reset` command at line ~4828 to handle `agents=None`
- [x] Fix `/status` command at line ~4898 to handle `agents=None`
- [x] Audit all `agents.` references in `run_interactive_mode()` for None safety

### 1.4 Complete Deferred Agent Creation
- [x] Verify `enable_rate_limit` parameter is passed correctly
- [x] Verify `session_storage_base` is passed correctly
- [x] Ensure context paths accumulate across turns (not reset)
- [ ] Test deferred creation flow end-to-end (manual test)

### 1.5 Add Tests
- [x] Test `AtPathCompleter` completion suggestions
- [ ] Test interactive mode with `@path` in first prompt (manual test)
- [ ] Test interactive mode without `@path` (plain question) (manual test)
- [ ] Test subsequent prompts with new `@path` references (manual test)
- [ ] Test path accumulation: turn 1 paths still accessible in turn 3 (manual test)
- [ ] Test permission upgrade: `@file` then `@file:w` → write (manual test)

## Phase 2: Web UI Session Mount Parity

### 2.1 Add Session Mount Parameters
- [x] Update `run_coordination()` (~line 4169) to pass `filesystem_session_id` and `session_storage_base`
- [x] Update `run_coordination_with_history()` (~line 4546) to pass `filesystem_session_id` and `session_storage_base`
- [x] Import or define `SESSION_STORAGE` constant in web server

### 2.2 Test Web UI Docker Persistence
- [ ] Verify Docker containers persist between turns in Web UI (manual test)
- [ ] Verify container state (installed packages, files) persists (manual test)
- [ ] Compare performance: before vs after (should be faster) (manual test)

## Phase 3: Web UI `@path` Support

### 3.1 Add `@path` Parsing to Web UI
- [x] Parse `@path` references when user sends message
- [x] Display extracted paths in UI (similar to CLI)
- [x] Handle first message (deferred agent creation pattern)

### 3.2 Handle Path Changes Mid-Session
- [x] If new paths require new mounts and Docker is running, context_paths injected
- [ ] Option to restart agents with new paths (out of scope for this PR)
- [ ] Update UI to show current context paths (out of scope for this PR)

### 3.3 Web UI Tests
- [ ] Test `@path` parsing in Web UI message handler (manual test)
- [ ] Test warning when path requires container restart (out of scope)

## Phase 4: Documentation

### 4.1 User Documentation
- [x] Add `@path` syntax section to `docs/source/user_guide/files/file_operations.rst`
- [x] Document escaped `\@` syntax
- [x] Add examples for common use cases

### 4.2 Update Existing Docs
- [x] Ensure context_paths documentation mentions `@path` alternative
- [ ] Update Web UI documentation if applicable (out of scope for this PR)

## Phase 5: Web UI Inline File Picker

### 5.1 Backend Endpoint
- [x] Create `/api/path/autocomplete` endpoint in `frontend/web/server.py`
- [x] Add path validation (resolve to absolute, check exists)
- [ ] Add rate limiting for browse endpoint (out of scope for this PR)
- [ ] Test with various path inputs (manual test)

### 5.2 Frontend Component
- [x] Create `PathAutocomplete.tsx` component
- [x] Inline Tailwind CSS styles (no separate CSS file needed)
- [x] Handle keyboard navigation (↑↓, Tab, Enter, Esc)
- [x] Support `:w` suffix display (arrow right toggles)

### 5.3 Integration
- [x] Integrate autocomplete with chat input in App.tsx
- [ ] Pass session working directory as base path (future enhancement)
- [ ] Test with Web UI sessions (manual test)

### 5.4 Testing
- [ ] Test autocomplete popup appears on @ keypress (manual test)
- [ ] Test file/directory navigation (manual test)
- [ ] Test :w suffix selection (manual test)
- [ ] Test keyboard navigation (manual test)
- [ ] Test path insertion into input (manual test)

## Acceptance Criteria Checklist

- [x] All Phase 1 tasks complete (tests added, manual tests pending)
- [x] All Phase 2 tasks complete (manual tests pending)
- [x] All Phase 3 tasks complete (basic implementation, UI improvements out of scope)
- [x] All Phase 4 tasks complete (documentation updated)
- [x] All Phase 5 tasks complete (core implementation, manual tests pending)
- [x] `uv run pytest massgen/tests/test_prompt_parser.py -v` passes
- [x] `uv run pytest massgen/tests/test_path_completer.py -v` passes
- [x] `uv run pre-commit run --all-files` passes
- [ ] Manual testing: CLI interactive mode with `@path` works
- [ ] Manual testing: Web UI Docker persistence works
- [ ] Manual testing: Web UI file picker with `@path` works
