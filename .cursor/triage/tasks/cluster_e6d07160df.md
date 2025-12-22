# Cluster e6d07160df

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'gemini-3-flash-preview' == 'gemini-<num>-flash'
  
  - gemini-<num>-flash
  + gemini-3-flash-preview`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_config_builder.py::TestCloneAgent::test_clone_openai_to_gemini_preserves_provider
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_config_builder.py::TestCloneAgent::test_clone_openai_to_gemini_preserves_provider
```

## Affected nodeids

- `massgen/tests/test_config_builder.py::TestCloneAgent::test_clone_openai_to_gemini_preserves_provider`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

