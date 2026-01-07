Hook Framework
==============

MassGen provides a hook framework for extending agent behavior at key execution points.
Hooks enable content injection, permission validation, and custom processing during
tool execution.

Overview
--------

Hooks are callbacks that execute at specific points in the agent lifecycle:

- **PreToolUse**: Before a tool is invoked
- **PostToolUse**: After a tool returns its result

Hooks can:

- **Allow/Deny** tool execution (PreToolUse)
- **Inject content** into tool results or as separate messages (PostToolUse)
- **Extract reminders** from tool output for system notifications
- **Modify arguments** before tool execution

Built-in Hooks
--------------

MassGen includes two built-in hooks that power multi-agent coordination:

MidStreamInjectionHook
~~~~~~~~~~~~~~~~~~~~~~

Injects updates from other agents into tool results during coordination.

**Purpose**: When Agent A provides an answer, other agents need to see that update
without losing their work progress. The MidStreamInjectionHook injects these updates
at natural pauses (tool completion) rather than requiring full agent restarts.

**Injection Strategy**: ``tool_result`` - appends to the current tool output

**Example injection**:

.. code-block:: text

   ============================================================
   ⚠️  IMPORTANT: NEW ANSWER RECEIVED - ACTION REQUIRED
   ============================================================

   [UPDATE: agent1 submitted new answer(s)]

     [agent1] (workspace: /path/to/temp_workspaces/agent_b/agent1):
       I've implemented the authentication module...

   ============================================================
   REQUIRED ACTION - You MUST do one of the following:
   ============================================================

   1. **ADD A TASK** to your plan: 'Evaluate agent answer(s) and decide next action'
      - Use update_task_status or create a new task to track this evaluation
      - Read their workspace files (paths above) to understand their solution
      - Compare their approach to yours

   2. **THEN CHOOSE ONE**:
      a) VOTE for their answer if it's complete and correct (use vote tool)
      b) BUILD on their work - improve/extend it and submit YOUR enhanced answer
      c) MERGE approaches - combine the best parts of their work with yours
      d) CONTINUE your own approach if you believe it's better

   DO NOT ignore this update - you must explicitly evaluate and decide!
   ============================================================

**Benefits**:

- Preserves agent's conversation history
- No lost work on new answers
- Lightweight mid-stream delivery

HighPriorityTaskReminderHook
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Injects reminders when high-priority tasks are completed using the planning tools.

**Purpose**: When an agent completes a high-priority task via ``update_task_status``,
this hook injects a reminder to document learnings. This encourages reflection and
knowledge capture after important work.

**Injection Strategy**: ``user_message`` - creates a separate message after tool result

**Trigger condition**: The hook inspects ``update_task_status`` tool output and fires when:

- ``task.priority == "high"``
- ``task.status == "completed"``

**Formatted injection**:

.. code-block:: text

   ============================================================
   ⚠️  SYSTEM REMINDER
   ============================================================

   ✓ High-priority task completed! Document decisions to optimize future work:
     • Which skills/tools were effective (or not)? → memory/long_term/skill_effectiveness.md
     • What approach worked (or failed) and why? → memory/long_term/approach_patterns.md
     • What would prevent mistakes on similar tasks? → memory/long_term/lessons_learned.md
     • User preferences revealed? → memory/short_term/user_prefs.md

   ============================================================

**Note**: Unlike passive extraction from tool JSON, this hook actively inspects tool
output and makes decisions about when to inject. This pattern is more flexible and
keeps reminder logic separate from tool implementation.

Injection Strategies
--------------------

Hooks can inject content using two strategies:

``tool_result`` Strategy
~~~~~~~~~~~~~~~~~~~~~~~~

Appends content directly to the tool result. Best for:

- Cross-agent updates during coordination
- Additional context that relates to the tool operation
- Minimal message overhead

.. code-block:: python

   HookResult(
       inject={
           "content": "[UPDATE] New information...",
           "strategy": "tool_result"
       }
   )

``user_message`` Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~

Injects as a separate user message after the tool result. Best for:

- System reminders and notifications
- Content that should be clearly distinguished from tool output
- Semantic separation

.. code-block:: python

   HookResult(
       inject={
           "content": "SYSTEM REMINDER: ...",
           "strategy": "user_message"
       }
   )

API-Specific Handling
---------------------

Different LLM APIs handle injection differently:

Anthropic API (Claude)
~~~~~~~~~~~~~~~~~~~~~~

Uses separate content blocks within a single message for clean semantic separation:

.. code-block:: json

   {
     "role": "user",
     "content": [
       {
         "type": "tool_result",
         "tool_use_id": "call_123",
         "content": "actual tool output"
       },
       {
         "type": "text",
         "text": "<system-reminder>Your TODO list is empty</system-reminder>"
       }
     ]
   }

OpenAI API (GPT-4, o1, etc.)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two approaches:

**Separate message**:

.. code-block:: json

   {"role": "tool", "tool_call_id": "call_123", "content": "actual output"}
   {"role": "user", "content": "<system-reminder>...</system-reminder>"}

**Structured output** (with system prompt explaining format):

.. code-block:: json

   {
     "role": "tool",
     "tool_call_id": "call_123",
     "content": "{\"output\": \"actual\", \"system_notes\": [\"reminder\"]}"
   }

Visual Separation
~~~~~~~~~~~~~~~~~

When appending to tool results, clear visual separators prevent model confusion:

.. code-block:: text

   actual tool output here

   ═══════════════════════════════════════════════════════
   SYSTEM CONTEXT (not part of tool output):
   - Your TODO list is empty
   - Consider using TodoWrite for multi-step tasks
   ═══════════════════════════════════════════════════════

Workspace Handling
------------------

When injecting answers from other agents, workspace paths are normalized so the
receiving agent can access the referenced files.

The Problem
~~~~~~~~~~~

Each agent has an isolated workspace:

- Agent A: ``.massgen/workspaces/agent_a_workspace/``
- Agent B: ``.massgen/workspaces/agent_b_workspace/``

If Agent A's answer references their workspace path, Agent B cannot access it.

Path Normalization
~~~~~~~~~~~~~~~~~~

Workspace paths are automatically normalized during injection:

.. code-block:: text

   Before (Agent A's answer):
   "I created /Users/foo/.massgen/workspaces/agent_a_workspace/output.py"

   After (what Agent B sees):
   "I created /Users/foo/.massgen/temp_workspaces/agent1/output.py"

The receiving agent can now actually access the files at the normalized path.

Snapshot Sharing
~~~~~~~~~~~~~~~~

When Agent A provides an answer:

1. Agent A's workspace is snapshotted
2. The snapshot is copied to Agent B's temp workspace
3. Paths in the injected answer point to the temp workspace
4. Agent B can read Agent A's files for verification

Anonymization
~~~~~~~~~~~~~

Agent identities are preserved through this process:

- Agent B doesn't know "agent1" is really "Agent A"
- Prevents voting bias based on agent identity
- But Agent B knows the injection is external (not from self)

This trade-off is acceptable because:

- Knowing updates are external prevents self-confirmation loops
- Anonymization between agents still prevents bias
- The alternative (full restart) loses ALL progress

Custom Hooks
------------

You can create custom hooks by implementing the hook interface.

Python Callable Hook
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from massgen.mcp_tools.hooks import (
       PythonCallableHook,
       HookEvent,
       HookResult,
       GeneralHookManager,
       HookType,
   )

   def my_audit_hook(event: HookEvent) -> HookResult:
       """Log all tool calls for auditing."""
       print(f"Tool called: {event.tool_name}")
       print(f"Arguments: {event.tool_input}")
       return HookResult.allow()

   # Register the hook
   manager = GeneralHookManager()
   hook = PythonCallableHook("audit", my_audit_hook, matcher="*")
   manager.register_global_hook(HookType.PRE_TOOL_USE, hook)

External Command Hook
~~~~~~~~~~~~~~~~~~~~~

Hooks can also be external scripts that receive JSON on stdin and return JSON on stdout:

.. code-block:: python

   from massgen.mcp_tools.hooks import ExternalCommandHook

   hook = ExternalCommandHook(
       "security_check",
       command="/path/to/security_hook.py",
       matcher="Write|Edit|Bash"
   )

The script receives:

.. code-block:: json

   {
     "hook_type": "PreToolUse",
     "tool_name": "Write",
     "tool_input": {"file_path": "/etc/passwd", "content": "..."},
     "agent_id": "agent_1"
   }

And returns:

.. code-block:: json

   {
     "allowed": false,
     "decision": "deny",
     "reason": "Cannot write to system files"
   }

Pattern Matching
~~~~~~~~~~~~~~~~

Hooks support glob-style pattern matching:

- ``*`` - Match all tools
- ``Write`` - Match exactly "Write"
- ``mcp__*`` - Match all MCP tools
- ``Write|Edit`` - Match "Write" or "Edit"

Hook Registration
-----------------

Global vs Per-Agent
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # Global hooks - apply to ALL agents
   hooks:
     PreToolUse:
       - matcher: "*"
         handler: "massgen.hooks.audit_all_tools"
         type: "python"

   agents:
     - id: "agent1"
       backend:
         # Per-agent hooks - extend global by default
         hooks:
           PreToolUse:
             - matcher: "Write"
               handler: "custom_write_hook.py"
               type: "command"
           PostToolUse:
             override: true  # Only use per-agent hooks
             hooks:
               - handler: "agent1_logging.py"
                 type: "command"

Error Handling
~~~~~~~~~~~~~~

- **Timeout**: Fail open (allow) - don't block agent on slow hooks
- **Import errors**: Fail closed (deny) - configuration error
- **Runtime errors**: Fail open with logging - don't crash agent

Timing Considerations
---------------------

Mid-stream injection has specific timing rules:

1. **First update**: Uses traditional full-message injection
   - Prevents premature convergence on first answer

2. **Subsequent updates**: Uses mid-stream hook injection
   - Lighter weight, preserves work in progress
   - Only new answers (not already seen) are injected

3. **Vote-only mode**: Skips mid-stream injection entirely
   - Tool schemas are fixed at stream start
   - Full restart required for new vote options

Debugging Injection
-------------------

Testing mid-stream injection requires one agent to be slower than others so it
receives updates while working. MassGen provides a debug delay feature for this.

Debug Delay Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Add ``debug_delay_seconds`` to a backend config to artificially slow an agent:

.. code-block:: yaml

   agents:
     - id: "agent_a"
       backend:
         type: "gemini"
         model: "gemini-3-flash-preview"

     - id: "agent_b"
       backend:
         type: "gemini"
         model: "gemini-3-flash-preview"
         debug_delay_seconds: 30        # Delay in seconds
         debug_delay_after_n_tools: 2   # Apply after N tool calls

**Parameters**:

- ``debug_delay_seconds``: How long to pause (default: 0, disabled)
- ``debug_delay_after_n_tools``: Apply delay after this many tool calls (default: 3)

**Why delay after N tools?** Delaying at the start would cause immediate restarts.
By waiting until the agent has made progress (created tasks, done some work), the
delay happens at a natural point where injection is meaningful.

Injection Visibility
~~~~~~~~~~~~~~~~~~~~

When injection occurs, you'll see:

1. **Log messages**:

   .. code-block:: text

      [Orchestrator] Copying snapshots for mid-stream injection to agent_b
      [Orchestrator] Injection workspace .../temp_workspaces/agent_b/agent1 contains: ['tasks', 'poem.txt']
      [Orchestrator] Mid-stream injection for agent_b: 1 new answer(s)
      [PostToolUse] Hook injection for mcp__filesystem__read_text_file: strategy=tool_result, content_len=1641

2. **Stream chunk**: A visible ``📥 [INJECTION]`` chunk in the output

3. **Full content**: The injection content is logged for debugging

Example Debug Config
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # massgen/configs/debug/injection_delay_test.yaml
   agents:
     - id: "agent_a"
       backend:
         type: "gemini"
         model: "gemini-3-flash-preview"
         cwd: "workspace1"
         enable_mcp_command_line: true

     - id: "agent_b"
       backend:
         type: "gemini"
         model: "gemini-3-flash-preview"
         cwd: "workspace2"
         enable_mcp_command_line: true
         debug_delay_seconds: 30
         debug_delay_after_n_tools: 2

   orchestrator:
     coordination:
       enable_agent_task_planning: true
       task_planning_filesystem_mode: true

Run with:

.. code-block:: bash

   uv run massgen --config massgen/configs/debug/injection_delay_test.yaml \
       "Create a simple poem and write it into a file"

.. seealso::

   - :doc:`agent_communication` - Multi-agent coordination and broadcasts
   - :doc:`/user_guide/files/file_operations` - Workspace management
