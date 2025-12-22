# Cluster addd89f9c7

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: Regex pattern did not match.
  Expected regex: 'Azure OpenAI endpoint URL is required'
  Actual message: 'Azure OpenAI API key is required. Set AZURE_OPENAI_API_KEY environment variable or pass api_key parameter.'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_init_missing_api_key
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_init_missing_api_key
```

## Affected nodeids

- `massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_init_missing_api_key`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

