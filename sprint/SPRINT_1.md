# Sprint 1 — Universal Agent System

**Goal:** Any AI model drops in, spins up, joins the team. No code changes required.
**Phases:** 1 (Providers) + 2 (Config/Generic Agent) + 3 (Spawn) + 5 (Reliability)
**Agents:** Claude (reasoning/architecture) + Qwen (code/implementation)

---

## Task Board

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 101 | BaseProvider abstract class | Claude | ✅ done |
| 102 | AnthropicProvider | Claude | ✅ done |
| 103 | OpenAICompatProvider | Qwen | ✅ done |
| 104 | OllamaProvider | Claude | ✅ done |
| 105 | GeminiProvider | Claude | ✅ done |
| 201 | agents.yaml schema + example | Claude | ✅ done |
| 202 | GenericAgent class | Qwen | ✅ done |
| 203 | config.py loader | Qwen | ✅ done (missing providers fixed by Claude) |
| 204 | prompts.py role system prompts | Claude | ✅ done |
| 301 | spawn_agents.sh (Linux/Mac) | Claude | ✅ done |
| 302 | meow.py spawn — Linux + agents.yaml | Claude | ✅ done |
| 501 | File locking (filelock) | Qwen | ✅ done (lock scope fixed by Claude) |
| 502 | Error handling in run() | Qwen | ✅ done |
| 503 | Fix mission_control.py BOARD_DIR | Claude | ✅ done |
| 504 | requirements.txt update | Claude | ✅ done |

---

## Rules

- **Claim a task:** Change status to `🔄 in_progress` and put your name in Assigned
- **Complete a task:** Change status to `✅ done`, update the task file with what you did
- **Review:** Leave a review comment in `reviews/` after reviewing the other agent's work
- **Don't duplicate:** Check status before starting. If it's `🔄`, leave it alone.
- **Flag blockers:** Change status to `🚫 blocked` and note why in the task file

---

## Division of Labour

**Claude** owns: architecture, providers (Anthropic/Ollama/Gemini), config schema, prompts, spawn, fixes
**Qwen** owns: OpenAI-compat provider, GenericAgent, config loader, file locking, error handling

---

## Sprint Completion Criteria

- [x] `agents/providers/` package with all 4 providers (Anthropic, OpenAI-compat, Ollama, Gemini)
- [x] `agents.yaml` works to define a team
- [x] `agents/generic_agent.py` runs any provider
- [x] `meow spawn` works on Linux
- [x] No race conditions on board writes (full read-modify-write locked)
- [x] Agents recover from API errors without dying

## Sprint 1 — COMPLETE ✅
