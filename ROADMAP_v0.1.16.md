# MassGen v0.1.16 Roadmap

## Overview

Version 0.1.16 focuses on quickstart improvements and accurate token/price counting, enhancing the onboarding experience and cost tracking capabilities.

- **Make Quickstart More Intuitive** (Required): 🚀 Ensure tools and skills work through PyPI for better onboarding
- **Integrate LiteLLM Registry** (Required): 💰 More accurate token and price counting across providers

## Key Technical Priorities

1. **Make Quickstart More Intuitive**: Ensure tools and skills work properly through PyPI installation
   **Use Case**: Enable users to get started with MassGen quickly and easily, with tools and skills working out of the box via PyPI

2. **Integrate LiteLLM Registry**: More accurate token counting across all providers
   **Use Case**: Provide accurate token usage and cost information across all supported model providers

## Key Milestones

### 🎯 Milestone 1: Make Quickstart More Intuitive (REQUIRED)

**Goal**: Ensure tools and skills work properly through PyPI installation for better onboarding

**Owner**: @ncrispino (nickcrispino on Discord)

**Issue**: [#544](https://github.com/massgen/MassGen/issues/544)

#### 1.1 PyPI Installation Improvements
- [ ] Ensure all tools work correctly when installed via PyPI
- [ ] Ensure all skills work correctly when installed via PyPI
- [ ] Verify dependencies are properly bundled
- [ ] Test installation on clean environments
- [ ] Cross-platform installation testing (Windows, macOS, Linux)

#### 1.2 Onboarding Experience
- [ ] Improved first-run experience
- [ ] Better documentation and guidance during initial setup
- [ ] Streamlined configuration process
- [ ] Clear error messages for common setup issues
- [ ] Interactive setup wizard improvements

#### 1.3 Documentation Updates
- [ ] Updated quickstart guide
- [ ] Installation troubleshooting guide
- [ ] Common issues and solutions
- [ ] Video tutorials (optional)
- [ ] Example configurations for new users

**Success Criteria**:
- ✅ Tools and skills work correctly when installed via PyPI
- ✅ Quickstart process is streamlined and intuitive
- ✅ New users can get started within 5 minutes
- ✅ Clear error messages guide users through setup issues
- ✅ Documentation covers all common scenarios

---

### 🎯 Milestone 2: Integrate LiteLLM Registry (REQUIRED)

**Goal**: Integrate LiteLLM registry for more accurate token and price counting across all providers

**Owner**: @ncrispino (nickcrispino on Discord)

**Issue**: [#543](https://github.com/massgen/MassGen/issues/543)

#### 2.1 LiteLLM Integration
- [ ] Integrate LiteLLM's model registry
- [ ] Fetch up-to-date pricing information
- [ ] Support for all major providers (OpenAI, Anthropic, Google, etc.)
- [ ] Automatic registry updates
- [ ] Fallback mechanisms for offline usage

#### 2.2 Token Counting
- [ ] Accurate token counting across all supported providers
- [ ] Provider-specific tokenizer integration
- [ ] Real-time token usage tracking
- [ ] Token usage reporting and analytics
- [ ] Token estimation before API calls

#### 2.3 Price Calculation
- [ ] Precise price calculation for different models
- [ ] Support for input/output token pricing differences
- [ ] Currency conversion support (optional)
- [ ] Cost tracking for multi-agent workflows
- [ ] Cost estimation and budgeting features

#### 2.4 Integration & Testing
- [ ] Integration with existing cost tracking system
- [ ] Unit tests for token counting accuracy
- [ ] Integration tests with various providers
- [ ] Performance testing for overhead impact
- [ ] Documentation and usage examples

**Success Criteria**:
- ✅ Token counting is accurate across all supported providers
- ✅ Price calculations match actual provider pricing
- ✅ Cost tracking works for multi-agent workflows
- ✅ Registry updates automatically with new model pricing
- ✅ Minimal performance overhead from integration

---

## Success Criteria

### Functional Requirements

**Make Quickstart More Intuitive:**
- [ ] All tools work via PyPI installation
- [ ] All skills work via PyPI installation
- [ ] Quickstart documentation is clear and complete
- [ ] Error messages are helpful and actionable
- [ ] Setup process is streamlined

**Integrate LiteLLM Registry:**
- [ ] LiteLLM registry integrated
- [ ] Token counting is accurate
- [ ] Price calculations are correct
- [ ] Cost tracking functional
- [ ] Registry updates automatically

### Performance Requirements
- [ ] PyPI installation is fast
- [ ] Token counting has minimal overhead
- [ ] Price lookups are cached efficiently
- [ ] Startup time is not significantly impacted
- [ ] Memory usage is reasonable

### Quality Requirements
- [ ] All tests passing
- [ ] Comprehensive documentation
- [ ] Configuration examples provided
- [ ] Error handling is robust
- [ ] User-facing messages are clear

---

## Dependencies & Risks

### Dependencies
- **Make Quickstart More Intuitive**: PyPI packaging, dependency management, cross-platform testing, documentation system
- **Integrate LiteLLM Registry**: LiteLLM library, provider APIs, caching system, cost tracking infrastructure

### Risks & Mitigations
1. **PyPI Packaging Issues**: *Mitigation*: Comprehensive testing on clean environments, CI/CD for package validation
2. **Dependency Conflicts**: *Mitigation*: Careful dependency pinning, virtual environment testing
3. **LiteLLM API Changes**: *Mitigation*: Version pinning, fallback mechanisms, monitoring for updates
4. **Pricing Accuracy**: *Mitigation*: Regular validation against provider pricing pages, user feedback integration
5. **Performance Overhead**: *Mitigation*: Caching, lazy loading, performance profiling

---

## Future Enhancements (Post-v0.1.16)

### v0.1.17 Plans
- **Improve Consistency of Memory & Tool Reminders** (@ncrispino): Enhance consistency of memory retrieval across agents
- **MassGen Terminal Evaluation** (@ncrispino): Enable MassGen to evaluate and improve its own frontend/UI

### v0.1.18 Plans
- **Integrate RL into MassGen** (@qidanrui @praneeth999): Reinforcement learning integration for agent optimization
- **Smithery MCP Tools Support** (@ncrispino): Integration with Smithery to expand available MCP tools

### Long-term Vision
- **Universal Rate Limiting**: Rate limiting for all backends
- **Advanced Tool Selection**: Machine learning-based tool selection
- **Cost Analytics**: Detailed cost tracking and budget management
- **Tool Performance Metrics**: Analytics on tool usage patterns

---

## Timeline Summary

| Phase | Focus | Key Deliverables | Owner | Priority |
|-------|-------|------------------|-------|----------|
| Phase 1 | Quickstart | PyPI installation, onboarding improvements, documentation | @ncrispino | **REQUIRED** |
| Phase 2 | Token Counting | LiteLLM integration, accurate pricing, cost tracking | @ncrispino | **REQUIRED** |

**Target Release**: November 24, 2025 (Monday @ 9am PT)

---

## Getting Started

### For Contributors

**Phase 1 - Make Quickstart More Intuitive:**
1. Review current PyPI installation process (Issue #544)
2. Identify tools/skills that don't work via PyPI
3. Fix packaging and dependency issues
4. Update documentation
5. Test on clean environments
6. Create troubleshooting guide

**Phase 2 - Integrate LiteLLM Registry:**
1. Integrate LiteLLM library (Issue #543)
2. Implement token counting for all providers
3. Add price calculation logic
4. Integrate with cost tracking system
5. Add comprehensive tests
6. Document usage and configuration

### For Users

- v0.1.16 brings quickstart improvements and accurate cost tracking:

  **Make Quickstart More Intuitive:**
  - Tools and skills work out of the box via PyPI
  - Improved onboarding experience
  - Better documentation and guidance
  - Streamlined configuration process
  - Clear error messages for common issues

  **Integrate LiteLLM Registry:**
  - Accurate token counting across all providers
  - Precise cost calculations
  - Up-to-date pricing information
  - Better cost tracking for multi-agent workflows
  - Cost estimation before running tasks

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup and workflow
- Code standards and testing requirements
- Pull request process
- Documentation guidelines

**Contact Track Owners:**
- Quickstart & LiteLLM: @ncrispino on Discord (nickcrispino)

---

*This roadmap reflects v0.1.16 priorities focusing on quickstart improvements and accurate token/price counting.*

**Last Updated:** November 21, 2025
**Maintained By:** MassGen Team
