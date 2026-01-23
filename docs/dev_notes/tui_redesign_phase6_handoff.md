# TUI Redesign Phase 6 Handoff: Modals + Enhanced Previews

## Previous Phases Summary

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Input Bar + Mode Toggles | ✓ Complete |
| Phase 2 | Agent Tabs | ✓ Complete |
| Phase 3 | Tool Cards & Timeline | ✓ Complete |
| Phase 4 | Welcome Screen | ✓ Complete |
| Phase 5 | Task Lists + Progress | ✓ Complete |
| **Phase 6** | **Modals + Enhanced Previews** | **✓ Complete (commit fa11307e)** |

## What Was Completed in Phase 6

### 6.1 Modal Visual Redesign

All 5 modal files updated:
- `task_plan_modal.py` - "Task Plan" (was "📋 Task Plan")
- `tool_detail_modal.py` - Tool name only (emoji removed)
- `background_tasks_modal.py` - "Background Operations" (was "⚙️ Background Operations")
- `plan_approval_modal.py` - "Plan Approval" (was "Plan Ready for Execution")
- `subagent_modal.py` - "Subagent . {id}" (was "🚀 {id}")

**Key Technical Note**: Theme variables (`$accent-*`, `$fg-*`, etc.) do NOT work in modal `DEFAULT_CSS` blocks. These are processed separately from the main theme files. All modals now use hardcoded hex colors:

| Purpose | Hex Color |
|---------|-----------|
| Purple (special) | `#a371f7` |
| Yellow (warning) | `#d29922` |
| Cyan (info) | `#39c5cf` |
| Blue (primary) | `#58a6ff` |
| Green (success) | `#3fb950` |
| Red (error) | `#f85149` |
| Muted text | `#8b949e` |
| Primary text | `#e6edf3` |
| Background base | `#0d1117` |
| Surface | `#1c2128` |
| Surface-2 | `#161b22` |
| Surface-3 | `#21262d` |
| Border | `#30363d` |

### 6.2 Diff View (DEFERRED)

Deferred to a future phase. Tasks remain in openspec for later implementation.

### 6.3 Workspace Browser Improvements

**Major Changes:**
- Removed redundant `WorkspaceFilesModal` class entirely
- Enhanced `WorkspaceBrowserModal` with:
  - Tree view with ASCII connectors (`├──`, `└──`, `│`)
  - Collapsible directories (click header to toggle)
  - Dirs with >3 files collapsed by default
  - `▶ dirname/ (count)` for collapsed, `▼ dirname/` for expanded
  - Filter out subagent directories (UUIDs, `agent_*`, `subagent_*`, gitignored)

**Files Modified:**
- `browser_modals.py` - Main workspace browser logic
- `workspace_modals.py` - Removed `WorkspaceFilesModal`, kept `FileInspectionModal`
- `textual/__init__.py`, `textual/widgets/__init__.py`, `textual/widgets/modals/__init__.py` - Updated exports
- `textual_terminal_display.py` - `/workspace` command now calls `_show_workspace_browser()`

**State Tracking:**
- `_expanded_dirs: Set[str]` - Which directories are expanded
- `_dir_file_counts: Dict[str, int]` - File counts per directory
- `_toggle_directory()` and `_refresh_file_list()` methods handle expansion

### 6.4 Result Renderer

**New File:** `massgen/frontend/displays/textual_widgets/result_renderer.py`

Features:
- Content type detection: JSON, Python, JavaScript, TypeScript, Markdown, YAML, XML, Shell
- Uses `rich.syntax.Syntax` for syntax highlighting
- Smart truncation (default: 50 lines, 5000 chars)
- JSON is pretty-printed before highlighting
- Integrated into `ToolDetailModal` for args and result display

## Phase 7: Header + Final Polish ✓ COMPLETED

Reference: `openspec/changes/update-tui-conversational-design/tasks.md`

### 7.1 Header Simplification
- [x] 7.1.1 Remove emoji from HeaderWidget (🤖, 💬, ⚠️ removed)
- [x] 7.1.2 Use bullet separator (•) instead of pipe

### 7.2 Color Refinements
- [x] 7.2.1 Desaturate accent colors in dark.tcss (15-20% softer)
- [x] 7.2.2 Update light.tcss to match new aesthetic
- [x] 7.2.3 Add softer border colors ($border-soft, $border-accent)

### 7.3 New CSS Classes
- [x] 7.3.1 Add `.rounded-card` class
- [x] 7.3.2 Add `.input-hero` class
- [x] 7.3.3 Add `.mode-pill` class
- [x] 7.3.4 Add `.progress-bar` and `.progress-bar-fill` classes
- [x] 7.3.5 Add `.diff-add` and `.diff-remove` classes
- [x] 7.3.6 Add `.tree-node`, `.tree-node-expanded`, `.tree-node-collapsed` classes
- [x] **7.3.7 CHECKPOINT: User approval for header + final polish ✓**

## Next Phase: Phase 8 - Professional Visual Polish

See `docs/dev_notes/tui_redesign_phase7_handoff.md` for Phase 8 details.

## Files Likely to Modify in Phase 7

1. **`massgen/frontend/displays/textual_widgets/header_widget.py`** - Remove emoji, update separators
2. **`massgen/frontend/displays/textual_themes/dark.tcss`** - Color refinements, new classes
3. **`massgen/frontend/displays/textual_themes/light.tcss`** - Matching light theme updates

## Testing

```bash
# Test workspace browser with collapsible dirs
uv run massgen --display textual --config massgen/configs/tools/mcp/filesystem_demo.yaml "List files"
# Press 'w' to open workspace browser, click on directories to expand/collapse

# Test subagent modal
uv run massgen --display textual --config three_agents.yaml "Use one subagent to research X"
# Click on subagent card to open modal

# Test tool detail modal
uv run massgen --display textual --config massgen/configs/tools/mcp/filesystem_demo.yaml "Read a file"
# Press 't' or click on tool card to see syntax-highlighted results
```

## Known Issues / Future Improvements

1. **Theme variables in modals** - Would be nice to have a way to use theme vars in `DEFAULT_CSS` but this is a Textual framework limitation
2. **Diff view** - Still deferred, would be valuable for file edit operations
3. **Light theme** - Hardcoded colors are optimized for dark theme; light theme may need separate values

## Approval Workflow

Phase 6 is complete. For Phase 7:
1. Review tasks in openspec
2. Implement header simplification and color refinements
3. User runs TUI to approve
4. Proceed to Phase 8: Professional Visual Polish
