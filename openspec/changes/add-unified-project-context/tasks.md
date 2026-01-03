# Tasks: Add Unified Project Context

## 1. Core Infrastructure

- [ ] 1.1 Create `massgen/context/project_context.py` with `load_project_context()` function
- [ ] 1.2 Add `project_context: Optional[str]` to ExecutionContext in `base_with_custom_tool_and_mcp.py`
- [ ] 1.3 Load project context in `stream_with_tools()` and pass to ExecutionContext

## 2. System Prompt Integration

- [ ] 2.1 Add CONTEXT.md creation instructions to `system_message_builder.py`
- [ ] 2.2 Include template and examples for what to put in CONTEXT.md

## 3. Multimodal Tools - Understanding

- [ ] 3.1 Update `read_media.py` to add `project_context` to @context_params
- [ ] 3.2 Update `understand_image.py` to inject context into OpenAI API call
- [ ] 3.3 Update `understand_audio.py` to inject context into API calls
- [ ] 3.4 Update `understand_video.py` to inject context into all backend API calls
- [ ] 3.5 Update `understand_file.py` to inject context into API call

## 4. Multimodal Tools - Generation

- [ ] 4.1 Update `generate_media.py` to add `project_context` to @context_params
- [ ] 4.2 Update `generation/_image.py` to inject context into prompts
- [ ] 4.3 Update `generation/_video.py` to inject context into prompts
- [ ] 4.4 Update `generation/_audio.py` to inject context into prompts

## 5. Subagent Integration

- [ ] 5.1 Update `_copy_context_files()` to auto-copy CONTEXT.md if it exists
- [ ] 5.2 Update `_build_subagent_system_prompt()` to include context from CONTEXT.md
- [ ] 5.3 Ensure subagents are read-only (cannot create/modify CONTEXT.md)

## 6. Configuration

- [ ] 6.1 Add `project_context` to excluded config params in `base.py`
- [ ] 6.2 Add `project_context` to excluded config params in `_api_params_handler_base.py`

## 7. Testing

- [ ] 7.1 Add unit tests for `load_project_context()` function
- [ ] 7.2 Test context injection in understand_image
- [ ] 7.3 Test subagent CONTEXT.md auto-copy
