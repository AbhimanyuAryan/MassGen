# Cluster 824e0d52b0

- **Count**: 2
- **Exception type**: `<unknown>`
- **Normalized message**: `massgen.cli.ConfigurationError: OpenAI API key not found. Set OPENAI_API_KEY environment variable.
You can add it to a .env file in:
  - Current directory: .env
  - User config: ~<path>
  - Global: ~<path>

Or run: massgen --setup`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_programmatic_api.py::TestRunFunctionIntegration::test_run_with_single_model
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_programmatic_api.py::TestRunFunctionIntegration::test_run_with_single_model massgen/tests/test_programmatic_api.py::TestRunFunctionIntegration::test_run_with_models_list
```

## Affected nodeids

- `massgen/tests/test_programmatic_api.py::TestRunFunctionIntegration::test_run_with_single_model`
- `massgen/tests/test_programmatic_api.py::TestRunFunctionIntegration::test_run_with_models_list`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

