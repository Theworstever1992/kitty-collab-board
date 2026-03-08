# TASK 203 — config.py Loader

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-06
**Completed:** 2026-03-06
**Phase:** 2 — Config-Driven Agent Teams

## Description

Create `agents/config.py`. Loads `agents.yaml` and instantiates the correct provider
for each agent config. The bridge between YAML and running agents.

## Interface

```python
def load_agents_config(path: str = "agents.yaml") -> list[dict]:
    """Load raw agent configs from YAML."""
    ...

def build_provider(agent_config: dict) -> BaseProvider:
    """Instantiate the correct provider from config."""
    # maps provider name -> provider class
    ...

def build_agent(agent_config: dict) -> GenericAgent:
    """Build a fully configured GenericAgent from one YAML entry."""
    ...
```

## Acceptance Criteria

- [ ] `load_agents_config()` returns list of dicts, raises clear error if file missing
- [ ] `build_provider()` maps: `anthropic` → `AnthropicProvider`, `openai_compat` → `OpenAICompatProvider`, `ollama` → `OllamaProvider`, `gemini` → `GeminiProvider`
- [ ] Unknown provider raises `ValueError` with helpful message listing valid options
- [ ] `api_key_env` from config passed to provider if present
- [ ] `base_url` from config passed to provider if present

## Review

**Claude review — NEEDS FIX (fixed by Claude)**

Good structure. Validation, fallback path search, clear error messages — all solid.

**Bug (fixed by Claude):** `provider_map` only contains `openai_compat`. The other three providers (`anthropic`, `ollama`, `gemini`) are left as TODO comments waiting for "Claude implements them" — but Claude did implement them (Tasks 101-105 are done). Fixed by Claude to import and register all four providers.

Once fixed, `build_provider()` can instantiate any of the four configured providers correctly.
