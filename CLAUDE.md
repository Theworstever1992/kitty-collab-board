# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Kitty Collab Board** (codename: **Clowder**) is a multi-agent AI collaboration system. Multiple AI agents (Claude, Qwen, etc.) run as independent processes, poll a shared JSON task board, claim and complete tasks, and report results. A human operator manages the board via `meow.py` / `mission_control.py`.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in API keys
python wake_up.py     # create board/ and logs/ dirs, print PowerShell aliases
```

Required env vars: `ANTHROPIC_API_KEY`, `DASHSCOPE_API_KEY`

Optional path overrides (used by Docker): `CLOWDER_BOARD_DIR`, `CLOWDER_LOG_DIR`

## Common Commands

**Board & Task Management:**
```bash
python meow.py                  # show board status
python meow.py mc               # open Mission Control TUI (curses on Linux, simple on Windows)
python meow.py wake             # re-initialize board + print aliases
python meow.py task "do thing"  # quick-add a task
python meow.py add              # add a task interactively
python meow.py spawn            # spawn agents via PowerShell (Windows only)
```

**Running Agents:**
```bash
python agents/claude_agent.py   # run Claude agent
python agents/qwen_agent.py     # run Qwen agent
```

**Web API & Frontend:**
```bash
# Start FastAPI backend (port 8000)
uvicorn web.backend.main:app --reload

# Start React frontend (port 3000) — requires Node.js
cd web/frontend && npm install && npm run dev
```

**Testing:**
```bash
pytest                          # run all tests
pytest tests/test_board.py -v   # run board tests
pytest tests/unit/test_retry.py -v  # run specific test file
```

**Docker (recommended for deployment):**
```bash
docker-compose up -d            # start all services (API + Claude + Qwen agents)
python mission_control.py       # monitor from host
docker-compose down             # stop all services
```

## Architecture

### Shared State (`board/`)
- `board/board.json` — task list; agents poll, claim, and complete tasks by mutating this file
- `board/agents.json` — agent registry; agents write their entry on startup and update `last_seen` on each heartbeat
- `logs/` — per-agent log files created on first write

**Task statuses:** `pending` → `in_progress` → `done` | `blocked`

**Task fields:** `id` (e.g. `task_<unix_timestamp>`), `title`, `description`, `prompt`, `status`, `created_at`, `claimed_by`, `claimed_at`, `result`, `handoff` (optional), `role`, `priority`, `skills`

### Agent Pattern
All agents inherit from `agents/base_agent.py:BaseAgent`. The base class handles:
- Registration/heartbeat (read-modify-write `agents.json`)
- Board polling (every 5 seconds by default)
- Task claiming/completion with optimistic locking (no file locking; race conditions possible under heavy load)
- Logging to both stdout and `logs/<agent_name>.log`
- Handoff protocol (task delegation between agents)
- Health monitoring (last_seen heartbeat tracking)

Subclasses override only `handle_task(task: dict) -> str` to implement custom logic.

**Key BaseAgent methods:**
- `register()` / `deregister()` — manage agent registration in `agents.json`
- `claim_task(id)` — attempt to claim a pending task
- `complete_task(id, result)` — mark task done with result string
- `handoff_task(target, notes)` — delegate task to another agent
- `accept_handoff()` / `decline_handoff()` — respond to handoffs
- `log(msg, level)` — write to log file and stdout
- `run()` — main loop: register → heartbeat → poll → claim → handle → complete

### Agent Implementations
- `claude_agent.py` — uses `anthropic` SDK; invokes Claude model (configurable, default `claude-opus-4-6`)
- `qwen_agent.py` — uses OpenAI-compatible endpoint via DashScope; model `qwen-plus`
- `generic_agent.py` — template for adding new provider-based agents

**To add a new agent:**
1. Subclass `BaseAgent` and implement `handle_task()`
2. Choose a provider from `agents/providers/` (Anthropic, OpenAI-compatible, Ollama, Gemini)
3. Add a service entry to `docker-compose.yml`
4. Update `STANDING_ORDERS.md` agent roster

### Operator Tools
- `meow.py` — CLI dispatcher for board operations (status, add tasks, spawn agents)
- `mission_control.py` — interactive TUI for board management (curses on Unix, simple loop on Windows)
  - Keys: `q`=quit, `r`=refresh, `a`=add task, `h`=handoff, `A`=archive done tasks, Up/Down=navigate, Enter=view result
- `wake_up.py` — initializes `board/` and `logs/` directories, prints PowerShell aliases
- `config.py` / `agents.yaml` — centralized configuration for agents and thresholds

### Web API & Frontend

**FastAPI Backend** (`web/backend/main.py`, port 8000):
- REST endpoints for board operations (`GET /api/tasks`, `POST /api/tasks`, etc.)
- WebSocket for real-time board updates
- Health monitoring (`GET /api/health`, `/api/health/{agent}`)
- Log streaming for agents
- JSON state management without direct file access

**React Frontend** (`web/frontend/`, port 3000):
- Task board visualization and management
- Agent health dashboard with real-time status
- Log viewer for each agent
- Built with React 18, TypeScript, Vite, Bootstrap 5

### Health Monitoring & Alerts
`agents/health_monitor.py` provides:
- Agent health tracking via heartbeat intervals (thresholds: 60s warning, 300s offline)
- Health status endpoints for web API
- Alert channels (console, log file, webhook)
- Discord/Slack webhook support for agent alerts

### Additional Subsystems
- `agents/retry.py` — exponential backoff retry logic for resilient task handling
- `agents/audit.py` — board mutation audit logging for debugging
- `agents/providers/` — abstraction layer for LLM providers (Anthropic, OpenAI-compatible, Ollama, Gemini)
- `logging_config.py` — centralized logging configuration

### Agent Protocol
See `STANDING_ORDERS.md`. Agents must:
- Register on startup and maintain heartbeat
- Read the board before acting
- Avoid duplicate claimed tasks
- Log all significant actions
- Flag blockers (set status to `blocked`)
- Hand off rather than abandon tasks (via `handoff_task()`)
- Communicate only through the board JSON — no direct agent-to-agent calls

## Development

### Board State Inspection
```bash
# View task board (JSON)
cat board/board.json | python -m json.tool

# View agent registry and health
cat board/agents.json | python -m json.tool

# View agent logs
tail -f logs/claude_agent.log
tail -f logs/qwen_agent.log
```

### Debugging Patterns
1. **Agent not claiming tasks?** Check if `status` field matches expected state, if agent is registered in `agents.json`, if it's polling (check logs for poll messages)
2. **Task stuck in progress?** Check `claimed_by` and `claimed_at`; may need manual intervention (edit JSON if safe)
3. **Web API not connecting?** Ensure backend is running on port 8000 and CORS origins are configured correctly
4. **Frontend not updating?** Check browser console for WebSocket connection errors; verify API endpoint in `web/frontend/src/api/client.ts`

### Testing
- Tests live in `tests/` with pytest configuration in `pytest.ini`
- Use `pytest -v` for verbose output, `-x` to stop on first failure
- Test coverage includes board operations, retry logic, and provider integration

### Code Organization
- **Agents:** Implement custom logic by subclassing `BaseAgent`; handlers should be idempotent
- **Providers:** Add new LLM providers in `agents/providers/base.py` by subclassing `BaseProvider`
- **Web routes:** Add new FastAPI endpoints in `web/backend/main.py` and consume via `web/frontend/src/api/client.ts`
- **Config:** Use environment variables (`.env`) for deployment flexibility; runtime config in `config.py` and `agents.yaml`
