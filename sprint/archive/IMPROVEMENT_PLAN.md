# 🚀 Improvement Plan — Kitty Collab Board (Clowder)

**Created:** 2026-03-06  
**Status:** Approved for implementation  
**Collaborators:** Claude, Qwen, Human Operator

---

## 📊 Project Analysis Summary

### Current State
The Kitty Collab Board is a multi-agent AI collaboration system with a solid foundation:
- Clean agent inheritance architecture (`BaseAgent` pattern)
- JSON-based shared state board
- Docker + local deployment options
- TUI-based Mission Control
- GitHub Actions CI/CD for Docker publishing

### Strengths ✅
- Well-structured `BaseAgent` class pattern
- Human-readable board state (JSON)
- Comprehensive documentation (`CLAUDE.md`, `STANDING_ORDERS.md`)
- Flexible CLI (`meow.py`)
- Containerized deployment ready

### Critical Gaps 🔴
- No file locking → race conditions on task claiming
- No task timeout/reclaim → abandoned tasks stay stuck forever
- No error recovery → agents crash silently on API failures
- Windows-only agent spawning → excludes Linux/Mac users
- No test suite → regressions undetected
- No multi-UI strategy → terminal-only access

---

## 📋 Implementation Roadmap

### Phase 1: Provider Abstraction Layer (Foundation)

Make AI backends swappable with a common interface.

| # | Task | Description | Files |
|---|------|-------------|-------|
| 1.1 | Create `agents/providers/` package | New package structure for provider implementations | `agents/providers/__init__.py` |
| 1.2 | `BaseProvider` abstract class | Define `complete(prompt, system, config) -> str` interface | `agents/providers/base.py` |
| 1.3 | Anthropic provider | Wrap Anthropic SDK | `agents/providers/anthropic_provider.py` |
| 1.4 | OpenAI-compatible provider | Support Qwen, OpenAI, any compatible endpoint | `agents/providers/openai_compat.py` |
| 1.5 | Ollama provider | Local models via Ollama REST API | `agents/providers/ollama.py` |
| 1.6 | Gemini provider | Google Generative AI SDK | `agents/providers/gemini.py` |

**Dependencies:** `google-generativeai>=0.4.0`

---

### Phase 2: Config-Driven Agent Teams

Define the entire team in YAML. No code changes to add models.

| # | Task | Description | Files |
|---|------|-------------|-------|
| 2.1 | Create `agents.yaml` schema | Define: name, model, provider, role, max_tokens, base_url, system_prompt | `agents.yaml` |
| 2.2 | Generic agent class | Single agent that accepts any provider + config | `agents/generic_agent.py` |
| 2.3 | Config loader | Load agent configs from YAML at startup | `agents/config.py` |
| 2.4 | Role-based system prompts | Inject role-specific prompts per agent | `agents/prompts.py` |
| 2.5 | Update `STANDING_ORDERS.md` | Document the new agent roster format | `STANDING_ORDERS.md` |

**Dependencies:** `pyyaml>=6.0`

---

### Phase 3: Cross-Platform Spawning

One command to launch the full team on any OS.

| # | Task | Description | Files |
|---|------|-------------|-------|
| 3.1 | Linux/Mac spawn script | Bash script to launch agents as background processes | `spawn_agents.sh` |
| 3.2 | Update `meow.py spawn` | Read `agents.yaml` and spawn all configured agents | `meow.py` |
| 3.3 | Single agent spawn | `meow.py spawn --agent <name>` for individual agents | `meow.py` |
| 3.4 | Docker sync | Auto-generate `docker-compose.yml` services from `agents.yaml` OR document manual sync | `docker-compose.yml` or script |

---

### Phase 4: Task Routing

Route tasks to the right agent by role.

| # | Task | Description | Files |
|---|------|-------------|-------|
| 4.1 | Add `role` field to tasks | Optional field in `board.json` task schema | `board/board.json` schema |
| 4.2 | Role-based claiming logic | Agents skip tasks that don't match their role | `agents/base_agent.py` |
| 4.3 | CLI role assignment | `meow task "do thing" --role code` sets role on creation | `mission_control.py`, `meow.py` |
| 4.4 | Mission Control display | Show task role in TUI dashboard | `mission_control.py` |

---

### Phase 5: Reliability & Hardening

Critical fixes for production use.

| # | Task | Description | Files |
|---|------|-------------|-------|
| 5.1 | **File locking** | Use `filelock` for atomic board.json writes (cross-platform) | `agents/base_agent.py` |
| 5.2 | **Error handling** | try/except in `run()` → mark task `blocked` on failure | `agents/base_agent.py` |
| 5.3 | **Stale task watchdog** | Reset `in_progress` tasks >5 min old back to `pending` | `mission_control.py` or background service |
| 5.4 | **Fix env var handling** | Ensure `mission_control.py` reads `CLOWDER_BOARD_DIR` | `mission_control.py` |
| 5.5 | **API retry logic** | Exponential backoff for transient API failures | `agents/providers/*.py` |

**Dependencies:** `filelock>=3.12.0`

---

### Phase 6: Testing & Code Quality

Prevent regressions and improve maintainability.

| # | Task | Description | Files |
|---|------|-------------|-------|
| 6.1 | Pytest setup | Configure pytest with async support | `pytest.ini`, `tests/conftest.py` |
| 6.2 | Board operation tests | Test claim, complete, release operations | `tests/test_board.py` |
| 6.3 | Agent lifecycle tests | Test registration, heartbeat, deregistration | `tests/test_agent.py` |
| 6.4 | Provider tests | Mock API tests for each provider | `tests/test_providers.py` |
| 6.5 | Type hints | Add complete typing across all modules | All `.py` files |
| 6.6 | Structured logging | Replace custom logging with Python `logging` (JSON format) | `agents/base_agent.py` |
| 6.7 | Centralize config | Move magic numbers (poll intervals, timeouts) to config | `config.py` |

**Dependencies:** `pytest>=7.4.0`, `pytest-asyncio>=0.21.0`

---

### Phase 7: Multi-UI Strategy (Parallel Tracks)

Three interfaces, one shared backend API.

#### Track A: TUI (Maintain & Enhance)
| # | Task | Description | Files |
|---|------|-------------|-------|
| 7.A1 | Keep existing TUI | Maintain `mission_control.py` curses interface | `mission_control.py` |
| 7.A2 | Keyboard shortcuts | Quick actions: claim, refresh, filter by status | `mission_control.py` |
| 7.A3 | Task result viewer | Display completed task results inline | `mission_control.py` |
| 7.A4 | Agent health display | Distinguish registered-but-dead vs running | `mission_control.py` |

#### Track B: Web-Based GUI
| # | Task | Description | Tech Stack |
|---|------|-------------|------------|
| 7.B1 | FastAPI backend | REST API + WebSocket for real-time updates | FastAPI, uvicorn |
| 7.B2 | React frontend | Dashboard with task board, agent status, log viewer | React + TypeScript, Bootstrap |
| 7.B3 | Real-time sync | WebSocket for live board updates | WebSocket |
| 7.B4 | Log streaming | Live tail of agent logs in browser | WebSocket + file tailing |
| 7.B5 | Task management | Add, edit, delete, reassign tasks via UI | React frontend |

**Dependencies:** `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`, `websockets>=12.0`

#### Track C: Native GUI (Future)
| # | Task | Description | Tech Stack |
|---|------|-------------|------------|
| 7.C1 | Architecture design | Plan Tauri/Electron app with shared API layer | Tauri (Rust) or Electron |
| 7.C2 | System tray integration | Background agent with tray controls | Tauri system tray |
| 7.C3 | Native notifications | OS-level alerts for task completion/blockers | Native OS APIs |
| 7.C4 | Offline-first | Local board cache, sync when backend available | LocalStorage/SQLite |

**Architecture Note:** All three UIs share a common backend API layer for consistent behavior.

---

### Phase 8: Feature Enhancements

Advanced collaboration features.

| # | Task | Description | Files |
|---|------|-------------|-------|
| 8.1 | Task priority system | Add priority field (critical/high/normal/low), sort queue | `board/board.json` schema |
| 8.2 | Agent handoff protocol | Explicit task transfer between agents with notes | `agents/base_agent.py`, `STANDING_ORDERS.md` |
| 8.3 | Board audit log | Track all state changes for debugging and replay | `board/audit.json` |
| 8.4 | Health monitoring & alerts | Notify operator when agents go offline or hit rate limits | `mission_control.py`, optional webhooks |
| 8.5 | Board archival | Move `done` tasks to `board/archive.json` after N days | `mission_control.py` |
| 8.6 | Verbose status | `meow status --verbose` dumps full task results | `meow.py` |

---

## 📦 Complete Dependencies List

```txt
# Existing
anthropic>=0.20.0
openai>=1.0.0
rich>=13.0.0
python-dotenv>=1.0.0

# Phase 1: Providers
google-generativeai>=0.4.0

# Phase 2: Config
pyyaml>=6.0

# Phase 5: Reliability
filelock>=3.12.0

# Phase 6: Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Phase 7: Web GUI
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0
```

---

## 🎯 Success Criteria

| Phase | Completion Criteria |
|-------|---------------------|
| Phase 1 | All 6 providers implemented and tested |
| Phase 2 | New agent can be added via YAML only (no code changes) |
| Phase 3 | `meow spawn` works on Windows, Linux, and Mac |
| Phase 4 | Role-based task routing functional |
| Phase 5 | No race conditions, no stuck tasks, agents recover from errors |
| Phase 6 | 80%+ test coverage, structured logs parseable by tools |
| Phase 7 | All three UIs functional with shared API backend |
| Phase 8 | Priority tasks handled first, agent handoffs work, audit trail exists |

---

## 📝 Implementation Notes

### Backward Compatibility
- Existing `board.json` format must remain readable during migration
- Legacy agent files (`claude_agent.py`, `qwen_agent.py`) can coexist during transition

### Docker Support
- All changes must work in containerized deployment
- Volume mounts for `board/` and `logs/` must be preserved

### Cross-Platform
- No Windows-only or Unix-only features
- Test on Windows (PowerShell), Linux (bash), macOS (zsh)

### Incremental Rollout
- Each phase should be independently deployable
- No phase should block another unless explicitly noted

### Agent Protocol
- All agents must follow `STANDING_ORDERS.md`
- New features must be documented in standing orders

---

## 🔗 Related Documents

- `README.md` — User-facing documentation
- `CLAUDE.md` — Claude Code context
- `STANDING_ORDERS.md` — Agent rules and protocol
- `TODO.md` — Claude's original roadmap (superseded by this plan)
- `.github/copilot-instructions.md` — GitHub Copilot guidance

---

*This plan is the authoritative roadmap for Kitty Collab Board development. All agents should reference this document when working on improvements.*
