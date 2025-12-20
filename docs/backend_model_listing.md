# Backend Model Listing Discovery (MAS-163)

## Overview
This document clarifies current backend model discovery behavior to inform
future UX improvements without introducing execution-time dependencies.

MassGen’s runtime model handling is **string-based and provider-agnostic**.

Model selection relies on:
- User-supplied model strings
- Provider prefixes (e.g. `groq/`, `together/`, `cerebras/`)
- LiteLLM backend routing

There are **no strict provider-specific model registries** used during execution.

As a result, automatic model listing primarily improves:
- CLI UX (interactive selection, suggestions)
- Documentation accuracy
- Example configurations

It does **not** affect core execution or routing.

---
## Non-Goals

- Introducing runtime dependencies on provider model registries
- Enforcing provider-specific model allowlists
- Blocking execution based on model availability checks

## Current Model Listing Status

| Provider     | Automatic Listing | Notes |
|-------------|------------------|-------|
| OpenRouter  | ✅ Yes | Models fetched dynamically via API |
| OpenAI      | ❌ Not implemented | Requires manual updates |
| Anthropic   | ❌ Not implemented | Requires manual updates |
| Groq        | ❌ Not implemented | Requires manual updates |
| Nebius      | ❌ Not implemented | Requires manual updates |
| Together AI | ❌ Not implemented | Requires manual updates |
| Cerebras    | ❌ Not implemented | Requires manual updates |
| Qwen        | ❌ Not implemented | Requires manual updates |
| Moonshot    | ❌ Not implemented | Requires manual updates |

---

## Findings

- Runtime model handling does **not** rely on provider registries
- Provider inference occurs via model name prefixes
- Tests confirm no hardcoded provider-specific model registries are enforced at runtime
- Model names primarily appear in:
  - documentation
  - CLI examples
  - presentation artifacts

---
These findings suggest that automatic model discovery should be treated as
a UX concern rather than a runtime requirement.

## Recommendations

1. Clearly document which providers support automatic model discovery
2. Mark providers requiring manual updates
3. Explore API-based model listing only for UX-facing components
4. Avoid introducing execution-time dependencies on model registries

## Follow-Up Work

This clarification enables safe exploration of automatic model listing
for providers such as Groq, OpenAI, Anthropic, and others without introducing
execution-time dependencies or requiring API keys at the initial stage.

Potential next steps include:
- Investigating which providers expose public or unauthenticated model listing APIs
- Leveraging LiteLLM or third-party wrappers for consolidated model discovery
- Implementing automatic listing exclusively in UX-facing components (e.g., CLI setup)
- Clearly documenting providers that must remain manually updated

