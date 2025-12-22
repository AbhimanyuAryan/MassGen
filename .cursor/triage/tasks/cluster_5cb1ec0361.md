# Cluster 5cb1ec0361

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `TypeError: build_config() got an unexpected keyword argument 'context_path'. Did you mean 'context_paths'?`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_with_context_path
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_with_context_path
```

## Affected nodeids

- `massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_with_context_path`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

