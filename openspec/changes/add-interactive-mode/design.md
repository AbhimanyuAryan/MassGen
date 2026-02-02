# Interactive Mode Design

## Context

MassGen is a multi-agent coordination system that currently operates in a task-oriented fashion: users submit a question, agents coordinate to solve it, and a final answer is produced. There's no persistent layer for ongoing orchestration or context management across runs.

**Stakeholders:**
- End users who want a more conversational MassGen experience
- Developers building on MassGen who need programmatic run control
- Power users managing complex multi-run workflows

## Goals / Non-Goals

### Goals
- Create a persistent interactive layer that manages context across runs
- Enable the interactive agent to decide when to delegate vs. answer directly
- Provide clear data flow between interactive layer and spawned runs
- Maintain compatibility with existing single-task workflows
- Enable approval flows before spawning runs (configurable)

### Non-Goals
- Meta-level task planning (deferred)
- Parallel run orchestration (deferred)
- `ask_others` integration (pending broadcast refactoring)
- Bidirectional callbacks between interactive and runs (one-way only)

## Decisions

### Decision 1: Entry Point Strategy
**Choice:** Interactive Mode is the default when TUI launches with `interactive_mode.enabled: true` in config.

**Why:** This makes interactive mode the natural starting point without requiring new CLI flags. Users who want single-task behavior can disable it or use `--automation` mode.

**Alternatives considered:**
- Separate `--interactive` flag: Adds cognitive overhead
- Always interactive: Breaks existing workflows

### Decision 2: Run Triggering Mechanism
**Choice:** Use a `launch_run` tool that the interactive agent invokes.

**Why:** This follows the existing workflow toolkit pattern. The agent can reason about when to use it, and tool calls are naturally observable in the TUI.

**Alternatives considered:**
- Magic keywords in messages: Less flexible, harder to pass context
- Separate UI button: Removes agent autonomy

### Decision 3: Context Flow Architecture
**Choice:** One-way context flow (interactive → runs). The interactive agent packages context and passes it to runs. Results flow back but runs cannot request context mid-execution.

**Why:** Simplifies initial implementation. Bidirectional flow adds significant complexity and can be added later.

**Alternatives considered:**
- Bidirectional with callbacks: Too complex for v1
- No context passing: Limits usefulness

### Decision 4: Tool Set Differentiation
**Choice:** Interactive agent gets `launch_run` only (plus any MCP/external tools). It does NOT get `new_answer`, `vote`, or `ask_others`.

**Why:** The interactive agent orchestrates but doesn't participate in coordination. Clear role separation.

**Alternatives considered:**
- Full tool access: Would confuse the agent's role
- Subset of coordination tools: Partial access is confusing

### Decision 5: System Prompt Section Reuse
**Choice:** Reuse existing MassGen system prompt sections (skills, memory, filesystem, etc.) but exclude coordination-specific sections.

**Why:** The interactive agent still needs capabilities like skills, memory, and filesystem access. Only the coordination workflow (vote/new_answer) doesn't apply.

**Included sections:**
- `AgentIdentitySection` (custom identity)
- `CoreBehaviorsSection` (action bias, parallel tools)
- `SkillsSection` (if enabled)
- `MemoryFilesystemSection` (if enabled)
- `FilesystemWorkspaceSection` (if workspace configured)
- `TaskPlanningSection` (if enabled)
- Model-specific guidance (GPT5, Grok)

**Excluded sections:**
- `MassGenCoordinationSection` (vote/new_answer workflow)
- `BroadcastCommunicationSection` (ask_others)
- `VotingGuidanceSection` (voting criteria)

**Added section:**
- `InteractiveOrchestratorSection` - explains launch_run usage and run configuration options

### Decision 6: Approval Flow
**Choice:** Optional approval modal controlled by `require_approval` config.

**Why:** Some users want oversight before runs start. Others prefer autonomous operation.

**Alternatives considered:**
- Always require approval: Too friction-heavy
- Never require approval: Some users want control

### Decision 7: Launch Run Tool Parameters
**Choice:** The `launch_run` tool supports flexible run configurations:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `task` | string | required | What to accomplish |
| `context` | string | null | Background info, constraints |
| `agent_mode` | "single" \| "multi" | "multi" | One or multiple agents |
| `agents` | string[] | all | Specific agents to use |
| `refinement` | bool | true (multi), false (single) | Enable voting/refinement |
| `planning_mode` | bool | false | Plan without executing |
| `execute_after_planning` | bool | false | Auto-execute after planning |
| `coordination_overrides` | object | null | Fine-grained config |

**Run Mode Matrix:**

| Mode | agent_mode | refinement | planning_mode | Behavior |
|------|------------|------------|---------------|----------|
| Quick single | single | false | false | One agent, direct execution |
| Single + refine | single | true | false | One agent with self-refinement |
| Multi no-refine | multi | false | false | Multiple agents, best initial wins |
| Multi + refine | multi | true | false | Full coordination with voting |
| Plan only | any | any | true | Agents describe approach, no actions |
| Plan → Execute | any | any | true + execute | Plan first, then auto-execute winner |

**Why this flexibility:** Different tasks have different optimal configurations. Simple tasks don't need multi-agent overhead. Complex tasks benefit from coordination. Planning mode enables "think first" workflows.

## Architecture

### Class Hierarchy

```
InteractiveSession
├── _interactive_agent: ChatAgent (single agent, special system prompt)
├── run_history: List[RunResult]
├── _orchestrator_factory: Callable (creates orchestrators for runs)
└── workspace: ProjectWorkspace (context/file management)

LaunchRunToolkit (workflow toolkit)
├── toolkit_id: "launch_run"
├── get_tools(): Returns tool definition
└── is_enabled(): True when interactive mode on
```

### Data Flow

```
User Input
    │
    ▼
InteractiveSession.chat()
    │
    ├─── Simple query ──────────► Interactive Agent responds directly
    │
    └─── Complex task ──────────► Interactive Agent calls launch_run
                                        │
                                        ▼
                                  Approval Modal (if required)
                                        │
                                        ▼
                                  InteractiveSession._execute_run()
                                        │
                                        ▼
                                  Orchestrator spawned with context
                                        │
                                        ▼
                                  Multi-agent coordination
                                        │
                                        ▼
                                  RunResult returned to Interactive Agent
                                        │
                                        ▼
                                  Agent summarizes/suggests next steps
```

### State Machine

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
             ┌──────────┐                                 │
             │   IDLE   │◄─────────────────────┐          │
             └────┬─────┘                      │          │
                  │                            │          │
                  │ User sends message         │          │
                  ▼                            │          │
             ┌──────────┐                      │          │
             │ CHATTING │                      │          │
             └────┬─────┘                      │          │
                  │                            │          │
          ┌───────┴───────┐                    │          │
          │               │                    │          │
          ▼               ▼                    │          │
    Direct reply    launch_run called          │          │
          │               │                    │          │
          │               ▼                    │          │
          │        ┌──────────────┐            │          │
          │        │ AWAITING     │────────────┤          │
          │        │ APPROVAL     │  Cancel    │          │
          │        └──────┬───────┘            │          │
          │               │ Approve            │          │
          │               ▼                    │          │
          │        ┌──────────────┐            │          │
          │        │   RUNNING    │            │          │
          │        └──────┬───────┘            │          │
          │               │ Complete           │          │
          │               ▼                    │          │
          │        ┌──────────────┐            │          │
          │        │ PROCESSING   │────────────┘          │
          │        │ RESULTS      │                       │
          │        └──────────────┘                       │
          │                                               │
          └───────────────────────────────────────────────┘
```

## Config Schema

```yaml
orchestrator:
  interactive_mode:
    enabled: true                    # Enable interactive mode
    require_approval: true           # Show approval modal before runs
    backend:                         # Optional: defaults to first agent's backend
      type: "claude"
      model: "claude-sonnet-4-20250514"
    append_system_prompt: |          # Optional: custom guidance
      You specialize in code review tasks.
    context_compaction:
      enabled: true                  # Auto-compact long conversations
      threshold_tokens: 50000        # Trigger compaction threshold
      preserve_recent: 10            # Keep N recent exchanges

  coordination:
    # ... existing coordination config
```

## Risks / Trade-offs

### Risk: Context Loss During Compaction
**Mitigation:** Preserve critical context markers, allow users to pin important messages.

### Risk: Approval Modal Friction
**Mitigation:** Make it optional via config, provide keyboard shortcut to approve quickly.

### Risk: Agent Confusion About Role
**Mitigation:** Clear system prompt differentiating interactive agent from coordination agents.

### Trade-off: One-Way Context Flow
**Accepted:** Simplifies v1, can add bidirectional callbacks later if needed.

### Trade-off: No Parallel Runs
**Accepted:** Sequential runs are simpler, parallel orchestration is a v2 feature.

## Migration Plan

1. Interactive mode is opt-in via config (default: disabled initially)
2. Existing configs continue to work unchanged
3. Add example configs showing interactive mode usage
4. Document migration path for users wanting interactive mode

## Open Questions

1. **Should interactive mode be default in future versions?** - Deferred, gather user feedback first
2. **How should workspace directories be structured?** - Proposed structure in implementation plan, may evolve
3. **What level of context should be passed to runs?** - Start with full context, add filtering if needed
