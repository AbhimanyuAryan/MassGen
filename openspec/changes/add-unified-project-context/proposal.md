# Change: Add Unified Project Context for Tools and Subagents

## Why

Custom tools (read_media, generate_media, understand_*) and subagents make external API calls without project context, causing the external models to hallucinate incorrect interpretations. For example, when evaluating an image for "MassGen", GPT-4.1 interpreted it as "Massachusetts General Hospital" because it had zero context about what MassGen actually is.

This wastes API calls and produces unusable results.

## What Changes

- Main agents will create a `CONTEXT.md` file in their workspace before spawning subagents or using multimodal tools
- System prompt builder will include instructions for when/how to create CONTEXT.md
- Multimodal tools will read CONTEXT.md and inject it into external API calls
- Subagent manager will auto-copy CONTEXT.md to subagent workspaces
- ExecutionContext will gain a `project_context` field for context injection

## Impact

- Affected specs: project-context (new capability)
- Affected code:
  - `massgen/system_message_builder.py` - Add CONTEXT.md creation instructions
  - `massgen/context/project_context.py` - New module for context loading
  - `massgen/backend/base_with_custom_tool_and_mcp.py` - ExecutionContext field
  - `massgen/tool/_multimodal_tools/*.py` - Context injection in API calls
  - `massgen/subagent/manager.py` - Auto-copy and include context
