# TASK 201 — agents.yaml Schema + Example

**Assigned:** Claude
**Status:** done
**Phase:** 2 — Config-Driven Agent Teams

## Description

Create `agents.yaml` at the project root. This is the single file that defines the entire agent team.
No code changes needed to add a new model — just add an entry here.

## Schema

```yaml
agents:
  - name: string           # unique agent name, used for logs and board registration
    model: string          # model identifier (e.g. claude-sonnet-4-6, qwen-plus, llama3.2)
    provider: string       # one of: anthropic, openai_compat, ollama, gemini
    role: string           # reasoning | code | research | summarization | general
    max_tokens: int        # default 4096
    api_key_env: string    # env var name for API key (optional, providers have sensible defaults)
    base_url: string       # for openai_compat and ollama only
    system_prompt: string  # optional override; if omitted, role default from prompts.py is used
```

## Acceptance Criteria

- [x] Valid YAML with all 4 current providers represented as examples
- [x] claude entry (anthropic)
- [x] qwen entry (openai_compat + DashScope base_url)
- [x] llama entry (ollama)
- [x] gemini entry
- [x] Comments explaining each field

## Implementation Notes

Created `/agents.yaml` at project root with all four agents: claude (anthropic/reasoning),
qwen (openai_compat/code), llama (ollama/summarization), gemini (gemini/research).
Each entry is fully commented. All fields from the schema are demonstrated.

## Review

_Qwen reviews here_
