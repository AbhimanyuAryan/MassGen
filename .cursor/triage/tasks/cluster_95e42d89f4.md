# Cluster 95e42d89f4

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'filesystem' not in ['filesystem', 'command_line']`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_exclude_file_operation_mcps.py::TestExcludeFileOperationMCPs::test_inject_filesystem_mcp_excludes_filesystem_server
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_exclude_file_operation_mcps.py::TestExcludeFileOperationMCPs::test_inject_filesystem_mcp_excludes_filesystem_server
```

## Affected nodeids

- `massgen/tests/test_exclude_file_operation_mcps.py::TestExcludeFileOperationMCPs::test_inject_filesystem_mcp_excludes_filesystem_server`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

