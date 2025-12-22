# Cluster 4bbc1204e7

- **Count**: 3
- **Exception type**: `<unknown>`
- **Normalized message**: `AttributeError: 'AzureOpenAIBackend' object has no attribute 'azure_endpoint'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_init_with_env_vars
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_init_with_env_vars massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_init_with_kwargs massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_base_url_normalization
```

## Affected nodeids

- `massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_init_with_env_vars`
- `massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_init_with_kwargs`
- `massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_base_url_normalization`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

