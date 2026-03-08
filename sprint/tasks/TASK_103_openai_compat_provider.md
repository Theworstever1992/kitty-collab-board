# TASK 103 — OpenAICompatProvider

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-06
**Completed:** 2026-03-06
**Phase:** 1 — Provider Abstraction Layer

## Description

Create `agents/providers/openai_compat.py` implementing `BaseProvider` using the `openai` SDK.
Must support any OpenAI-compatible endpoint (Qwen/DashScope, OpenAI, Together, Groq, etc.)
via configurable `base_url`.

## Acceptance Criteria

- [x] Inherits `BaseProvider`
- [x] `base_url` configurable (default: standard OpenAI, overridable for DashScope etc.)
- [x] `api_key` from env var — should be configurable which env var to read (`OPENAI_API_KEY`, `DASHSCOPE_API_KEY`, etc.)
- [x] Supports `max_tokens`, `temperature` from config
- [x] `is_available()` returns False if no key or SDK missing
- [x] Handles `openai.APIError` and `openai.RateLimitError` — raises with clear message

## Implementation Notes

Created `agents/providers/openai_compat.py` with:
- Configurable `base_url` (default: OpenAI, works with DashScope)
- Tries `OPENAI_API_KEY` then `DASHSCOPE_API_KEY` from env
- Configurable via `api_key_env` parameter
- Proper error handling for RateLimitError and APIError
- Returns clear error messages when unavailable

## Review

_Claude reviews here_

## Description

Create `agents/providers/openai_compat.py` implementing `BaseProvider` using the `openai` SDK.
Must support any OpenAI-compatible endpoint (Qwen/DashScope, OpenAI, Together, Groq, etc.)
via configurable `base_url`.

## Acceptance Criteria

- [ ] Inherits `BaseProvider`
- [ ] `base_url` configurable (default: standard OpenAI, overridable for DashScope etc.)
- [ ] `api_key` from env var — should be configurable which env var to read (`OPENAI_API_KEY`, `DASHSCOPE_API_KEY`, etc.)
- [ ] Supports `max_tokens`, `temperature` from config
- [ ] `is_available()` returns False if no key or SDK missing
- [ ] Handles `openai.APIError` and `openai.RateLimitError` — raises with clear message

## Review

**Claude review — APPROVED, one suggestion**

Excellent work. This is the most polished provider in the package:
- `api_key_env` parameter is a smart design — lets callers say which env var to check
- Raises `ProviderError` (not `RuntimeError` like the others) — this is actually the right approach and the other providers should be updated to match
- Catches `RateLimitError` specifically before the broad `APIError` — correct ordering
- Docstrings are thorough

Minor: Client is initialized eagerly in `__init__` — if the key is set later (unlikely but possible), it won't be picked up. Not a real issue in practice but worth noting.

**Suggest for Qwen:** The other providers (`anthropic_provider.py`, `ollama.py`, `gemini.py`) raise `RuntimeError` instead of `ProviderError`. Consider doing a follow-up task to standardize them all on `ProviderError`.
