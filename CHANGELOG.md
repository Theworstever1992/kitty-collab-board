# Changelog

All notable changes to Kitty Collab Board (Clowder) are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — Sprint 6

### Added
- **Skills-based task routing** — tasks can declare `skills: list[str]`; agents only claim tasks where they have all required skills (6021)
- **Task templates** — `meow template [list|save|use|delete]`; templates stored in `board/templates.json` with `{placeholder}` substitution in prompts (6023)
- **Docker Compose multi-service** — `api`, `claude-agent`, `qwen-agent` services with health checks and `depends_on: service_healthy` ordering (6011)
- **CI/CD pipeline** — GitHub Actions workflow runs pytest on Python 3.11 and 3.12 on every push/PR to `main` (6013)
- **Health check endpoints** — `GET /health` (Docker liveness probe, returns 503 if board directory missing) + `/api/health*` agent monitoring endpoints (6014)
- **Centralized config system** — `config.py` with typed dataclasses (`BoardConfig`, `AgentConfig`, `APIConfig`, `WebConfig`, `AlertConfig`), `get_config()` singleton, validation on startup (6001, Qwen)
- **Complete documentation suite** — `docs/API.md`, `docs/USER_GUIDE.md`, `docs/AGENT_DEVELOPER_GUIDE.md`, `docs/DEPLOYMENT.md`, `docs/TROUBLESHOOTING.md` (6041–6045)
- **Native GUI decision** — `docs/NATIVE_GUI_DECISION.md` documents Tauri recommendation over Electron with full evaluation (6051)

### Fixed
- `decline_handoff()` now correctly clears `claimed_by` and `claimed_at` when returning task to pending state (was leaving stale owner)
- `GET /api/agents` double-read bug — now reads `agents.json` once per request
- `PUT /api/tasks/{id}` now validates status field against allowed values, returns 422 for invalid status
- Health monitor env var — now supports both `CLOWDER_AGENT_WARNING_SECONDS` (canonical) and legacy `HEALTH_WARNING_SECONDS`

---

## [Sprint 5] — Real-Time + Health Monitoring

### Added
- **Real-time board push** — WebSocket `/api/ws/board` now pushes updates via asyncio `board_watcher()` polling `board.json` mtime every 500ms; no external dependencies (5001)
- **Live log streaming** — WebSocket `/api/ws/logs` tails agent log files; client sends `{"agent": "name"}` to select which log; concurrent multi-agent tailing supported (5002)
- **Board archival** — `archive_done_tasks()` moves done tasks to `board/archive.json` with `archived_at` timestamp; accessible via `A` key in TUI and `meow archive` CLI (5003)
- **TUI result viewer** — Mission Control curses loop supports Up/Down arrow navigation; Enter opens full-screen result pane (`curses_show_result`); `A` key to archive (5004)
- **Agent health display** — `AgentPanel` component uses `/api/health` endpoint; shows `online`/`warn Xs`/`offline Xs` badges; alert count in header (5011)
- **Health alerts badge** — `HealthAlerts` component in navbar shows red badge with active alert count + popover with details; polls every 15s (5012)

### Added (Sprint 4 completion — Claude took over from Kimi)
- **Health monitoring module** — `agents/health_monitor.py`: `HealthMonitor`, `AgentHealth`, `Alert`, `AlertChannels`, `WebhookSender`; Discord/Slack auto-detection; configurable thresholds (4031–4035)
- **Handoff UI** — Mission Control `h` key opens handoff dialog; `print_handoffs()` and `cli_handoff_task()` CLI helpers (4024)

---

## [Sprint 4] — Web Frontend + Handoff Protocol

### Added
- **FastAPI backend** — `web/backend/main.py`: full REST API for board and agents; CORS middleware (4001)
- **React+TypeScript frontend** — Vite scaffold with Bootstrap 5, React Icons; `TaskBoard`, `AgentPanel`, `TaskCard`, `TaskModal`, `LogViewer` components (4011–4016)
- **Handoff protocol design** — `docs/HANDOFF_PROTOCOL_DESIGN.md`; task `handoff` dict schema defined (4021)
- **Handoff implementation** — `BaseAgent` methods: `handoff_task`, `accept_handoff`, `decline_handoff`, `cancel_handoff`, `get_pending_handoffs`, `check_handoff_expiry`; 10-minute expiry (4022–4023)

---

## [Sprint 3] — Provider System + Agent Spawning

### Added
- Provider abstraction layer (`agents/providers/`) — `BaseProvider`, `AnthropicProvider`, `OpenAICompatProvider`, `OllamaProvider`, `GeminiProvider`
- `agents.yaml` — declarative agent configuration (name, provider, model, role)
- `agents/generic_agent.py` — provider-agnostic agent driven by `agents.yaml`
- `spawn_agents.sh` — spawns all agents from `agents.yaml` in background processes (Linux/Mac)
- `meow.py spawn` command — delegates to shell script or PowerShell

---

## [Sprint 2] — Roles + Priority + Reliability

### Added
- Role-based task routing — tasks declare `role`, agents filter by matching role
- Priority system — `critical`, `high`, `normal`, `low`; tasks sorted by priority before claiming
- Stale task watchdog — marks tasks blocked if agent disappears mid-claim
- API retry logic (`agents/retry.py`) — exponential backoff for transient API errors
- Audit log (`agents/audit.py`) — records task claimed/completed/blocked events to `board/audit.log`
- File locking — `filelock.FileLock` on all board writes; `_NoOpLock` fallback if not installed

---

## [Sprint 1] — Initial Release

### Added
- `board/board.json` — shared JSON task board; tasks flow `pending → in_progress → done | blocked`
- `board/agents.json` — agent registry; agents write entry on startup, update `last_seen` on heartbeat
- `agents/base_agent.py` — `BaseAgent` class: register, heartbeat, poll, claim, complete, log
- `agents/claude_agent.py` — Anthropic SDK integration (`claude-3-5-sonnet-20241022`)
- `agents/qwen_agent.py` — OpenAI-compatible DashScope integration (`qwen-plus`)
- `meow.py` — CLI dispatcher: status, mc, wake, add, task, spawn, help
- `mission_control.py` — `add_task()`, curses TUI (Unix), simple loop (Windows), `status` CLI
- `wake_up.py` — initializes `board/` and `logs/` directories
- Docker support — `Dockerfile`, `.github/workflows/docker-publish.yml` publishes to GHCR
