# Cluster c93cc0fdf9

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AttributeError: 'ClaudeBackend' object has no attribute 'convert_messages_to_claude_format'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_backend.py::test_claude_message_conversion
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_backend.py::test_claude_message_conversion
```

## Affected nodeids

- `massgen/tests/test_claude_backend.py::test_claude_message_conversion`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

