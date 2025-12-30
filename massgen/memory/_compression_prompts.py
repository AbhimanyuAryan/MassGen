# -*- coding: utf-8 -*-
"""
Prompts for agent-driven context compression.

These prompts instruct the agent to save memories before context truncation.
"""

COMPRESSION_REQUEST = """
[SYSTEM: Context Compression Required]

Your context window is at {usage_percent:.0%} capacity ({current_tokens:,}/{max_tokens:,} tokens).
Before continuing, you MUST save memories and signal completion.

## IMPORTANT: Preserve Task Context

Before writing your summary, read these files to ensure you preserve full context:
1. `tasks/plan.json` - Your current task plan (if exists)
2. `tasks/evolving_skill/SKILL.md` - Your workflow plan (if exists)

## Required Steps:

### 1. Write Short-Term Summary
Write a DETAILED summary to `memory/short_term/recent.md` containing:

```markdown
# Recent Conversation Summary

## Task Context
[Brief description of what you're working on]

## Current Task Plan
[Summary of your task plan from tasks/ if applicable]

## Key Progress
- [Decisions made with context and reasoning]
- [Files created/modified with full paths]
- [Important findings with specifics]

## Environment Setup
- [Packages installed: pip install X, npm install Y]
- [Directories created]
- [Any configuration changes]

## Tool Results
- [Key tool calls and their outputs]
- [Function signatures or patterns discovered]
- [Errors encountered and how they were resolved]

## Current State
- [Where you are in the workflow]
- [What has been completed vs what remains]

## Next Steps
- [Specific remaining work with details]
```

**CRITICAL**: The summary must be DETAILED ENOUGH that you can continue work after
context truncation. Vague summaries like "working on website" are NOT acceptable.
Include specific file paths, decisions made, and actual content where relevant.

### 2. Write Long-Term Memories (if applicable)
Save any information worth preserving across sessions to `memory/long_term/[name].md`:
- User preferences discovered
- Project-specific patterns or conventions
- Reusable solutions or approaches
- Important facts about the codebase

### 3. Signal Completion
After writing memories, call the `compression_complete` tool to signal you're done.

If any file writing fails, report the error before calling compression_complete.

IMPORTANT: You must complete all three steps. The conversation history will be truncated
after you call compression_complete, so ensure all important information is saved first.
"""

COMPRESSION_FAILED_RETRY = """
[SYSTEM: Compression Incomplete]

The required memory file was not found. Please ensure you:
1. Write the summary to `memory/short_term/recent.md`
2. Call the `compression_complete` tool

Attempt {attempt}/{max_attempts}. If you continue to fail, algorithmic compression will be used.
"""
