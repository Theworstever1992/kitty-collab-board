# Architecture — Kitty Collab Board (Clowder)

**Version:** 1.0.0
**Last Updated:** 2026-03-08

---

## Overview

Kitty Collab Board (codename: **Clowder**) is a multi-agent AI collaboration system where multiple AI agents run as independent processes, coordinate via a shared JSON task board, and complete work assigned by a human operator.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Human Operator                              │
│              (meow.py CLI / Mission Control TUI)                │
│                  (Web Dashboard: localhost:3000)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Web Backend                          │
│                  (localhost:8000/api/*)                         │
│  ┌─────────────┬─────────────┬─────────────┬─────────────────┐ │
│  │ REST API    │ WebSocket   │ Analytics   │ Health Monitor  │ │
│  │ /api/tasks  │ /api/ws     │ /api/analytics │ /api/health │ │
│  └─────────────┴─────────────┴─────────────┴─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared State Layer                           │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │ board.json   │ agents.json  │ audit.json   │ metrics.json │ │
│  │ (tasks)      │ (registry)   │ (audit log)  │ (analytics)  │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│                     (board/ directory)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  Claude Agent    │ │   Qwen Agent     │ │  Generic Agent   │
│  (Anthropic)     │ │  (DashScope)     │ │  (Any Provider)  │
└──────────────────┘ └──────────────────┘ └──────────────────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
                  ┌───────────────────────┐
                  │   BaseAgent Class     │
                  │  (agents/base_agent)  │
                  └───────────────────────┘
```

---

## Core Components

### 1. Shared State (`board/`)

File-based shared state for inter-agent coordination.

| File | Purpose | Format |
|------|---------|--------|
| `board.json` | Task list with status | JSON array |
| `agents.json` | Agent registry | JSON object |
| `audit.json` | Append-only audit log | JSON array |
| `metrics.json` | Analytics data | JSON object |
| `recurring.json` | Recurring task definitions | JSON object |
| `dependencies.json` | Task dependency graph | JSON object |

**Task Status Flow:**
```
pending → in_progress → done
   ↓           ↓
blocked ←─────┘
```

### 2. Agent System (`agents/`)

All agents inherit from `BaseAgent`:

```python
class BaseAgent:
    def register()          # Announce in agents.json
    def deregister()        # Mark offline
    def get_tasks()         # Read pending tasks
    def claim_task(id)      # Lock task (filelock)
    def complete_task(id)   # Mark done
    def log(msg, level)     # Structured logging
    def run()               # Main loop
    def handle_task(task)   # OVERRIDE THIS
```

**Provider Abstraction:**
```python
class BaseProvider(ABC):
    @abstractmethod
    def complete(prompt, system, config) -> str
    @abstractmethod
    def is_available() -> bool
```

**Available Providers:**
- `AnthropicProvider` — Claude models
- `OpenAICompatProvider` — Qwen, Groq, Together, any OpenAI-compatible
- `OllamaProvider` — Local models
- `GeminiProvider` — Google Gemini

### 3. Web API (`web/backend/`)

FastAPI application serving:
- REST API for CRUD operations
- WebSocket for real-time updates
- Analytics endpoints
- Health monitoring

### 4. Web Frontend (`web/frontend/`)

React + TypeScript dashboard:
- Task board with real-time updates
- Agent status panel
- Analytics dashboard
- Log streaming viewer

### 5. CLI Tools

| Tool | Purpose |
|------|---------|
| `meow.py` | Main CLI entry point |
| `mission_control.py` | TUI dashboard |
| `wake_up.py` | Initialize board, print aliases |

---

## Data Flow

### Task Lifecycle

1. **Creation:** Human adds task via CLI, TUI, or Web UI
2. **Polling:** Agents poll `board.json` every 5 seconds
3. **Claiming:** Agent claims task (filelock ensures atomicity)
4. **Execution:** Agent calls AI provider with task prompt
5. **Completion:** Agent writes result, marks task done
6. **Metrics:** System records completion metrics

### Agent Registration

1. Agent starts, calls `register()`
2. Writes entry to `agents.json` with status=online
3. Updates `last_seen` every 30 seconds (heartbeat)
4. On shutdown, calls `deregister()` (status=offline)
5. Health monitor tracks agent status

---

## Key Design Decisions

### File-Based Shared State

**Why:** Simple, human-readable, no external dependencies

**Trade-offs:**
- ✅ Easy to debug and inspect
- ✅ Works across languages/processes
- ❌ Race conditions possible (mitigated by filelock)
- ❌ Not suitable for high-frequency updates

### File Locking

Uses `filelock` library for cross-platform locking:
- Lock files: `board.json.lock`, `agents.json.lock`
- Timeout: 10 seconds
- Fallback: No-op lock if library unavailable

### Optimistic Task Claiming

Agents check-then-claim with file locking:
- Prevents corrupted writes
- Occasional duplicate claims possible under heavy load
- Acceptable for typical workloads

### Structured Logging

Two-tier logging:
- **JSON logs** (`logs/*.log`) — machine-parseable, rotated
- **Audit log** (`board/audit.json`) — append-only, all state changes

---

## Extension Points

### Adding a New Agent

1. Create agent class inheriting from `BaseAgent`
2. Implement `handle_task(task)` method
3. Add to `agents.yaml` configuration
4. Run via `python agents/generic_agent.py --agent <name>`

### Adding a New Provider

1. Create `agents/providers/my_provider.py`
2. Inherit from `BaseProvider`
3. Implement `complete()` and `is_available()`
4. Add to `build_provider()` in `agents/config.py`

### Adding a New Board

```python
from agents.multiboard import get_multiboard_manager

manager = get_multiboard_manager()
manager.create_board("project_x", "Project X tasks")
manager.switch_board("project_x")
```

---

## Performance Characteristics

| Metric | Target | Typical |
|--------|--------|---------|
| Agent startup | < 2s | ~1s |
| Task claim latency | < 100ms | ~50ms |
| Memory per agent | < 200MB | ~100MB |
| Board file size | < 10MB | ~1MB |
| WebSocket latency | < 500ms | ~100ms |

---

## Security Considerations

- **API keys** stored in `.env` (never commit)
- **No input validation** on task prompts
- **No sandboxing** — agents run with full Python capabilities
- **File permissions** — default system permissions
- **CORS** — configured for localhost:3000 in dev

---

## Deployment Architecture

### Docker Deployment

```yaml
services:
  api:
    image: ghcr.io/theworstever1992/clowder-api:1.0.0
    ports: ["8000:8000"]
    volumes: [./board:/app/board, ./logs:/app/logs]
  
  claude:
    image: ghcr.io/theworstever1992/clowder-claude:1.0.0
    depends_on: [api]
  
  qwen:
    image: ghcr.io/theworstever1992/clowder-qwen:1.0.0
    depends_on: [api]
```

### Native Deployment

```bash
# Start API
uvicorn web.backend.main:app --host 0.0.0.0 --port 8000

# Start agents
python agents/generic_agent.py --agent claude
python agents/generic_agent.py --agent qwen
```

---

## Monitoring

### Health Endpoints

- `GET /health` — API health check
- `GET /api/health` — Agent health summary
- `GET /api/health/alerts/active` — Active alerts

### Metrics Endpoints

- `GET /api/analytics/summary` — System summary
- `GET /api/analytics/completion-trend` — Completion trend
- `GET /api/analytics/agent-leaderboard` — Agent rankings

### Logs

- Agent logs: `logs/<agent_name>.log` (JSON format)
- Audit log: `board/audit.json`
- API logs: `logs/api.log`

---

## Future Enhancements

- [ ] Database backend option (SQLite/PostgreSQL)
- [ ] Message queue for high-frequency updates (Redis)
- [ ] Native desktop app (Tauri)
- [ ] Mobile app (React Native)
- [ ] Advanced scheduling (cron-like recurring tasks)
- [ ] Multi-tenant support

---

*For implementation details, see source code in `agents/`, `web/`, and `board/` directories.*
