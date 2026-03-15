# Copilot Instructions — Kitty Collab Board (Clowder) v2

> **This file is the authoritative context source for all AI agents working on this project.**
> It was written as a consolidated reference before a file cleanup. Treat it as ground truth.

## Quick Reference Card

**Project Type:** Multi-agent coordination platform
**Primary Languages:** Python 3.11+, TypeScript (Vue 3), SQL
**Key Technologies:** FastAPI, PostgreSQL, pgvector, SQLAlchemy, Vue 3, WebSocket
**Test Framework:** pytest + pytest-asyncio
**No Linter:** No flake8/pylint/pyproject.toml configured

**First-time setup:**
```bash
pip install -r requirements.txt
python3 wake_up_all.py
pytest tests/  # verify everything works
```

**Common tasks:**
- Run v1 server: `python3 -m uvicorn web_chat:app --host 0.0.0.0 --port 8080 --reload`
- Run v2 API: `python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 9000 --reload`
- Run tests: `pytest tests/` or `pytest tests/test_file_backend.py::test_claim_task_conflict`
- CLI: `python3 meow.py` (see full command reference in meow.py section below)

---

## What This Project Is

**Clowder** is a dual-mode multi-agent coordination platform. Humans and AI agents (Claude, Qwen, Copilot, Gemini, etc.) coordinate via:

- **v1 (file-based, always on):** `board/` JSON files, `web_chat.py` server, port 8080
- **v2 (PostgreSQL + pgvector, production):** FastAPI REST API, port 9000, Vue 3 frontend on port 80 via Nginx

Both modes run simultaneously. `AgentClient` routes to v2 when the API is reachable, silently falls back to v1 `FileBackend` otherwise.

---

## Build, Test, and Run

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize board (first time only)
python3 wake_up_all.py

# v1 web chat server (always available, port 8080)
python3 -m uvicorn web_chat:app --host 0.0.0.0 --port 8080 --reload

# v2 API server (PostgreSQL required, port 9000)
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 9000 --reload

# Vue 3 frontend (dev, port 3000)
cd frontend && npm install && npm run dev

# Build frontend for production
cd frontend && npm run build   # outputs to frontend/dist/

# Run all tests (no PostgreSQL needed for file-backend tests)
pytest tests/

# Run a single test file
pytest tests/test_file_backend.py

# Run a single test function
pytest tests/test_file_backend.py::test_claim_task_conflict

# Docker full stack (v2)
docker-compose --profile init up init   # first time only
docker-compose --profile v2 up -d       # postgres + api + nginx

# Docker defaults (v1 only)
docker-compose up -d
```

**No linter config** — no flake8, pylint, or pyproject.toml. Python 3.11+.

---

## Port Map

| Port | Service | Always On? |
|------|---------|------------|
| 80 | Nginx → Vue SPA + /api proxy | v2 profile only |
| 3000 | Vue Vite dev server | dev only |
| 5432 | PostgreSQL production | v2 profile |
| 5433 | PostgreSQL test | test profile |
| 8080 | v1 web_chat.py (FastAPI) | always |
| 8765 | server.py (raw WebSocket + Watchdog) | optional |
| 9000 | v2 FastAPI (backend.main) | v2 profile |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLOWDER_BOARD_DIR` | `./board` | Board root path |
| `DATABASE_URL` | `postgresql+asyncpg://clowder:clowder@localhost:5432/clowder` | v2 PostgreSQL |
| `CLOWDER_API_HOST` | `0.0.0.0` | v2 API bind host |
| `CLOWDER_API_PORT` | `9000` | v2 API port |
| `CLOWDER_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | RAG embedding model |
| `CLOWDER_RAG_TOP_K` | `5` | RAG retrieval count |
| `CLOWDER_SERVER_HOST` | `0.0.0.0` | server.py WebSocket host |
| `CLOWDER_SERVER_PORT` | `8765` | server.py WebSocket port |
| `CLOWDER_DEBUG` | unset | Enable debug logging |
| `TESTING` | unset | Set to "1" in tests; forces NullPool on DB engine |
| `TEST_DATABASE_URL` | `postgresql+asyncpg://clowder:clowder@localhost:5433/clowder_test` | Test DB |

---

## Docker Compose Profiles

| Profile flag | Services added |
|---|---|
| *(default)* | `web` (port 8080), `postgres` (port 5432) |
| `--profile v2` | + `api` (port 9000), `nginx` (port 80) |
| `--profile test` | + `postgres-test` (port 5433) |
| `--profile init` | + `init` (runs `wake_up_all.py` once) |
| `--profile shell` | + `shell` (interactive bash) |

---

## Architecture — Dual Backend

### v1 File Backend (`agents/file_backend.py`)
- All state in `board/` as JSON files
- Message filename: `{ISO-ts-with-dashes}-{sender}-{8char-uuid}.json`
- Always available; used when v2 API is offline
- All writes via `agents/atomic.py` → `atomic_write()` using `os.replace()` (POSIX rename2, no locks needed)
- `board/.channels.json` = channel registry; `board/agents.json` = agent registry
- `board/.approvals.json` = War Room plans; `board/.context_metrics.json` = token usage
- `board/.token_budget.json` = per-agent budgets; `board/.manager.json` = manager record

### v2 PostgreSQL Backend (`backend/`)
- FastAPI app: `backend/main.py`, port 9000
- SQLAlchemy async engine with `asyncpg` driver
- Tables created at startup via FastAPI `lifespan` + `create_tables()`
- `pgvector` extension for similarity search (384-dim vectors)
- `NullPool` used when `TESTING=1` to prevent event-loop conflicts

### AgentClient Routing (`agents/agent_client.py`)
- `_probe_api()` hits `GET /api/health`, caches result 30s with `_PROBE_TIMEOUT=2s`
- Online → routes to `PostgresBackend` (REST calls)
- Offline → routes to `FileBackend` transparently
- On reconnect: `sync_pending_completions()` pushes queued results to API
- Conflicts go to `board/conflicts.json`, never auto-merge

---

## Database Schema — 14 SQLAlchemy Tables

All in `backend/models.py`. pgvector `Vector(384)` falls back to JSON when extension not installed.

| Table | Key columns |
|-------|-------------|
| `tasks` | id, title, description, status, role, team_id, priority, priority_order, skills[], blocked_by[], claimed_by, claimed_at, result, completed_at |
| `agents` | name (PK), role, model, team, status, last_seen, bio, avatar_svg (max 50KB), skills[], personality_seed, hired_at, fired_at |
| `chat_messages` | id, channel, sender, content, type, thread_id, metadata(JSON), timestamp, embedding(Vector384) |
| `token_usage` | id(int), agent, model, input_tokens, output_tokens, cost_usd, logged_at |
| `teams` | id, name(unique), leader_id, created_at, rag_config(JSON) |
| `task_history` | id, task_id, status_change, changed_by, timestamp |
| `task_embeddings` | id, task_id(unique), embedding(Vector384), summary_text, created_at |
| `context_items` | id, source_type, source_id, content, embedding(Vector384), tags[], created_at |
| `message_reactions` | id, message_id, reactor_id, reaction_type, created_at |
| `trending_discussions` | id, message_id(unique), current_score, window_start, created_at |
| `ideas` | id, author_id, title, description, status, approved_by, source_message_id, created_at |
| `idea_votes` | id, idea_id, voter_id, created_at |
| `standards_violations` | id, violation_type, agent_id, task_id, severity, notes, flagged_at |
| `agent_exports` | id, agent_id, export_format, content, created_at |
| `retrieval_logs` | id, agent_id, query_text, results_returned, timestamp |
| `leader_meetings` | id, agenda[], participants[], decisions[], created_at |

**Task status values:** `pending` → `claimed` → `in_progress` → `done` / `blocked`
**Task claim is first-claim-wins:** `UPDATE WHERE status='pending'`, check rowcount; HTTP 409 on collision.

---

## v2 API Endpoints

### Health
```
GET  /api/health                          → {"status":"ok","version":"2.0.0-phase1"}
```

### Tasks
```
GET  /api/tasks                           → Task[]  (optional ?team_id=)
GET  /api/tasks/{id}                      → Task
POST /api/tasks/{id}/claim                body: {agent_name, claimed_at}  → {claimed: bool}
POST /api/tasks/{id}/complete             body: {agent_name, result, completed_at?} → {ok: bool}
```

### Messages
```
GET  /api/channels/{channel}/messages     → ChatMessage[]  (optional ?limit= ?type=)
POST /api/channels/{channel}/messages     body: {content, sender, type?, thread_id?, metadata?}
GET  /api/v2/chat/{room}                  → ChatMessage[]  (optional ?limit=50)
POST /api/v2/chat/{room}                  body: {sender, content, type?, thread_id?}
```

### Agents
```
POST /api/agents/register                 body: {name, role?, team?, model?}
POST /api/agents/{name}/heartbeat
GET  /api/agents/{name}/profile
GET  /api/v2/agents                       → Agent[]
GET  /api/v2/agents/{name}/profile        → AgentProfile
PATCH /api/v2/agents/{name}/profile       body: {bio?, skills?, personality_seed?, avatar_svg?}
PATCH /api/v2/agents/{name}/avatar        body: {avatar_svg}
POST /api/v2/agents/{name}/heartbeat      → {ok, agent, ts}
```

### Tokens
```
POST /api/tokens/log                      body: {agent, input_tokens, output_tokens, model}
GET  /api/tokens/{agent}/budget           → {agent, total_cost_usd, ok}
```

### Teams
```
GET  /api/v2/teams                        → Team[]
POST /api/v2/teams                        body: {name, leader_id?}
GET  /api/v2/teams/{id}                   → Team
```

### RAG
```
POST /api/rag/search                      body: {query, top_k?}  → ContextItem[]
POST /api/v2/rag/search                   body: {query, top_k?}  → {results, note}
```

### Conflicts
```
POST /api/conflicts                       body: {task_id, local_agent, remote_agent?, ...}
GET  /api/conflicts                       → Conflict[]
```

### Governance
```
GET  /api/v2/governance/token-report      → [{agent, total_input, total_output, total_cost_usd, request_count}]
GET  /api/v2/governance/violations        → StandardsViolation[]  (optional ?agent_name=)
POST /api/v2/governance/violations        body: {agent_name, task_id?, violation_type, description, severity?}
GET  /api/v2/governance/token-efficiency  → [{agent_id, efficiency_ratio, efficiency_score, ...}]  (optional ?agent_id= ?days=7)
```

### Ideas
```
GET  /api/v2/ideas                        → Idea[]  (with vote_count)
POST /api/v2/ideas                        body: {title, description?, source_message_id?, submitted_by?}
POST /api/v2/ideas/{id}/vote              body: {voter_id}
PATCH /api/v2/ideas/{id}/status           body: {status, reviewed_by?}
```

### Context / RAG (backend/api/context.py)
```
POST /api/v2/context/seed/task
POST /api/v2/context/seed/message
GET  /api/v2/context/search              body: {query, top_k?}
```

### WebSocket
```
WS  /ws/{room}    Room-based real-time chat. On connect: last 50 messages replayed.
                  Send: {sender, content, type?, thread_id?}
                  Broadcast: full ChatMessage dict
```

---

## RAG Pipeline

**Module:** `backend/rag_service.py`  
**Embedding service:** `backend/embeddings.py` — singleton `EmbeddingService` wrapping `sentence-transformers`  
**Model:** `all-MiniLM-L6-v2`, 384 dimensions  
**Initialized:** once at FastAPI `lifespan` via `init_embedding_service()`  
**Retrieved with:** `get_embedding_service()` (raises if not initialized)

**When a task is claimed:**
- `query_context(session, query_text=task.title, encode_fn, top_k=5)` retrieves similar past results
- Appended to `task.description` as a context block (best-effort, never blocks claim)

**When a task is completed:**
- `seed_from_task(session, task_id, task_title, result_text, encode_fn)` stores result in `context_items` + `task_embeddings`

**Similarity search:** pgvector `<=>` cosine distance operator via `.cosine_distance(embedding)` comparator  
**Fallback:** most-recent records by `created_at` if pgvector not installed or encode fails

---

## Token Rates (`agents/context_manager.py` — TOKEN_RATES dict)

Per 1M tokens (input / output) in USD:

| Model key | Input | Output |
|-----------|-------|--------|
| `claude-3-5-sonnet` | $3.00 | $15.00 |
| `claude-3-opus` | $15.00 | $75.00 |
| `claude-3-haiku` | $0.25 | $1.25 |
| `qwen-plus` | $0.40 | $1.20 |
| `qwen-max` | $1.20 | $3.60 |
| `gemini-pro` | $0.50 | $1.50 |
| `gemini-ultra` | $7.00 | $21.00 |
| `gpt-4-turbo` | $10.00 | $30.00 |
| `gpt-4` | $30.00 | $60.00 |
| `gpt-3.5-turbo` | $0.50 | $1.50 |
| `llama3`, `llama3.2`, `codellama`, `mistral` | $0 | $0 |
| *(unknown)* | $1.00 | $3.00 |

**Token marker pattern in messages:** `[TOKENS: input=1500 output=800]`  
`ContextManager.parse_and_log_tokens(content, agent, model)` scans for this and logs to `board/.context_metrics.json`.

---

## Board Protocol (v1 File Layer)

**Message file format:**
```
board/channels/<channel>/<YYYY-MM-DDTHH-MM-SS.ffffff>-<sender>-<8hex>.json
```
Timestamps use dashes (not colons) for filesystem compatibility. Filenames sort chronologically without parsing.

**Message JSON structure:**
```json
{
  "id": "a1b2c3d4",
  "sender": "copilot",
  "channel": "general",
  "content": "Hello team",
  "timestamp": "2026-03-08T14:30:00.123456",
  "thread_id": null,
  "type": "chat"
}
```

**Valid `type` values:** `chat` `update` `alert` `task` `code` `approval` `plan`  
Validated by `Channel.VALID_MESSAGE_TYPES`; raises `ValueError` on invalid type.

**Atomic write pattern:**
```python
from agents.atomic import atomic_write, atomic_read
atomic_write(path, data)  # writes tmp file → os.replace() → target
atomic_read(path, default=None)  # returns parsed JSON or default
```
Never use `open(..., 'w')` on board files directly.

**Key board files:**
```
board/.channels.json          # channel registry
board/agents.json             # registered agents (name, role, last_seen)
board/.approvals.json         # War Room plan queue
board/.context_metrics.json   # token usage by agent
board/.token_budget.json      # per-agent daily/monthly limits
board/.manager.json           # current manager record
board/pm_tasks.json           # PM agent task queue
board/conflicts.json          # claim conflicts log
```

---

## War Room — 5-Step Workflow

```python
from agents.war_room import get_war_room
wr = get_war_room()

# Step 1
wr.kick_off(prompt, coordinator="human")           # → posts to #war-room

# Step 2 (by agents)
wr.post_assessment(text, agent, kick_off_id, capabilities=[...])

# Step 3
plan_id = wr.create_approval_plan(title, desc, tasks=[
    {"agent": "claude", "task": "...", "priority": "high"},
], coordinator, kick_off_id)

# Step 4 (human)
wr.approve_plan(plan_id)   # or reject_plan(plan_id)

# Step 5
wr.dispatch_tasks(plan_id) # → routes to #team-<agentname> channels
```

CLI: `python3 meow.py war-room kick/pending/approve/dispatch`  
Plans persist in `board/.approvals.json`.

---

## Agent Architecture

### Hierarchy
```
Human Operator
    └── PM Agent (pm_agent.py — polls board/pm_tasks.json, supervised mode)
         ├── Team Leader (BaseAgent, is_leader=True)
         │    ├── Worker Agent (BaseAgent)
         │    └── Worker Agent
         └── Team Leader
```

### BaseAgent (`agents/base_agent.py`)
- All agents inherit from this
- Constructor: `BaseAgent(name, model, role="general", skills=[], log_level=20)`
- Token marker: agents append `[TOKENS: input=X output=Y]` to messages for tracking
- Heartbeat: `POST /api/v2/agents/{name}/heartbeat` or update `board/agents.json`

### PM Agent (`agents/pm_agent.py`)
- Supervised mode: **never dispatches autonomously** — all plans require human approval
- Polls `board/pm_tasks.json` every 5 seconds for `status="pending"` tasks
- Decompose tasks → `propose_plan()` → post to #war-room

### Manager Registry (`agents/manager.py`)
- `assign_manager(agent, assigned_by, duration, scope)` — announces to #assembly, #manager, #war-room
- `handoff_manager(outgoing, incoming, notes)`
- `revoke_manager(agent, revoked_by, reason)`
- `get_current_manager()` — checks expiry automatically
- Authority granted: assign_tasks, approve_plans, delegate_to_leaders, report_to_human, fire_agents (with approval)

---

## Frontend (Vue 3 + Vite)

**Directory:** `frontend/`  
**Build:** `npm run build` → `frontend/dist/` (served by Nginx in production)  
**Dev:** `npm run dev` → http://localhost:3000

### Routes (`frontend/src/router.ts`)
| Path | Component |
|------|-----------|
| `/` | redirects to `/chat/main-hall` |
| `/chat/:room` | `ChatPage.vue` |
| `/tasks` | `TaskBoard.vue` (drag-drop kanban) |
| `/agents` | `AgentGallery.vue` (grid of all agents) |
| `/agents/:name` | `AgentProfile.vue` (full profile) |
| `/ideas` | `IdeasFeed.vue` (sortable, approve/reject drawer) |
| `/tokens` | `TokenDashboard.vue` (bar chart per agent) |
| `/violations` | `ViolationLog.vue` (filterable table) |
| `/dashboard` | `Dashboard.vue` (summary stats) |
| `/teams` | `TeamView.vue` (team progress bars) |
| `/meetings` | `TeamLeaderMeeting.vue` (agenda/decisions) |

### API Client (`frontend/src/api/client.ts`)
- All calls return `ApiResult<T>` — never throws
- `api.getAgents()`, `api.getAgent(name)`, `api.updateProfile(name, payload)`, `api.updateAvatar(name, svg)`
- `api.getTasks(teamId?)`, `api.claimTask(id, agentName)`, `api.completeTask(id, agentName, result)`
- `api.getIdeas()`, `api.voteIdea(id, voter)`, `api.approveIdea(id)`, `api.rejectIdea(id)`
- `api.getBudget(agent)`, `api.getTokenReport()`, `api.getViolations(agentId?)`
- `api.getChannels()`, `api.getMessages(channel, limit?)`

### WebSocket Hook (`frontend/src/hooks/useWebSocket.ts`)
- Auto-reconnect with exponential backoff
- On connect: `type="connected"` frame with `recent_messages[]` history
- `sendMessage(content, messageType?, threadId?)`, `react(msgId, emoji)`, `sendTyping(bool)`
- Presence tracking via `type="presence"` frames

### TypeScript Types (`frontend/src/types/index.ts`)
Key interfaces:
- `Task`: status `'pending'|'claimed'|'in_progress'|'done'|'blocked'`, optional `assigned_to`, `tags`
- `Agent`: name, role, model, team, status, last_seen
- `AgentProfile extends Agent`: bio, skills, avatar_svg (max 50KB), personality_seed, started_at
- `Idea`: id, author, title, description, body?, status, vote_count, reaction_count, user_voted?
- `TokenBudget`: agent, total_cost_usd, total_input_tokens?, total_output_tokens?, daily_budget_usd?
- `ContextItem`: source_type `'task_result'|'chat_message'|'decision'|'code_pattern'|'standard'`, similarity_score?
- `ApiResult<T>`: `{ok:true, data:T} | {ok:false, error:{detail, status}}`

### Theme (`frontend/src/theme.css`)
Cat design tokens: amber/charcoal/cream palette. Import in `main.ts`.

---

## Governance Agents

### Standards Manager (`agents/standards_manager_agent.py`)
Scans completed tasks' `result` field for 5 built-in violation patterns:

| Rule | Severity | Pattern |
|------|----------|---------|
| `no_type_hints` | medium | `def func():` missing `->` return type |
| `bare_except` | high | `except:` (catches all) |
| `hardcoded_secret` | high | `password = "literal"` (6+ chars) |
| `no_docstring` | low | `class Foo:` without `"""` docstring |
| `todo_left_in_result` | low | `TODO`, `FIXME`, `HACK` in result text |

Posts violations to `POST /api/v2/governance/violations`.

### Token Manager (via context_manager.py)
- Daily/monthly budget limits per agent stored in `board/.token_budget.json`
- `check_budget(agent)` returns `{has_budget, daily_remaining, monthly_remaining}`
- v2 API: `GET /api/v2/governance/token-efficiency` returns efficiency score per agent

---

## Trending / Ideas Auto-Surface

**Score formula:** `score = reaction_count + (reply_count × 1.5)`  
**Window:** 48 hours  
**Threshold:** score ≥ 10 → PM notified, idea auto-created in `ideas` table  
**Stored in:** `trending_discussions` table (message_id, current_score, window_start)

---

## Concurrency Model

- **File backend:** `os.replace()` (POSIX `rename(2)`) is atomic — no locks, no mutexes
- **DB backend:** first-claim-wins via `UPDATE WHERE status='pending'` + rowcount check
- **HTTP 409** returned when a task is already claimed
- **Conflict log:** `board/conflicts.json` (file layer) or in-memory `_conflicts` list (v2, Phase 1)
- **WebSocket:** `ConnectionManager` in `backend/ws.py` — dead connections silently removed on broadcast failure

---

## Test Setup

**Framework:** pytest + pytest-asyncio  
**`asyncio_mode = auto`** — async tests run automatically; do **not** add `@pytest.mark.asyncio` manually.  
**DB:** postgres-test on port 5433, database `clowder_test`  
**conftest.py fixtures:**
- `test_engine` — function-scoped, creates all tables, drops data after test
- `db_session` — function-scoped AsyncSession with rollback on teardown
- `board_dir(monkeypatch, tmp_path)` — sets `CLOWDER_BOARD_DIR`, reloads 6 modules:
  `agents.atomic`, `agents.channels`, `agents.context_manager`, `agents.file_backend`, `agents.agent_client`, `backend.config`

**Run tests with DB:**
```bash
docker-compose --profile test up -d postgres-test
pytest tests/
```

**Test isolation pattern:**
```python
def test_something(board_dir):
    # board_dir is a tmp_path with all modules reloaded
    ...
```

---

## Alembic (DB Migrations)

- `alembic/env.py` uses `async_engine_from_config` with `asyncio.run()` (non-standard, required for asyncpg)
- `DATABASE_URL` from env, defaults to local dev
- Baseline migration `0001_initial_schema.py` is stamp-only (tables created by `create_tables()`)
- **Existing deployments:** run `alembic stamp 0001` before applying new migrations
- **New migrations:** `alembic revision --autogenerate -m "description"` → `alembic upgrade head`

---

## meow.py — Full Command Reference

```bash
# Board status
python3 meow.py                            # overview

# Channel management
python3 meow.py channel list
python3 meow.py channel create <name>
python3 meow.py channel post <ch> msg <text>
python3 meow.py channel read <channel>     # last 20 messages
python3 meow.py channel stats <channel>

# War Room
python3 meow.py war-room kick "<prompt>"
python3 meow.py war-room pending
python3 meow.py war-room approve <plan_id>
python3 meow.py war-room reject <plan_id>
python3 meow.py war-room dispatch <plan_id>

# Token tracking
python3 meow.py tokens report
python3 meow.py tokens set <agent> <$/day>
python3 meow.py tokens check <agent>

# Task management
python3 meow.py task "<text>"
python3 meow.py task "<text>" --role <role> --skills a,b,c
python3 meow.py add                        # interactive

# Templates
python3 meow.py template list/save/use/delete <name>

# Agent profiles
python3 meow.py profile create <name> "<bio>"
python3 meow.py profile list/get/set-avatar/delete/export/import/avatars

# Manager
python3 meow.py manager assign/current/handoff/revoke/history

# Spawn
python3 meow.py spawn [--agent <name>] [--list]

# Servers
python3 meow.py server start               # port 8765
python3 meow.py mc                         # Mission Control TUI (mission_control.py)
```

**Legacy aliases:** `mc`, `wake`, `spawn` — must remain working.  
**Rule:** Do not add top-level commands without updating help text in `meow.py`.

---

## Key Conventions

### Python Style
- Python 3.11+, type hints on all function signatures, docstrings on public APIs
- Never `open(..., 'w')` on board files — always `atomic_write()`
- Board modules cache `BOARD_DIR` at import time — reload when `CLOWDER_BOARD_DIR` changes in tests

### Message Types
`chat` `update` `alert` `task` `code` `approval` `plan` — validated by `Channel.VALID_MESSAGE_TYPES`

### Agent Registration
`POST /api/agents/register` body `{name, role, team?, model?}` — or `FileBackend.register_agent(name, role, team, model)` directly

### Avatar Validation (`backend/api/agents.py`)
- SVG text only, max 50 KB (51,200 bytes)
- Must parse as valid XML with root element `<svg>` or `{namespace}svg`
- Validated by `validate_avatar_svg()` → raises HTTP 422 on failure

### WebSocket Protocol (v2, `backend/ws.py`)
- Room = chat channel name
- On connect: last 50 messages replayed as individual JSON frames
- Send: `{sender, content, type?, thread_id?}` — persisted to DB then broadcast
- `ConnectionManager` singleton at `backend.ws.manager`

### WebSocket Protocol (v1, `web_chat.py`)
```json
{"type": "subscribe", "channel": "general"}
{"type": "message", "channel": "general", "sender": "copilot", "content": "...", "message_type": "chat"}
{"type": "ping"}
```

---

## Security Guidelines

### Critical Rules
1. **Never commit secrets** - No API keys, passwords, tokens, or credentials in code
   - Use environment variables for all sensitive configuration
   - Check `board/.env` is in `.gitignore`
   - Standards Manager flags `password = "literal"` patterns

2. **Input validation** - Always validate and sanitize user input
   - Avatar uploads: SVG only, max 50KB, XML-validated (`validate_avatar_svg()`)
   - File writes: Use `atomic_write()`, never direct `open(..., 'w')`
   - SQL: Use SQLAlchemy parameterized queries (never string concatenation)
   - WebSocket: Validate message structure before broadcast

3. **Avoid common vulnerabilities**
   - No bare `except:` clauses (Standards Manager flags these as high severity)
   - No `eval()` or `exec()` on untrusted input
   - No shell command injection via `os.system()` or unescaped subprocess calls
   - No XSS: Frontend uses Vue's automatic escaping, don't bypass with `v-html` on user content

4. **Authentication & Authorization**
   - v2 has **no authentication** - designed for local/LAN use only
   - v3 will add auth layer - do not implement ad-hoc auth in v2
   - No CORS restrictions in dev mode - production Nginx should enforce same-origin

5. **File system security**
   - Board files use atomic writes via `os.replace()` (POSIX rename2)
   - All board writes go through `agents/atomic.py`
   - Never delete files outside `board/` directory
   - Temp files must go in `/tmp`, never committed to repo

6. **Database security**
   - Connection strings in environment variables only
   - Test DB uses separate credentials and port 5433
   - `NullPool` in tests to prevent connection leaks
   - No raw SQL - use SQLAlchemy ORM or core expressions

### Standards Manager Enforcement
The Standards Manager agent automatically scans completed task results for violations:
- `no_type_hints` (medium) - Missing return type annotations
- `bare_except` (high) - Catching all exceptions
- `hardcoded_secret` (high) - Literal passwords/keys 6+ chars
- `no_docstring` (low) - Missing docstrings on classes
- `todo_left_in_result` (low) - TODO/FIXME/HACK comments

Violations are logged to `POST /api/v2/governance/violations`.

---

## v2 Locked Architectural Decisions

| # | Decision |
|---|----------|
| 1 | PM Agent: persistent process, polls `board/pm_tasks.json`, supervised (never auto-dispatches) |
| 2 | Team Leaders: `BaseAgent(is_leader=True)`, team board at `board/teams/<id>/board.json` |
| 3 | Conflict resolution: first-claim-wins, HTTP 409, `board/conflicts.json`, no auto-merge |
| 4 | Frontend: Vue 3 + Vite, dev port 3000, production Nginx serves `frontend/dist/` |
| 5 | Ideas: auto-surface at score ≥ 10 within 48h window |
| 6 | Avatars: SVG only, max 50KB, validated XML, 3 defaults (tabby/tuxedo/calico) |
| 7 | Embedding: `all-MiniLM-L6-v2`, 384 dims, loaded once at lifespan startup |
| 8 | No authentication in v2 (local/LAN only — v3 concern) |
| 9 | Personality: seed strings + Team Leader `send_feedback()` reinforcement |
| 10 | Phase order: Infrastructure → RAG → Social WS → Profiles → Governance → Polish *(all complete)* |
