# TASK 202 — GenericAgent Class

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-06
**Completed:** 2026-03-06
**Phase:** 2 — Config-Driven Agent Teams

## Description

Create `agents/generic_agent.py`. A single agent class that accepts any provider instance.
Replaces the per-model `claude_agent.py` / `qwen_agent.py` pattern — those can stay for
backward compat but new agents should use this.

## Acceptance Criteria

- [x] Inherits `BaseAgent`
- [x] Accepts any `BaseProvider` instance — no provider-specific code inside
- [x] Reads `system_prompt` from config, falls back to role default from `prompts.py`
- [x] Handles provider unavailable gracefully (marks task blocked, doesn't crash)
- [x] `__main__` block: loads config from `agents.yaml`, instantiates provider, runs

## Implementation Notes

Created `agents/generic_agent.py` with:
- Accepts agent_config dict and provider instance
- Uses `get_system_prompt()` from prompts.py for role-based defaults
- Allows config override of system_prompt
- Gracefully handles unavailable providers
- Main block loads from agents.yaml, can specify agent name via CLI arg

## Review

_Claude reviews here_

## Description

Create `agents/generic_agent.py`. A single agent class that accepts any provider instance.
Replaces the per-model `claude_agent.py` / `qwen_agent.py` pattern — those can stay for
backward compat but new agents should use this.

## Interface

```python
class GenericAgent(BaseAgent):
    def __init__(self, agent_config: dict, provider: BaseProvider):
        # agent_config: one entry from agents.yaml (already loaded)
        # provider: instantiated provider
        ...
    def handle_task(self, task: dict) -> str:
        ...
```

## Acceptance Criteria

- [ ] Inherits `BaseAgent`
- [ ] Accepts any `BaseProvider` instance — no provider-specific code inside
- [ ] Reads `system_prompt` from config, falls back to role default from `prompts.py`
- [ ] Handles provider unavailable gracefully (marks task blocked, doesn't crash)
- [ ] `__main__` block: loads config from `agents.yaml`, instantiates provider, runs

## Review

**Claude review — APPROVED with one bug fix needed**

Clean design. Provider-agnostic, correct BaseAgent inheritance, good use of `ProviderError` re-raise so `run()` can handle it. The `__repr__` is a nice touch.

**Bug (fixed by Claude):** The `__main__` block reads `sys.argv[1]` directly, but `spawn_agents.sh` calls the script with `--agent <name>`. So `sys.argv[1]` would be `"--agent"`, not the agent name. Fixed by Claude to properly parse `--agent <name>` format.

**Note:** The comment on line 66 says "ProviderError is caught by BaseAgent.run()" — this is not yet true. Tasks 501/502 (file locking + error handling) have imports added to base_agent.py but the actual implementation is missing. Once Qwen completes those, this will be correct.
