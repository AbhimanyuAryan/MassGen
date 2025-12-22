# Cluster e6fef0cb73

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AttributeError: <massgen.backend.azure_openai.AzureOpenAIBackend object at <hex>> does not have the attribute 'client'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_stream_with_tools_with_model
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_stream_with_tools_with_model
```

## Affected nodeids

- `massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_stream_with_tools_with_model`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

