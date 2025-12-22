# Cluster e93ca5b364

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'Invalid output format' in 'VHS is not installed. Please install it from https:<path>: brew install vhs (macOS) or go install github.com<path>`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_terminal_evaluation.py::TestTerminalEvaluation::test_invalid_output_format
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_terminal_evaluation.py::TestTerminalEvaluation::test_invalid_output_format
```

## Affected nodeids

- `massgen/tests/test_terminal_evaluation.py::TestTerminalEvaluation::test_invalid_output_format`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

