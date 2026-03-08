# Changelog

All notable changes to Kitty Collab Board (Clowder) are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-03-08 — Production Launch 🎉

### Added

**Logging & Performance (6002–6005)**
- **Structured JSON logging** — `logging_config.py` with rotating file handlers (10MB max, 5 backups); console + file output; exception formatting with stack traces; log level config (6002)
- **Performance profiling** — `agents/profiler.py` using `psutil`; tracks memory, CPU, startup time; results logged to `logs/profiling.json` (6003)
- **Memory optimization** — Agent footprint reduced to <200MB; queue-based task polling; lazy imports in providers (6004)
- **Startup optimization** — Agent startup time <2 seconds; parallel provider initialization; pre-loaded config (6005)

**Advanced Features (6022–6025)**
- **Task dependencies** — `blocked_by` field in task JSON; `DependencyManager` in `agents/dependencies.py`; agents can't claim blocked tasks; comprehensive tests in `tests/test_dependencies.py` (6022)
- **Recurring tasks** — `RecurringTaskScheduler` in `agents/recurring.py`; RRULE-based recurrence; auto-creates task instances; full test coverage in `tests/test_recurring.py` (6024)
- **Multi-board support** — `BoardManager` in `agents/board_manager.py`; isolated task boards per team/project; board switching in web UI; tests in `tests/test_multiboard.py` (6025)

**Analytics & Metrics (6031–6034)**
- **Task completion metrics** — `TaskMetrics` in `agents/metrics.py`; tracks completion count, time to completion, success rate; persisted to `board/metrics.json` (6031)
- **Agent performance tracking** — `AgentMetrics` tracks tasks claimed, completed, failed per agent; performance scoring (6032)
- **Analytics dashboard** — React component `AnalyticsDashboard.tsx` with real-time charts; task completion trends, agent performance comparison (6033)
- **Report export** — CSV/PDF export for metrics; `ReportGenerator` with customizable date ranges and filters (6034)

**Native Desktop App (6052–6055)**
- **Tauri app scaffold** — Cross-platform desktop app in `native-app/`; builds on macOS (Intel + Apple Silicon), Windows (x64 + ARM64), Linux (6052)
- **System tray integration** — Tray icon with menu; quick access to task board without window focus (6053)
- **Native notifications** — Desktop notifications via OS-native APIs; alerts for task completion, agent health warnings (6054)
- **Offline-first architecture** — Sync queue for operations; automatic retry when connectivity restored; conflict resolution (6055)

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
