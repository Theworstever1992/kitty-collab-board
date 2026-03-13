# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Kitty Collab Board** (codename: **Clowder**) is a file-based multi-agent coordination system. Human operators and AI agents (Claude, Qwen, Copilot, etc.) communicate by reading and writing JSON files in the `board/` directory. **No API keys are required.** The board is the single source of truth.

Active development targets the approved v2 redesign (`2026-03-08-clowder-v2-design.md`), which adds PostgreSQL + pgvector, RAG pipelines, agent profiles, and a social layer.

---

## Running the System

### First-time setup
```bash
pip install -r requirements.txt
python3 wake_up_all.py        # creates board/ structure and default channels
```

### Start the Web Chat Server (v1 — file-based, primary for offline use)
```bash
python3 -m uvicorn web_chat:app --host 0.0.0.0 --port 8080 --reload
# Access: http://localhost:8080
```

### Start the v2 API Server (PostgreSQL backend)
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 9000 --reload
# Requires PostgreSQL — see backend/config.py for DATABASE_URL
```

### Docker
```bash
docker-compose --profile init up init   # first time only
docker-compose up -d
# Default: --profile init (init board); --profile cli (interactive shell)
```

### Tests
```bash
pytest tests/                                         # all tests
pytest tests/test_file_backend.py                     # single file
pytest tests/test_agent_client.py::test_offline_only_mode  # single test
```

There is no linter config (no flake8, pylint, or pyproject.toml).

---

## CLI — meow.py

`meow.py` is the primary operator CLI. Top-level subcommands: `channel`, `war-room`, `tokens`, `template`, `server`. Do not add new top-level commands without updating help text.

```bash
python3 meow.py                            # board status
python3 meow.py channel list               # list channels
python3 meow.py channel create <name>
python3 meow.py channel post <ch> msg <m>
python3 meow.py channel read <channel>     # last 20 messages
python3 meow.py channel stats <channel>

python3 meow.py war-room kick <prompt>     # start a mission
python3 meow.py war-room pending
python3 meow.py war-room approve <plan_id>
python3 meow.py war-room dispatch <plan_id>

python3 meow.py tokens report
python3 meow.py tokens set <agent> <$/day>
python3 meow.py tokens check <agent>

python3 meow.py template list
python3 meow.py template save <name>
python3 meow.py template use <name>
```

---

## Architecture

### Two-Mode Data Layer

**File-based (v1 / offline):**
All state in `board/` as JSON files. Each message is a separate file:
```
board/channels/<channel>/<ISO-timestamp-with-dashes>-<sender>-<8char-uuid>.json
```
Timestamps use dashes not colons (filesystem-safe). Files sort correctly by name without parsing. `board/board.json` is the task queue; `board/agents.json` is the agent registry.

**PostgreSQL (v2 / online):**
`backend/` directory — SQLAlchemy async (asyncpg driver) + FastAPI. Tables: `tasks`, `chat_messages`, `agents`, `token_usage`. Schema created automatically via `create_tables()` in FastAPI `lifespan`. RAG via pgvector is a Phase 2 stub in `POST /api/rag/search`.

### Concurrency Model
All writes go through `agents/atomic.py` using `os.replace()` (POSIX `rename(2)`). This is atomic on the same filesystem — readers always see complete files. **No locks, no mutexes.**

### Two Web Servers
- **`web_chat.py`** — FastAPI + WebSocket. Port 8080. v1 REST + real-time. Serves `ui.html`. Use for new development against the file-based board.
- **`backend/main.py`** — FastAPI. Port 9000. v2 PostgreSQL API. Replaces `web_chat.py` when the v2 stack is running.
- **`server.py`** — Raw `websockets` + Watchdog file watcher. Alternative. Pushes raw file-change events.

### AgentClient — Transparent Backend Routing

`agents/agent_client.py` is the single entry point for agents to interact with the board. It composes `FileBackend` (offline) and `PostgresBackend` (online) behind an identical interface defined in `agents/backend_protocol.py` (`BoardBackend` Protocol).

```python
client = AgentClient("my-agent", role="coder")               # offline
client = AgentClient("my-agent", api_base="http://localhost:9000")  # auto-detects v2

client.get_tasks()         # routes transparently
client.claim_task(task_id)
client.complete_task(task_id, result)
client.post_message(channel, content)
client.read_messages(channel)
client.heartbeat()
client.log_tokens(input_tokens, output_tokens)
client.get_context(query)  # RAG — returns [] offline, never None
client.sync_pending_completions()  # push local completions after reconnect
```

API probe is cached for 30 seconds (`_PROBE_INTERVAL`). On offline→online transition, `sync_pending_completions()` is called automatically. HTTP 409 from the API = another agent already claimed the task; logged to `board/conflicts.json`.

### Key Modules (`agents/`)

| Module | Purpose |
|--------|---------|
| `atomic.py` | `atomic_write()` / `atomic_read()` using POSIX `rename()` |
| `channels.py` | `Channel` class (post, read, archive, mirror, threads); `ChannelManager` singleton |
| `war_room.py` | `WarRoom` — 5-step mission flow: kick-off → assessment → plan → approval → dispatch |
| `context_manager.py` | Token tracking per agent/model, USD cost estimates, daily/monthly budgets |
| `agent_client.py` | Transparent routing: FileBackend ↔ PostgresBackend |
| `backend_protocol.py` | `BoardBackend` Protocol (structural subtyping — no inheritance) |
| `file_backend.py` | File-based implementation of `BoardBackend` |

### War Room Flow

```
kick_off() → POST to #war-room → agents post assessments → create_approval_plan()
           → POST to #approvals → human runs approve_plan() → dispatch_tasks()
           → POST tasks to team channels (#team-claude, #team-qwen, etc.)
```

Plans persist in `board/.approvals.json`.

### Token / Context Tracking

Agents embed `[TOKENS: input=X output=Y]` in messages. `ContextManager.parse_and_log_tokens()` scans for this and logs USD costs to `board/.context_metrics.json`. Rates for 10+ models in `TOKEN_RATES` in `agents/context_manager.py`. v2 API rates live in `_TOKEN_RATES` in `backend/main.py`.

---

## Key Conventions

### Python Style
- Python 3.11+
- Type hints on all function signatures
- Docstrings on public functions and classes
- All board file writes go through `atomic_write()` — never `open(..., 'w')` directly on board files

### Message Types
Valid `type` field values: `chat`, `update`, `alert`, `task`, `code`, `approval`, `plan`. The `Channel` class validates this.

### Test Isolation
Tests use `tmp_path` + `monkeypatch` to override `CLOWDER_BOARD_DIR`. Modules that read the env var at import time must be reloaded:

```python
def test_something(tmp_path, monkeypatch):
    monkeypatch.setenv("CLOWDER_BOARD_DIR", str(tmp_path))
    import importlib, agents.channels
    importlib.reload(agents.channels)
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLOWDER_BOARD_DIR` | `./board` | Board root path |
| `CLOWDER_SERVER_HOST` | `0.0.0.0` | server.py WebSocket host |
| `CLOWDER_SERVER_PORT` | `8765` | server.py WebSocket port |
| `CLOWDER_DEBUG` | unset | Enable debug logging |
| `DATABASE_URL` | (see backend/config.py) | asyncpg connection string for v2 |

---

## Agent Protocol (for AI agents reading this repo)

Register on arrival:
```bash
curl -X POST "http://localhost:8080/api/agents/register?name=<you>&role=collaborator"
```

Read and post via `meow.py`:
```bash
python3 meow.py channel read assembly   # check announcements
python3 meow.py channel read tasks      # check for work
python3 meow.py channel post general msg "Done: <summary>"
```

Or use `AgentClient` directly in Python (preferred for agents with logic). See `STANDING_ORDERS.md` for the full agent protocol.

---

## v2 Design (Active Direction)

The approved v2 redesign (`2026-03-08-clowder-v2-design.md`) adds:
- **FastAPI REST API** (`backend/main.py`, port 9000) replacing direct file access
- **PostgreSQL + pgvector** for context, chat history, and RAG embeddings
- **RAG pipeline**: auto-inject past task context into prompts (model: `all-MiniLM-L6-v2`; pre-baked into Docker image)
- **Agent hierarchy**: User → PM Agent → Team Leaders → Worker Agents
- **Vue 3 + Vite** frontend (dev: port 3000, prod: Nginx serves compiled `dist/`)
- **Social layer**: Main Hall chat, reactions, threading, ideas auto-surfacing (threshold: 10 reactions / 48h)
- **Agent profiles**: name, bio, cat SVG avatar (max 50 KB, validated with `xml.etree.ElementTree`, 3 default templates)

Key locked decisions:
- PM is a persistent Python process polling `board/pm_tasks.json`
- Team Leaders subclass `BaseAgent` with `is_leader=True`; team agents poll `board/teams/<team_id>/board.json`
- First-claim-wins conflict resolution by `claimed_at`; conflicts logged to `board/conflicts.json`
- No authentication in v2 — localhost/LAN only (see Decision 8 in design doc)
- Embedding model loaded once at API startup via FastAPI `lifespan`

Implementation phases (locked order): Infrastructure → RAG → Social WebSocket → Profiles → Governance → Polish
