# Proposal: Unify Context Path Handling

## Summary

This proposal addresses three related issues with context path handling across CLI and Web UI:

1. **`@path` syntax support**: Add inline context path references in prompts (e.g., `@src/main.py`)
2. **Deferred agent creation**: Defer Docker container creation until first prompt to avoid double-launch
3. **Web UI parity**: Fix missing session mount parameters in Web UI that prevent Docker container persistence

## Problem Statement

### Issue 1: No inline context path syntax
Users must currently specify context paths in YAML config or via explicit UI. There's no way to quickly reference files inline in prompts like other tools (Claude Code, Codex CLI) support.

**Current state**: User must edit config to add context paths before running.

**Desired state**: User can type `Review @src/main.py and @tests/:w` directly in prompt.

### Issue 2: Docker containers launch twice in interactive mode
When entering interactive mode, agents (and Docker containers) are created immediately. If the first prompt contains `@path` references, agents must be recreated with the new mounts, causing Docker containers to launch twice.

**Current state**:
1. Enter interactive mode → Docker containers launch
2. Type first prompt with `@path` → Docker containers destroyed and relaunched

**Desired state**:
1. Enter interactive mode → No Docker launch yet
2. Type first prompt with `@path` → Docker containers launch once with all paths

### Issue 3: Web UI missing session mount support
The Web UI's `create_agents_from_config` calls are missing `filesystem_session_id` and `session_storage_base` parameters. This means:
- Docker containers are recreated every turn (slower)
- Container state is lost between turns
- No Docker container persistence optimization

**CLI call** (correct):
```python
create_agents_from_config(
    config,
    orchestrator_cfg,
    filesystem_session_id=memory_session_id,  # ← Missing in Web UI
    session_storage_base=SESSION_STORAGE,      # ← Missing in Web UI
)
```

**Web UI call** (missing parameters):
```python
create_agents_from_config(
    config,
    orchestrator_config=orchestrator_cfg,
    config_path=str(resolved_path),
    memory_session_id=session_id,
    progress_callback=progress_callback,
)
```

## Proposed Solution

### Part 1: Inline File Picker with `@` Trigger (NEW)

Replace basic `input()` with `prompt_toolkit.prompt()` and add inline autocomplete:

```
User types: "Review @src/ma"
                       ↓
              ┌──────────────────┐
              │ src/main.py      │  ← Popup appears like Claude Code
              │ src/manager.py   │
              │ src/makefile     │
              └──────────────────┘
```

**Implementation**:
- Custom `AtPathCompleter` class using `prompt_toolkit.completion.PathCompleter`
- Triggers when user types `@` followed by path characters
- Shows file/directory suggestions in popup
- Supports `:w` suffix for write permission
- Falls back to regex parsing for non-interactive contexts (automation mode)

**Why this approach**:
- Matches Claude Code UX (see screenshot)
- Eliminates punctuation parsing ambiguity (e.g., `@path/file). Ensure...`)
- Provides path discovery via autocomplete

### Part 1b: `@path` Syntax Parser (Fallback)

A `prompt_parser.py` module for non-interactive contexts:
- Parses `@path` (read) and `@path:w` (write) references
- Punctuation-aware regex: stops at `. , ; : ! ? ) } ] >`
- Supports directories with trailing slash: `@dir/`, `@dir/:w`
- Handles escaped `\@` for literal @ symbols
- Returns cleaned prompt with resolved absolute paths

**Status**: Implementation exists, needs punctuation boundary fix.

### Part 2: Deferred Agent Creation (Partially Complete)

For interactive mode without initial question:
1. Set `agents = None` initially
2. Show "Agents will be created after first prompt" in UI
3. Wait for first prompt
4. Parse `@path` references
5. Create agents with complete context_paths
6. Single Docker launch

**Status**: Core logic implemented, but several guards for `None` agents are missing.

### Part 3: Web UI Session Mount Parity (Not Started)

Add missing parameters to Web UI's agent creation calls:
1. `run_coordination()` at line ~4169
2. `run_coordination_with_history()` at line ~4546

Both need:
```python
filesystem_session_id=session_id,
session_storage_base=SESSION_STORAGE,
```

Also need to pass `SESSION_STORAGE` constant or derive from config.

## Scope

### In Scope
- **Inline file picker** using `prompt_toolkit` for CLI interactive mode
- Complete `@path` syntax support in CLI (interactive + automation)
- Deferred agent creation for CLI interactive mode
- **Context path accumulation** across turns (turn 1 paths accessible in turn 3)
- Add session mount parameters to Web UI
- Fix all `None` agent guards in CLI
- Add `@path` syntax support to Web UI (parse on message send)

### Out of Scope
- Path validation against Docker container mounts
- Dynamic mount addition to running containers (Docker limitation)

### Phase 5: Web UI Inline File Picker (Future)

Add inline autocomplete to the Web UI chat input, matching the CLI experience:

**Implementation approach**:
1. Add backend endpoint `/api/browse` to list files/directories
2. Create JavaScript autocomplete component that triggers on `@`
3. Integrate with Web UI chat input field
4. Support same syntax: `@path`, `@path:w`, `@~/`, `@dir/`

**Why add this**:
- Consistency between CLI and Web UI experiences
- File discovery without leaving the chat interface
- Reduces friction for `@path` syntax adoption

## Breaking Changes

None. All changes are additive or internal improvements.

## Dependencies

- Linear Issue: MAS-230 (`@filename` syntax for inline context path inclusion)

## Success Criteria

1. **Inline picker**: Typing `@` in CLI shows file autocomplete popup
2. `@path` syntax works in CLI single-question mode (automation)
3. `@path` syntax works in CLI interactive mode (first prompt)
4. Interactive mode launches Docker only once when using `@path` in first prompt
5. **Context accumulation**: Paths from turn 1 remain accessible in turn 3
6. **Permission upgrade**: `@file` in turn 1, `@file:w` in turn 2 → write permission
7. Web UI maintains Docker container state between turns
8. All existing tests pass
9. New tests cover inline picker and path parsing edge cases
