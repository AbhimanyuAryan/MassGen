# Cluster 9f91c21fe7

- **Count**: 4
- **Exception type**: `<unknown>`
- **Normalized message**: `AttributeError: 'MessageTemplates' object has no attribute 'evaluation_system_message'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_message_context_building.py::test_turn1_context
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_message_context_building.py::test_turn1_context massgen/tests/test_message_context_building.py::test_turn2_context massgen/tests/test_message_context_building.py::test_turn3_context massgen/tests/test_message_context_building.py::test_context_comparison
```

## Affected nodeids

- `massgen/tests/test_message_context_building.py::test_turn1_context`
- `massgen/tests/test_message_context_building.py::test_turn2_context`
- `massgen/tests/test_message_context_building.py::test_turn3_context`
- `massgen/tests/test_message_context_building.py::test_context_comparison`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

