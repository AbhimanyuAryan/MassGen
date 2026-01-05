# Backend Model Listing Discovery (MAS-163)

## Overview
This document clarifies current backend model discovery behavior to inform
future UX improvements without introducing execution-time dependencies.

MassGen's runtime model handling is **string-based and provider-agnostic**.

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
## Model Discovery Tiers

Automatic model discovery is intentionally scoped to UX-facing components
and may vary by provider capability.

Three discovery tiers are supported:

1. **Live Unauthenticated Discovery**
   - Providers exposing public model registries
   - Example: OpenRouter
   - No API keys required

2. **Authenticated Discovery** ✅ IMPLEMENTED
   - Enabled when user provides API keys
   - Filters specialized models (audio, image, embedding, etc.)
   - Sorts by creation date (newest first)
   - Puts recommended model at top
   - Strictly non-blocking and UX-only

3. **Static Provider Manifests**
   - Curated model lists stored in-repo (capabilities.py)
   - Fallback when API keys not available
   - Used for CLI UX, docs, and examples only

## Non-Goals

- Introducing runtime dependencies on provider model registries
- Enforcing provider-specific model allowlists
- Blocking execution based on model availability checks

## Current Model Listing Status

| Provider     | Discovery Method           | Filtering | Notes |
|-------------|---------------------------|-----------|-------|
| OpenRouter  | Live (unauthenticated)    | Tool support | Public API, filters to tool-supporting models |
| OpenAI      | ✅ Authenticated          | ✅ Chat only | Filters out audio/image/embedding, sorted by date |
| Anthropic   | Static manifest           | N/A | No public model registry |
| Groq        | ✅ Authenticated          | ✅ Chat only | Filters out whisper/guard/orpheus models |
| Together AI | ✅ Authenticated          | ✅ Chat only | Uses `type` field to filter chat/language/code |
| Nebius      | Authenticated (basic)     | None | Enterprise-gated |
| Cerebras    | Authenticated (basic)     | None | Limited availability |
| Qwen        | Authenticated (basic)     | None | Deployment-specific |
| Moonshot    | Authenticated (basic)     | None | Closed ecosystem |
| Fireworks   | Authenticated (basic)     | None | OpenAI-compatible |
| POE         | Authenticated (basic)     | None | Limited API |

---

## Implementation Details

### Filtering Logic

Models are filtered to show only chat/text models. Excluded:
- Audio/speech models (whisper, tts, orpheus, *-audio*)
- Image/video models (dall-e, sora, *-image*)
- Embedding models (text-embedding-*)
- Safety/moderation models (*-guard*, *-moderation*)
- Fine-tuned models (ft:*)
- Specialized APIs (*-search-api*, *-deep-research*)

### Sorting

When `sort_by_created=True`:
- Models sorted by creation timestamp (newest first)
- Default/recommended model moved to top of list

### Files Modified

- `massgen/utils/model_catalog.py` - Core discovery logic
- `massgen/utils/model_matcher.py` - Provider list for dynamic discovery
- `massgen/frontend/web/server.py` - WebUI API endpoint

---

## Findings

- Most providers do not expose unauthenticated model listing APIs
- Any automatic discovery beyond OpenRouter requires API keys
- Provider inference occurs via model name prefixes
- Tests confirm no hardcoded provider-specific model registries are enforced at runtime

## Remaining Work

Providers that could benefit from enhanced filtering:
- Nebius, Cerebras, Qwen, Moonshot, Fireworks - currently use basic OpenAI-compatible fetch
- POE - uses dedicated fetcher but no filtering

Potential improvements:
- Add `type` field filtering for other providers if their APIs support it
- Consider caching improvements for frequently accessed model lists
