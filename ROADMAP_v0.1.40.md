# MassGen v0.1.40 Roadmap

## Overview

Version 0.1.40 focuses on OpenAI Responses API improvements and inline context path syntax.

- **OpenAI Responses /compact Endpoint** (Required): Use OpenAI's native `/compact` endpoint instead of custom summarization
- **@filename Syntax for Inline Context Paths** (Required): Add `@path/to/file` syntax to include files/directories as read-only context in prompts

## Key Technical Priorities

1. **OpenAI Responses /compact Endpoint**: Leverage API-level context compression for better efficiency
   **Use Case**: Reduce token usage and improve response quality with native compression

2. **@filename Syntax for Inline Context Paths**: Include files/directories as context using `@path` in prompts
   **Use Case**: Easily include context files in prompts without modifying YAML config

## Key Milestones

### Milestone 1: OpenAI Responses /compact Endpoint (REQUIRED)

**Goal**: Use OpenAI's native `/compact` endpoint instead of custom summarization

**Owner**: @ncrispino (nickcrispino on Discord)

**Issue**: [#739](https://github.com/massgen/MassGen/issues/739)

#### 1.1 Compact Endpoint Integration
- [ ] Research OpenAI `/compact` endpoint API
- [ ] Implement compact endpoint client
- [ ] Replace custom summarization with native endpoint
- [ ] Handle fallback for non-OpenAI backends

#### 1.2 Context Compression
- [ ] Integrate with existing context management
- [ ] Configure compression thresholds
- [ ] Test with long conversations
- [ ] Measure token savings

#### 1.3 Testing & Validation
- [ ] Unit tests for compact endpoint
- [ ] Integration tests with orchestration
- [ ] Performance benchmarks vs custom summarization
- [ ] Edge case handling

**Success Criteria**:
- OpenAI compact endpoint integrated successfully
- Token usage reduced compared to custom summarization
- Response quality maintained or improved
- Fallback works for non-OpenAI backends

---

### Milestone 2: @filename Syntax for Inline Context Paths (REQUIRED)

**Goal**: Add `@path/to/file` syntax to include files/directories as read-only context in prompts

**Owner**: @ncrispino (nickcrispino on Discord)

**Issue**: [#767](https://github.com/massgen/MassGen/issues/767)

#### 2.1 Parser Implementation
- [ ] Extract `@path` patterns from prompt text
- [ ] Remove `@path` from prompt before sending to agents
- [ ] Validate paths exist
- [ ] Support relative and absolute paths
- [ ] Handle escaped `@` with `\@`

#### 2.2 Context Path Builder
- [ ] Convert `@` references to `context_paths` format
- [ ] Merge with existing YAML config paths
- [ ] Apply smart consolidation suggestions (3+ sibling files)
- [ ] Support `@path/to/file.py` (file) and `@path/to/dir/` (directory)

#### 2.3 CLI Integration
- [ ] Tab completion for `@` paths in interactive mode
- [ ] Path existence feedback
- [ ] Error messages for non-existent paths

#### 2.4 Testing & Documentation
- [ ] Unit tests for path parsing
- [ ] Integration tests with CLI and programmatic API
- [ ] Update documentation with examples
- [ ] Add edge case handling (email addresses, escaped @)

**Success Criteria**:
- `@path/to/file` adds file as read-only context
- `@path/to/dir/` adds directory as read-only context
- Multiple `@` references work in single prompt
- Paths validated before execution
- Smart consolidation suggestion for 3+ sibling files
- Works with both CLI and programmatic API

---

## Success Criteria

### Functional Requirements

**OpenAI Responses /compact Endpoint:**
- [ ] Compact endpoint integrated
- [ ] Token savings measured and documented
- [ ] Fallback for non-OpenAI backends works
- [ ] No regression in response quality

**@filename Syntax for Inline Context Paths:**
- [ ] Path parsing works correctly
- [ ] Context paths merged with YAML config
- [ ] Smart directory consolidation implemented
- [ ] Documentation complete with examples

### Performance Requirements
- [ ] Token usage reduced with compact endpoint
- [ ] No performance degradation in existing workflows
- [ ] Path parsing is fast and efficient

### Quality Requirements
- [ ] All tests passing
- [ ] Comprehensive documentation
- [ ] Error handling is robust
- [ ] User-facing messages are clear

---

## Dependencies & Risks

### Dependencies
- **OpenAI Compact Endpoint**: OpenAI API access, Responses API support
- **@filename Syntax**: Existing `context_paths` infrastructure

### Risks & Mitigations
1. **API Changes**: *Mitigation*: Monitor OpenAI API updates, implement version checks
2. **Path Edge Cases**: *Mitigation*: Handle email addresses, escaped @, and special characters
3. **Backend Compatibility**: *Mitigation*: Implement proper fallback for non-OpenAI backends

---

## Future Enhancements (Post-v0.1.40)

### v0.1.41 Plans
- **Integrate Smart Semantic Search** (@ncrispino): Advanced semantic search capabilities ([#639](https://github.com/massgen/MassGen/issues/639))
- **Add Model Selector for Log Analysis** (@ncrispino): Choose model for `massgen logs analyze` self-analysis mode ([#766](https://github.com/massgen/MassGen/issues/766))

### v0.1.42 Plans
- **Improve Log Sharing and Analysis** (@ncrispino): Enhanced log sharing workflows ([#722](https://github.com/massgen/MassGen/issues/722))
- **Add Fara-7B for Computer Use** (@ncrispino): Support for Fara-7B model for computer use tasks ([#646](https://github.com/massgen/MassGen/issues/646))

### Long-term Vision
- **Advanced Agent Communication**: Sophisticated inter-agent protocols and negotiation
- **Adaptive Context Management**: Dynamic context windows based on task requirements
- **Tool Marketplace**: User-contributed tools and integrations
- **Cost Analytics**: Detailed cost tracking and budget management

---

## Timeline Summary

| Phase | Focus | Key Deliverables | Owner | Priority |
|-------|-------|------------------|-------|----------|
| Phase 1 | OpenAI Compact Endpoint | API integration, token savings | @ncrispino | **REQUIRED** |
| Phase 2 | @filename Syntax | Path parsing, context inclusion | @ncrispino | **REQUIRED** |

**Target Release**: January 19, 2026 (Sunday @ 9am PT)

---

## Getting Started

### For Contributors

**OpenAI Responses /compact Endpoint:**
1. Review OpenAI Responses API documentation
2. Implement compact endpoint integration
3. Add fallback for non-OpenAI backends
4. Test with various conversation lengths
5. Benchmark token savings

**@filename Syntax for Inline Context Paths:**
1. Review existing `context_paths` implementation
2. Implement path parser in `cli.py` or new module
3. Add path validation and error handling
4. Implement smart directory consolidation
5. Update documentation with examples

### For Users

- v0.1.40 brings API improvements and new prompt syntax:

  **OpenAI Responses /compact Endpoint:**
  - Native context compression via OpenAI API
  - Reduced token usage
  - Better response quality

  **@filename Syntax:**
  - Include files in prompts: `massgen "Analyze @src/utils.py"`
  - Include directories: `massgen "Review @src/"`
  - Multiple files: `massgen "Compare @old.py with @new.py"`
  - Smart consolidation for 3+ sibling files

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup and workflow
- Code standards and testing requirements
- Pull request process
- Documentation guidelines

**Contact Track Owner:**
- OpenAI Compact Endpoint: @ncrispino on Discord (nickcrispino)
- @filename Syntax: @ncrispino on Discord (nickcrispino)

---

*This roadmap reflects v0.1.40 priorities focusing on OpenAI compact endpoint and @filename syntax for inline context paths.*

**Last Updated:** January 16, 2026
**Maintained By:** MassGen Team
