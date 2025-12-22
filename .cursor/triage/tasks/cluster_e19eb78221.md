# Cluster e19eb78221

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `TypeError: ag2_lesson_planner() got an unexpected keyword argument 'topic'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_ag2_lesson_planner.py::TestAG2LessonPlannerTool::test_missing_api_key_error
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_ag2_lesson_planner.py::TestAG2LessonPlannerTool::test_missing_api_key_error
```

## Affected nodeids

- `massgen/tests/test_ag2_lesson_planner.py::TestAG2LessonPlannerTool::test_missing_api_key_error`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

