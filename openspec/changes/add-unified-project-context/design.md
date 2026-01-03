# Design: Unified Task Context

## Context

Custom tools and subagents make external API calls (to GPT-4.1, Gemini, etc.) without understanding what the user is trying to accomplish. This causes hallucinations where external models misinterpret task-specific terminology.

**Key constraint**: Context must be dynamic and agent-created (not a static user file), similar to how evolving skills work.

## Goals / Non-Goals

### Goals
- Main agents create CONTEXT.md with task context (what we're building/doing, key terminology, relevant details)
- Multimodal tools read and inject context into external API calls
- Subagents automatically receive CONTEXT.md from parent workspace
- Tools/subagents fail with clear error if CONTEXT.md missing

### Non-Goals
- User-managed context files (agent creates them dynamically)
- Complex context inheritance hierarchies
- Context versioning or history

## Decisions

### Decision 1: Agent-created CONTEXT.md via system prompt instruction

**What**: Add instruction to system prompt telling agents to create CONTEXT.md before spawning subagents or using multimodal tools.

**Why**:
- Lightweight (no new tools needed)
- Flexible (agent decides content based on task)
- Follows established pattern (like evolving skills)

**Alternatives considered**:
- Explicit `create_project_context` tool - adds overhead, not worth it
- Automatic orchestrator creation - too rigid, can't customize

### Decision 2: Context loaded via `load_task_context()` helper

**What**: Single function that reads CONTEXT.md from workspace path, raises error if missing.

**Why**:
- Simple, testable
- Single point of discovery logic
- Easy to extend later

### Decision 3: Context injected via @context_params decorator

**What**: Add `task_context` to @context_params in read_media.py and generate_media.py, then pass to underlying tools.

**Why**:
- Uses existing infrastructure
- Clean separation of concerns
- LLM doesn't see context params in tool schema

### Decision 4: Context prepended to prompts with clear markers

**What**: Format as `[Task Context]\n{context}\n\n[Request]\n{prompt}`

**Why**:
- Clear separation helps external model distinguish context from request
- Consistent format across all tools

### Decision 5: Require CONTEXT.md (fail if missing)

**What**: Multimodal tools and subagent spawning will fail with a clear error if CONTEXT.md doesn't exist.

**Why**:
- Forces agents to learn the pattern
- Explicit behavior - no silent degradation
- Clear error message guides agent to create the file

**Error message**:
```
CONTEXT.md not found in workspace. Before using multimodal tools or spawning subagents,
create a CONTEXT.md file with task context. See system prompt for instructions.
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Large CONTEXT.md bloats prompts | Default 10000 char limit |
| Agent forgets to create CONTEXT.md | Tool fails with clear error message guiding agent |
| Context becomes stale during long runs | Agent can update CONTEXT.md as needed |
| Strict requirement blocks quick workflows | Clear system prompt instruction + helpful error |

## Migration Plan

1. No migration needed - purely additive change
2. Existing workflows continue working (no CONTEXT.md = no injection)
3. Rollback: Remove system prompt instruction, context loading still harmless

## Open Questions

None - design decisions confirmed with user.
