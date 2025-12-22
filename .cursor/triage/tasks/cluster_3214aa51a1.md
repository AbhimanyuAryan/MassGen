# Cluster 3214aa51a1

- **Count**: 4
- **Exception type**: `<unknown>`
- **Normalized message**: `failed on setup with "TypeError: Can't instantiate abstract class MockClaudeCodeAgent without an implementation for abstract methods 'get_configurable_system_message', 'get_status', 'reset'"`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_code_context_sharing.py::test_orchestrator_initialization_with_context_sharing
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_code_context_sharing.py::test_orchestrator_initialization_with_context_sharing massgen/tests/test_claude_code_context_sharing.py::test_snapshot_saving massgen/tests/test_claude_code_context_sharing.py::test_workspace_restoration_with_anonymization massgen/tests/test_claude_code_context_sharing.py::test_save_all_snapshots
```

## Affected nodeids

- `massgen/tests/test_claude_code_context_sharing.py::test_orchestrator_initialization_with_context_sharing`
- `massgen/tests/test_claude_code_context_sharing.py::test_snapshot_saving`
- `massgen/tests/test_claude_code_context_sharing.py::test_workspace_restoration_with_anonymization`
- `massgen/tests/test_claude_code_context_sharing.py::test_save_all_snapshots`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

