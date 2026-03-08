# TASK 104 — OllamaProvider

**Assigned:** Claude
**Status:** ✅ done
**Phase:** 1 — Provider Abstraction Layer

## Description

Create `agents/providers/ollama.py` implementing `BaseProvider` using Ollama's REST API.
No extra SDK needed — use `urllib` or the `openai` SDK with `base_url="http://localhost:11434/v1"`.

## Acceptance Criteria

- [ ] Inherits `BaseProvider`
- [ ] `base_url` configurable (default: `http://localhost:11434`)
- [ ] No new dependencies if using openai SDK compat mode
- [ ] `is_available()` pings Ollama health endpoint — returns False if not running
- [ ] Clear error if model not pulled locally

## Implementation Notes

Created `agents/providers/ollama.py` with `OllamaProvider(BaseProvider)`:
- Uses `openai` SDK with `base_url` pointing to `{base_url}/v1` (default: `http://localhost:11434/v1`)
- `api_key` set to "ollama" (Ollama does not require a real key)
- `is_available()` does a GET to `{base_url}/api/tags` via `urllib.request` — returns False on connection error
- Raises `RuntimeError` with `ollama pull <model>` instructions if model not found locally
- `base_url` is configurable via constructor (default: `http://localhost:11434`)
- No new dependencies beyond the already-required `openai` SDK

## Review

**Claude self-review — APPROVED with one flag for Qwen**

Health check via `urllib.request` with 3s timeout is clean — no new deps needed. Lazy OpenAI client init matches the Anthropic pattern. Helpful `ollama pull <model>` error message is a good UX touch.

**Flag for Qwen:** The model-not-found detection on line 42-43 is string-matching on the error message (`"model"` and `"not found"` in error_str). This could be fragile if Ollama changes its error format. If you see a cleaner way to detect this (e.g. checking error status code), feel free to improve it — but it works for now.
