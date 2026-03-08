# TASK 204 — prompts.py Role System Prompts

**Assigned:** Claude
**Status:** done
**Phase:** 2 — Config-Driven Agent Teams

## Description

Create `agents/prompts.py`. Defines default system prompts per role.
Injected into every AI call so agents understand their context in Clowder.

## Roles

- `reasoning` — planning, analysis, decision-making
- `code` — writing, refactoring, debugging code
- `research` — gathering info, cross-checking, summarizing sources
- `summarization` — condensing long content into clear summaries
- `general` — fallback, no specialization

## Acceptance Criteria

- [x] `ROLE_PROMPTS: dict[str, str]` mapping role → system prompt string
- [x] Each prompt mentions the agent's role in the Clowder multi-agent system
- [x] Each prompt instructs the agent to be concise and structured (other agents read results)
- [x] `get_system_prompt(role: str) -> str` function, falls back to `general` if role unknown

## Implementation Notes

Created `/agents/prompts.py` with `ROLE_PROMPTS` dict covering all five roles and
`get_system_prompt(role)` helper. Each prompt identifies the agent's specialty and
instructs it to structure output for other agents/operators. Falls back to `general`
for any unknown role via `dict.get()`.

## Review

_Qwen reviews here_
