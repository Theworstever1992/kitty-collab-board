# TASK 101 — BaseProvider Abstract Class

**Assigned:** Claude
**Status:** ✅ done
**Phase:** 1 — Provider Abstraction Layer

## Description

Create `agents/providers/base.py` with an abstract `BaseProvider` class.
All provider implementations (Anthropic, OpenAI-compat, Ollama, Gemini) inherit from this.

## Interface

```python
class BaseProvider(ABC):
    def complete(self, prompt: str, system: str = "", config: dict = {}) -> str:
        ...
    def is_available(self) -> bool:
        ...
```

## Acceptance Criteria

- [ ] ABC with `complete()` and `is_available()` abstract methods
- [ ] `config` dict accepts: `max_tokens`, `temperature`, any provider-specific extras
- [ ] Clean import: `from agents.providers.base import BaseProvider`

## Implementation Notes

Created `agents/providers/base.py` with `BaseProvider(ABC)` defining two abstract methods:
- `complete(prompt, system, config)` — call the model, return response text
- `is_available()` — check credentials/SDK availability

Also created `agents/providers/__init__.py` exporting `BaseProvider`. Clean import works as `from agents.providers.base import BaseProvider`.

## Review

**Claude review — APPROVED**

Clean and minimal. Good addition of `ProviderError` exception class — gives providers a consistent error type to raise. `get_model_name()` is a handy bonus, using `getattr` with a fallback is the right call.

One note for Qwen when implementing `openai_compat.py`: the docstring mentions `ProviderError` as the raise type but providers currently raise `RuntimeError`. Consider standardizing on `ProviderError` across all providers — it would make error handling in `GenericAgent` cleaner (catch `ProviderError` specifically rather than broad `Exception`).
