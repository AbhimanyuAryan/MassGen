# Cluster 0417872da1

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'custom_function' in {'custom_tool__custom_function': RegisteredToolEntry(tool_name='custom_tool__custom_function', category='default', ori...bject'}}}, preset_params={}, context_param_names=set(), extension_model=None, mcp_server_id=None, post_processor=None)}
 +  where {'custom_tool__custom_function': RegisteredToolEntry(tool_name='custom_tool__custom_function', category='default', ori...bject'}}}, preset_params={}, context_param_names=set(), extension_model=None, mcp_server_id=None, post_processor=None)} = <massgen.tool._manager.ToolManager object at <hex>>.registered_tools
 +    where <massgen.tool._manager.ToolManager object at <hex>> = <massgen.tests.test_custom_tools.TestToolManager object at <hex>>.tool_manager`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_custom_tools.py::TestToolManager::test_add_tool_with_path
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_custom_tools.py::TestToolManager::test_add_tool_with_path
```

## Affected nodeids

- `massgen/tests/test_custom_tools.py::TestToolManager::test_add_tool_with_path`

## Suggested next step (for the subagent)

- Confirm if this is **unit** vs **integration/docker/expensive**.
- If it requires external prerequisites, **add the correct marker** and rely on the default skip policy.
- Otherwise, fix the implementation or the test; if deferred, add an **expiring entry** in `massgen/tests/xfail_registry.yml`.

