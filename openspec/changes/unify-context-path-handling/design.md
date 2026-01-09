# Design: Unify Context Path Handling

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            User Input                                        │
│  "Review @src/main.py and fix issues in @tests/:w"                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PromptParser                                         │
│  - Extract @path references                                                  │
│  - Resolve to absolute paths                                                 │
│  - Determine read/write permissions                                          │
│  - Clean prompt (replace @path with resolved path)                           │
│                                                                              │
│  Input:  "Review @src/main.py and fix issues in @tests/:w"                  │
│  Output: ParsedPrompt(                                                       │
│            cleaned_prompt="Review /abs/src/main.py and fix issues in /abs/tests/",
│            context_paths=[                                                   │
│              {"path": "/abs/src/main.py", "permission": "read"},            │
│              {"path": "/abs/tests", "permission": "write"}                  │
│            ]                                                                 │
│          )                                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │   CLI Entry       │           │   Web UI Entry    │
        │                   │           │                   │
        │ • Single question │           │ • WebSocket msg   │
        │ • Interactive     │           │ • REST API        │
        └───────────────────┘           └───────────────────┘
                    │                               │
                    ▼                               ▼
        ┌───────────────────────────────────────────────────┐
        │              Agent Creation Decision               │
        │                                                    │
        │  if agents is None:                               │
        │      # First prompt - create with all paths       │
        │      agents = create_agents_from_config(          │
        │          config_with_context_paths,               │
        │          filesystem_session_id=session_id,        │
        │          session_storage_base=SESSION_STORAGE,    │
        │      )                                            │
        │  elif new_paths_require_new_mounts:               │
        │      # Subsequent prompt with new paths           │
        │      cleanup_existing_agents()                    │
        │      agents = create_agents_from_config(...)      │
        │  else:                                            │
        │      # Path already accessible - just register    │
        │      agent.filesystem_manager.add_turn_context_path(path)
        └───────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │              FilesystemManager                     │
        │                                                    │
        │  With session mount enabled:                       │
        │  • Session directory pre-mounted in Docker         │
        │  • New turn paths can be added without restart     │
        │  • Container persists across turns                 │
        │                                                    │
        │  Without session mount:                            │
        │  • New paths require container restart             │
        │  • Container state lost between turns              │
        └───────────────────────────────────────────────────┘
```

## Key Design Decision: Context Path Accumulation

**Context paths accumulate across turns within a session.**

When a user specifies `@path` in any turn, that path remains accessible for ALL subsequent turns in the session. This matches user expectations - if you reference a file in turn 1, you should still be able to discuss it in turn 5.

### Example Session Flow

```
Turn 1: "Review @src/main.py"
  → context_paths: [src/main.py (read)]
  → Agent can access: src/main.py

Turn 2: "Now check @tests/test_main.py:w too"
  → NEW paths: [tests/test_main.py (write)]
  → ACCUMULATED context_paths: [src/main.py (read), tests/test_main.py (write)]
  → Agent can access: src/main.py, tests/test_main.py

Turn 3: "Fix the bug we discussed"
  → No new @paths
  → ACCUMULATED context_paths: [src/main.py (read), tests/test_main.py (write)]
  → Agent can STILL access: src/main.py, tests/test_main.py

Turn 4: "Also update @docs/README.md:w"
  → NEW paths: [docs/README.md (write)]
  → ACCUMULATED context_paths: [src/main.py, tests/test_main.py, docs/README.md]
  → Agent can access: ALL THREE paths
```

### Implementation

The accumulation is stored in `original_config["orchestrator"]["context_paths"]`:

```python
# In run_interactive_mode, track accumulated paths
# original_config is passed by reference and persists across turns

if parsed.context_paths:
    # Get existing paths from config (accumulated from previous turns)
    existing_paths = set()
    if orchestrator_cfg:
        for p in orchestrator_cfg.get("context_paths", []):
            if isinstance(p, dict):
                existing_paths.add(p.get("path"))
            else:
                existing_paths.add(p)

    # Find truly new paths (not in accumulated set)
    new_paths = [ctx for ctx in parsed.context_paths
                 if ctx["path"] not in existing_paths]

    if new_paths:
        # ADD to existing paths (don't replace!)
        if "orchestrator" not in original_config:
            original_config["orchestrator"] = {}
        if "context_paths" not in original_config["orchestrator"]:
            original_config["orchestrator"]["context_paths"] = []

        for ctx in new_paths:
            original_config["orchestrator"]["context_paths"].append(ctx)

        # Update orchestrator_cfg reference
        orchestrator_cfg = original_config.get("orchestrator", {})
```

### Permission Upgrade Logic

If a path is referenced with different permissions across turns, upgrade to the higher permission:

```
Turn 1: @src/main.py      → read
Turn 2: @src/main.py:w    → write (upgrade!)

Result: src/main.py has WRITE permission
```

Implementation:
```python
def merge_context_path(existing_paths: list, new_path: dict) -> list:
    """Merge new path, upgrading permission if needed."""
    for existing in existing_paths:
        if existing["path"] == new_path["path"]:
            # Path exists - upgrade to write if new is write
            if new_path["permission"] == "write":
                existing["permission"] = "write"
            return existing_paths  # Already exists, possibly upgraded

    # New path - add it
    existing_paths.append(new_path)
    return existing_paths
```

## Component Details

### 1. PromptParser (`massgen/prompt_parser.py`)

**Already implemented.** Key classes:

```python
@dataclass
class ParsedPrompt:
    original_prompt: str      # Original user input
    cleaned_prompt: str       # Prompt with @refs replaced by resolved paths
    context_paths: list       # [{"path": str, "permission": "read"|"write"}]
    missing_paths: list       # Paths that don't exist
    suggestions: list         # Helpful suggestions for user

class PromptParser:
    def parse(self, prompt: str) -> ParsedPrompt

def parse_prompt_for_context(prompt: str, base_path: Path = None) -> ParsedPrompt
```

### Path Syntax Options

Three approaches considered for handling `@path` references:

#### Option A: Inline File Picker (Recommended)

Use `prompt_toolkit` to show autocomplete popup when user types `@`:

```
User types: "Review @src/ma"
                       ↓
              ┌──────────────────┐
              │ src/main.py      │  ← Popup appears
              │ src/manager.py   │
              │ src/makefile     │
              └──────────────────┘
```

**Implementation**: Custom `Completer` class that:
1. Detects `@` character in input
2. Extracts partial path after `@`
3. Uses `PathCompleter` for file/directory suggestions
4. Handles `:w` suffix for write permission

**Pros**: Best UX, matches Claude Code, no ambiguity
**Cons**: Requires replacing `input()` with `prompt_toolkit.prompt()`

#### Option B: Delimiter Syntax `@[path]` or `@(path)`

Use explicit delimiters to mark path boundaries:

```
"Review @[src/main.py] and fix @[tests/]:w"
"Review @(src/main.py) and fix @(tests/):w"
```

**Pros**: Clear boundaries, simple regex, handles any path chars
**Cons**: Extra typing, non-standard syntax

#### Option C: Punctuation-Aware Regex (Current)

Regex stops at common punctuation: `(?=[\s.,;:!?)}\]>]|$)`

```
"files in @path/to/assets). Ensure..."
                        ↑ stops here
```

**Pros**: Minimal syntax, handles most cases
**Cons**: Edge cases with paths containing `.` in middle, less predictable

### Selected Approach: Option A (Inline Picker)

**Rationale**: Provides best user experience and eliminates parsing ambiguity.

**Regex pattern** (fallback for non-interactive contexts):
`(?<!\\)@([^\s@]+?)(:w)?(?=[\s.,;:!?)}\]>]|$)`
- `(?<!\\)` - Not preceded by backslash (escape)
- `@` - Literal @ symbol
- `([^\s@]+?)` - Path (non-greedy, no spaces or @)
- `(:w)?` - Optional `:w` suffix for write permission
- `(?=[\s.,;:!?)}\]>]|$)` - Followed by whitespace, punctuation, or end

### 2. CLI Integration Points

**Entry point** (`cli.py:cli_main`):
```python
# Line ~5588: Check if interactive mode without question
is_interactive_without_question = not args.question and not getattr(args, "interactive_with_initial_question", None)

if is_interactive_without_question:
    agents = None  # Defer creation
else:
    # Parse @paths before creating agents
    if args.question:
        args.question, config = inject_prompt_context_paths(args.question, config)
    agents = create_agents_from_config(...)
```

**Interactive mode** (`cli.py:run_interactive_mode`):
```python
# On each prompt:
parsed = parse_prompt_for_context(question)

if agents is None:
    # First prompt - create agents with all paths
    config = inject_paths_into_config(config, parsed.context_paths)
    agents = create_agents_from_config(config, ...)
elif has_new_paths(parsed.context_paths, existing_paths):
    # New paths - may need to recreate agents
    # NOTE: existing_paths includes ALL paths from previous turns
    if paths_require_new_mounts(new_paths, agents):
        cleanup_agents(agents)
        # Recreate with ACCUMULATED paths (not just new ones)
        agents = create_agents_from_config(config_with_all_paths, ...)
    else:
        # Paths accessible via session mount
        for agent in agents.values():
            agent.filesystem_manager.add_turn_context_path(path)
```

### 3. Web UI Integration Points

**`run_coordination`** (`frontend/web/server.py:~4169`):
```python
# BEFORE (missing parameters):
agents = create_agents_from_config(
    config,
    orchestrator_config=orchestrator_cfg,
    config_path=str(resolved_path),
    memory_session_id=session_id,
    progress_callback=progress_callback,
)

# AFTER (with session mount):
agents = create_agents_from_config(
    config,
    orchestrator_config=orchestrator_cfg,
    config_path=str(resolved_path),
    memory_session_id=session_id,
    progress_callback=progress_callback,
    filesystem_session_id=session_id,          # ADD
    session_storage_base=SESSION_STORAGE,       # ADD
)
```

**`run_coordination_with_history`** (`frontend/web/server.py:~4546`):
Same changes as above.

### 4. Session Mount Mechanism

The session mount feature pre-mounts a session directory into Docker containers:

```
Host: ~/.massgen/sessions/{session_id}/
  └── turn_1/
  └── turn_2/
  └── ...

Docker: /massgen_session/
  └── turn_1/
  └── turn_2/
  └── ...
```

When `filesystem_session_id` and `session_storage_base` are provided:
1. `FilesystemManager` creates a `SessionMountManager`
2. Session directory is mounted at container creation
3. New turn directories can be registered without container restart
4. `add_turn_context_path()` just updates permission manager

Without these parameters:
1. No session mount manager
2. Each new path requires container restart
3. Container state is lost

## Error Handling

### Missing Paths
```python
parsed = parse_prompt_for_context("Review @nonexistent.py")
if parsed.missing_paths:
    print("Warning: These paths don't exist:")
    for path in parsed.missing_paths:
        print(f"  - {path}")
    # Continue anyway - agent will see the path in prompt
```

### Path Requires New Mount (Docker Running)
```python
if agents and new_paths and not can_add_without_restart(new_paths, agents):
    print("Warning: New paths require Docker restart")
    print("Recreating agents with new mounts...")
    cleanup_agents(agents)
    # Recreate with ALL accumulated paths
    agents = create_agents_from_config(config_with_accumulated_paths, ...)
```

## Testing Strategy

### Unit Tests (`test_prompt_parser.py`)
- Basic parsing: `@path`, `@path:w`
- Directory syntax: `@dir/`, `@dir/:w`
- Escaped @: `\@not_a_path`
- Multiple paths in one prompt
- Edge cases: paths with special chars, unicode

### Integration Tests
- CLI single question with `@path`
- CLI interactive first prompt with `@path`
- CLI interactive subsequent prompt with new `@path`
- **CLI interactive: verify turn 1 paths accessible in turn 3**
- **CLI interactive: verify permission upgrade (read → write)**
- Web UI with session mount enabled

### Manual Testing
1. `massgen "Review @src/main.py" --config basic.yaml`
2. `massgen --config basic.yaml` → type `Review @src/main.py`
3. Interactive session:
   - Turn 1: `Review @src/main.py`
   - Turn 2: `What about the tests?` (no @path - should still have access to src/main.py)
   - Turn 3: `Also check @tests/` (should have access to BOTH src/main.py and tests/)
4. Web UI: start session → send message → verify Docker persists

## Phase 5: Web UI Inline File Picker

Add inline autocomplete to the Web UI chat input, providing the same experience as the CLI.

### Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Web UI Chat Input                                  │
│  "Review @src/ma"                                                         │
│                 ↓ keyup event with '@' detected                           │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    JavaScript Autocomplete Component                       │
│  - Detect '@' character in input                                          │
│  - Extract partial path after '@'                                         │
│  - Fetch suggestions from backend                                         │
│  - Render dropdown below cursor position                                  │
│  - Handle keyboard navigation (↑↓, Tab, Enter, Esc)                       │
│  - Insert selected completion                                             │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                            REST API call
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    Backend: /api/browse Endpoint                          │
│                                                                           │
│  Request:  POST /api/browse                                               │
│            {"path": "src/ma", "base_path": "/project", "limit": 20}      │
│                                                                           │
│  Response: {                                                              │
│    "entries": [                                                           │
│      {"name": "main.py", "type": "file", "language": "python"},          │
│      {"name": "manager.py", "type": "file", "language": "python"},       │
│      {"name": "models/", "type": "directory"}                            │
│    ],                                                                     │
│    "path": "src/",                                                        │
│    "has_more": false                                                      │
│  }                                                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

### Backend Implementation

**New endpoint** (`frontend/web/server.py`):

```python
@app.route("/api/browse", methods=["POST"])
async def browse_files():
    """List files/directories for autocomplete."""
    data = await request.get_json()
    partial_path = data.get("path", "")
    base_path = data.get("base_path", str(Path.cwd()))
    limit = data.get("limit", 20)

    # Resolve the path
    if partial_path.startswith("~"):
        search_path = Path(partial_path).expanduser()
    else:
        search_path = Path(base_path) / partial_path

    # Get parent directory and prefix filter
    if search_path.exists() and search_path.is_dir():
        parent_dir = search_path
        prefix = ""
    else:
        parent_dir = search_path.parent
        prefix = search_path.name

    entries = []
    try:
        for entry in sorted(parent_dir.iterdir()):
            if prefix and not entry.name.lower().startswith(prefix.lower()):
                continue
            if entry.name.startswith("."):
                continue  # Skip hidden files

            entry_type = "directory" if entry.is_dir() else "file"
            language = get_language_for_extension(entry.suffix) if entry.is_file() else None

            entries.append({
                "name": entry.name + ("/" if entry.is_dir() else ""),
                "type": entry_type,
                "language": language,
            })

            if len(entries) >= limit:
                break
    except PermissionError:
        pass

    return jsonify({
        "entries": entries,
        "path": str(parent_dir.relative_to(base_path)) + "/" if parent_dir != Path(base_path) else "",
        "has_more": len(entries) >= limit,
    })
```

### Frontend Implementation

**New component** (`frontend/web/static/js/path-autocomplete.js`):

```javascript
class PathAutocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.basePath = options.basePath || '/';
        this.dropdown = null;
        this.selectedIndex = -1;
        this.entries = [];
        this.atPosition = -1;

        this.init();
    }

    init() {
        this.input.addEventListener('input', (e) => this.onInput(e));
        this.input.addEventListener('keydown', (e) => this.onKeyDown(e));
        document.addEventListener('click', (e) => this.onDocumentClick(e));
    }

    async onInput(e) {
        const value = this.input.value;
        const cursorPos = this.input.selectionStart;

        // Find @ position before cursor
        const textBeforeCursor = value.substring(0, cursorPos);
        const atMatch = textBeforeCursor.match(/@([^\s@]*)$/);

        if (!atMatch) {
            this.hideDropdown();
            return;
        }

        this.atPosition = textBeforeCursor.lastIndexOf('@');
        const partialPath = atMatch[1];

        // Check for :w suffix
        let searchPath = partialPath;
        if (searchPath.endsWith(':w')) {
            searchPath = searchPath.slice(0, -2);
        } else if (searchPath.endsWith(':')) {
            searchPath = searchPath.slice(0, -1);
        }

        // Fetch suggestions
        try {
            const response = await fetch('/api/browse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: searchPath, base_path: this.basePath }),
            });
            const data = await response.json();
            this.entries = data.entries;
            this.showDropdown(data.entries, data.path);
        } catch (err) {
            console.error('Browse error:', err);
            this.hideDropdown();
        }
    }

    showDropdown(entries, basePath) {
        if (entries.length === 0) {
            this.hideDropdown();
            return;
        }

        if (!this.dropdown) {
            this.dropdown = document.createElement('div');
            this.dropdown.className = 'path-autocomplete-dropdown';
            this.input.parentElement.appendChild(this.dropdown);
        }

        this.dropdown.innerHTML = entries.map((entry, i) => `
            <div class="path-autocomplete-item ${i === this.selectedIndex ? 'selected' : ''}"
                 data-index="${i}">
                <span class="icon">${entry.type === 'directory' ? '📁' : '📄'}</span>
                <span class="name">@${basePath}${entry.name}</span>
                ${entry.language ? `<span class="meta">${entry.language}</span>` : ''}
            </div>
        `).join('');

        // Also add :w variants for files
        entries.forEach((entry, i) => {
            if (entry.type === 'file') {
                this.dropdown.innerHTML += `
                    <div class="path-autocomplete-item" data-index="${entries.length + i}" data-write="true">
                        <span class="icon">📝</span>
                        <span class="name">@${basePath}${entry.name}:w</span>
                        <span class="meta">${entry.language} (write)</span>
                    </div>
                `;
            }
        });

        this.dropdown.querySelectorAll('.path-autocomplete-item').forEach(item => {
            item.addEventListener('click', () => this.selectItem(parseInt(item.dataset.index)));
        });

        this.dropdown.style.display = 'block';
        this.selectedIndex = 0;
        this.updateSelection();
    }

    selectItem(index) {
        const items = this.dropdown.querySelectorAll('.path-autocomplete-item');
        if (index >= items.length) return;

        const item = items[index];
        const completion = item.querySelector('.name').textContent;

        // Replace @partial with full path
        const value = this.input.value;
        const before = value.substring(0, this.atPosition);
        const after = value.substring(this.input.selectionStart);

        this.input.value = before + completion + after;
        this.input.selectionStart = this.input.selectionEnd = before.length + completion.length;

        this.hideDropdown();
        this.input.focus();
    }

    onKeyDown(e) {
        if (!this.dropdown || this.dropdown.style.display === 'none') return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1,
                    this.dropdown.querySelectorAll('.path-autocomplete-item').length - 1);
                this.updateSelection();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.updateSelection();
                break;
            case 'Tab':
            case 'Enter':
                if (this.selectedIndex >= 0) {
                    e.preventDefault();
                    this.selectItem(this.selectedIndex);
                }
                break;
            case 'Escape':
                this.hideDropdown();
                break;
        }
    }

    updateSelection() {
        this.dropdown.querySelectorAll('.path-autocomplete-item').forEach((item, i) => {
            item.classList.toggle('selected', i === this.selectedIndex);
        });
    }

    hideDropdown() {
        if (this.dropdown) {
            this.dropdown.style.display = 'none';
        }
        this.selectedIndex = -1;
    }

    onDocumentClick(e) {
        if (!this.dropdown?.contains(e.target) && e.target !== this.input) {
            this.hideDropdown();
        }
    }
}
```

**Styles** (`frontend/web/static/css/path-autocomplete.css`):

```css
.path-autocomplete-dropdown {
    position: absolute;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    max-height: 300px;
    overflow-y: auto;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    min-width: 300px;
}

.path-autocomplete-item {
    padding: 8px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
}

.path-autocomplete-item:hover,
.path-autocomplete-item.selected {
    background: var(--bg-hover);
}

.path-autocomplete-item .icon {
    font-size: 14px;
}

.path-autocomplete-item .name {
    flex: 1;
    font-family: monospace;
    font-size: 13px;
}

.path-autocomplete-item .meta {
    color: var(--text-secondary);
    font-size: 11px;
}
```

### Integration

In the Web UI chat initialization (`frontend/web/static/js/chat.js`):

```javascript
// Initialize path autocomplete on chat input
const chatInput = document.getElementById('chat-input');
const pathAutocomplete = new PathAutocomplete(chatInput, {
    basePath: sessionConfig.workingDirectory || '/',
});
```

### Security Considerations

1. **Path traversal**: Backend validates paths don't escape allowed directories
2. **Rate limiting**: Limit `/api/browse` calls to prevent abuse
3. **Permission check**: Only show files accessible to the session

### Tasks

Add to `tasks.md`:

```markdown
## Phase 5: Web UI Inline File Picker

### 5.1 Backend Endpoint
- [ ] Create `/api/browse` endpoint in `frontend/web/server.py`
- [ ] Add path validation (prevent traversal outside allowed dirs)
- [ ] Add rate limiting for browse endpoint
- [ ] Test with various path inputs

### 5.2 Frontend Component
- [ ] Create `path-autocomplete.js` component
- [ ] Create `path-autocomplete.css` styles
- [ ] Handle keyboard navigation (↑↓, Tab, Enter, Esc)
- [ ] Support `:w` suffix display

### 5.3 Integration
- [ ] Initialize autocomplete on chat input
- [ ] Pass session working directory as base path
- [ ] Test with Web UI sessions

### 5.4 Testing
- [ ] Test autocomplete popup appears on @ keypress
- [ ] Test file/directory navigation
- [ ] Test :w suffix selection
- [ ] Test keyboard navigation
- [ ] Test path insertion into input
```

## Migration Notes

No migration needed. All changes are:
- New optional syntax (`@path`)
- Internal optimizations (deferred creation)
- Bug fixes (Web UI session mount)

Existing configs and workflows continue to work unchanged.
