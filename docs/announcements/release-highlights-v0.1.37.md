# Release Highlights — v0.1.37 (2026-01-12)

### 📜 [Execution Traces](https://docs.massgen.ai/en/latest/user_guide/logging.html#execution-traces)
- **Full History Preservation**: Human-readable `execution_trace.md` files saved alongside agent snapshots
- **Compression Recovery**: Agents can read trace files to recover detailed history after context compression
- **Cross-Agent Access**: Other agents can access execution traces in temp workspaces to understand approaches
- **No Truncation**: Tool calls, results, and reasoning blocks preserved in full
- **Grep-Friendly**: Searchable markdown format for debugging and analysis

### 🧠 [Thinking Mode Improvements](https://docs.massgen.ai/en/latest/user_guide/backends.html#thinking-mode)
- **Claude Code Thinking**: Streaming buffer support for Claude Code reasoning content
- **Gemini Thinking Fixes**: Proper reasoning content handling and streaming buffer integration
- **Vote Reasoning Traces**: Full vote context captured in execution trace files

### 🏷️ Standardized Agent Labeling
- **Unified Format**: Consistent agent identification across all backends
- **Improved Anonymization**: Better workspace anonymization for cross-agent sharing
- **Coordination Context**: Clearer agent references in multi-agent workflows

### 🐛 Bug Fixes
- **Claude Code Backend**: Fixed skills and tool handling issues
- **Config Builder**: Fixed configuration generation edge cases
- **Round Timeout**: Improved timeout behavior during coordination

---

### 📖 Getting Started
- [**Quick Start Guide**](https://github.com/massgen/MassGen?tab=readme-ov-file#1--installation): Try the new features today
- **Try These Examples**:

```bash
# Run a multi-agent task and check execution traces
uv run massgen --config massgen/configs/basic/multi/three_agents_default.yaml \
  "Explain the benefits of functional programming"

# Execution traces are saved in .massgen/massgen_logs/[log_dir]/[agent]/snapshots/
# Each snapshot contains execution_trace.md with full history

# Test round timeout behavior
uv run massgen --config massgen/configs/debug/round_timeout_test.yaml \
  "Write a short story"
```

  - [`three_agents_default.yaml`](https://github.com/massgen/MassGen/blob/main/massgen/configs/basic/multi/three_agents_default.yaml) - Multi-agent configuration for testing execution traces
  - [`round_timeout_test.yaml`](https://github.com/massgen/MassGen/blob/main/massgen/configs/debug/round_timeout_test.yaml) - Debug configuration for timeout testing
