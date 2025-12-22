# Cluster 20d8cab08a

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: VHS is not installed. Install with: brew install vhs (macOS) or go install github.com<path>
assert False
 +  where False = check_vhs_installed()`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_terminal_evaluation.py::TestTerminalEvaluation::test_vhs_installed
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_terminal_evaluation.py::TestTerminalEvaluation::test_vhs_installed
```

## Affected nodeids

- `massgen/tests/test_terminal_evaluation.py::TestTerminalEvaluation::test_vhs_installed`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

