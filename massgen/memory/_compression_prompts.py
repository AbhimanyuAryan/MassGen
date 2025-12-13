# -*- coding: utf-8 -*-
"""
Prompts for agent-driven context compression.

These prompts instruct the agent to save memories before context truncation.
"""

COMPRESSION_REQUEST = """
[SYSTEM: Context Compression Required]

Your context window is at {usage_percent:.0%} capacity ({current_tokens:,}/{max_tokens:,} tokens).
Before continuing, you MUST save memories and signal completion.

## Required Steps:

### 1. Write Short-Term Summary
Write a summary to `memory/short_term/recent.md` containing:

```markdown
# Recent Conversation Summary

## Current Task
[What you're working on]

## Key Progress
- [Decisions made]
- [Files modified]
- [Important findings]

## Tool Results
- [Key tool outputs worth preserving]

## Next Steps
- [What remains to do]
```

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
