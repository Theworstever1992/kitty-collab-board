# TASK 102 — AnthropicProvider

**Assigned:** Claude
**Status:** ✅ done
**Phase:** 1 — Provider Abstraction Layer

## Description

Create `agents/providers/anthropic_provider.py` implementing `BaseProvider` using the Anthropic SDK.
Replaces the inline API call in `claude_agent.py`.

## Acceptance Criteria

- [ ] Inherits `BaseProvider`
- [ ] Reads `ANTHROPIC_API_KEY` from env if not passed
- [ ] Supports `max_tokens` from config (default 4096)
- [ ] `is_available()` returns False if no API key or SDK missing
- [ ] Handles `anthropic.APIError` gracefully — raises with clear message

## Implementation Notes

Created `agents/providers/anthropic_provider.py` with `AnthropicProvider(BaseProvider)`:
- Reads `ANTHROPIC_API_KEY` from env if not passed in constructor
- `complete()` calls `client.messages.create()` with model, max_tokens (default 4096), system prompt, and user message
- `is_available()` returns False if SDK not importable or no api_key set
- Catches `anthropic.APIError` and re-raises as `RuntimeError` with clear message
- Uses `try/except ImportError` around `import anthropic`

## Review

**Claude review — APPROVED with minor note**

Lazy client init (`_get_client()`) is the right pattern — avoids failing at import time if key isn't set yet. System prompt correctly omitted when empty.

Minor nit: default model is `claude-3-5-sonnet-20241022` — model comes from `agents.yaml` in practice so this won't matter, but worth updating the default to `claude-sonnet-4-6` for correctness.

**For Qwen:** Mirror this lazy-init pattern in `openai_compat.py`. Also note that `AnthropicProvider` raises `RuntimeError` — consider raising `ProviderError` (defined in `base.py`) for consistency.
