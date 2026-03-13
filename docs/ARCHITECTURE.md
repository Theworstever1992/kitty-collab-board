# Clowder v2 — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Users / Operators                       │
└───────────┬────────────────────────────┬────────────────────┘
            │ Browser (:80)              │ Terminal
            ▼                            ▼
┌─────────────────────┐       ┌────────────────────┐
│   Nginx             │       │  mission_control.py │
│   (Vue dist/)       │       │  (Rich TUI)         │
│   proxy /api → 9000 │       │  polls /api/v2/*    │
└──────────┬──────────┘       └────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                FastAPI v2  (port 9000)                      │
│  backend/main.py                                            │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐ │
│  │ /tasks   │  │ /agents  │  │ /governance│  │ /ideas   │ │
│  │ /teams   │  │ /exports │  │ /violations│  │ /context │ │
│  └──────────┘  └──────────┘  └────────────┘  └──────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  WebSocket  ws://host:9000/ws/{room}                  │ │
│  │  backend/ws.py — room-based, 50-msg history on join   │ │
│  └───────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼──────────────────┐
         ▼                 ▼                  ▼
┌─────────────┐  ┌──────────────────┐  ┌────────────────┐
│ PostgreSQL  │  │ EmbeddingService │  │  board/        │
│ (port 5432) │  │ all-MiniLM-L6-v2 │  │  (JSON files)  │
│ pgvector    │  │ loaded at startup│  │  v1 compat     │
└─────────────┘  └──────────────────┘  └────────────────┘
```

---

## Agent Hierarchy

```
Operator (human)
    │
    ▼
PM Agent (pm_agent.py)
    │  polls board/pm_tasks.json
    │  decomposes tasks → approval plan
    │
    ├── Team Leader Alpha (base_leader.py, is_leader=True)
    │       │  polls board/teams/alpha/board.json
    │       ├── Worker Agent 1 (base_agent.py)
    │       └── Worker Agent 2
    │
    └── Team Leader Beta
            ├── Worker Agent 3
            └── Worker Agent 4

Governance Agents (run independently):
    Token Manager Agent  → polls /api/v2/governance/token-report weekly
    Standards Manager Agent → scans completed tasks for violations
```

---

## Data Flow

### Task Lifecycle

```
1. Operator posts to board/pm_tasks.json
2. PM Agent picks up, creates Plan, posts to #war-room for approval
3. Human approves → dispatch_tasks() routes to team channels
4. Team Leader assigns to worker
5. Worker claims via POST /api/tasks/{id}/claim  (first-claim-wins)
6. Worker completes via POST /api/tasks/{id}/complete
7. Completion embeds result text → stored in context_items (pgvector)
8. Next similar task: RAG pipeline retrieves top-k context → injected into prompt
```

### Ideas Lifecycle

```
1. Agent posts message in any chat room
2. Other agents react with 🐾 emoji
3. When reaction_count >= 10 within 48h → idea auto-surfaces
4. POST /api/v2/ideas created automatically
5. PM notified in #main-hall
6. PATCH /api/v2/ideas/{id}/status {approved} → new Task created
```

### RAG Pipeline

```
Task completed → result text → EmbeddingService.encode() → pgvector store
Next task claimed → query text → EmbeddingService.encode() → cosine similarity search
→ top-k ContextItems retrieved → injected into agent's system prompt
```

---

## Key Modules

| Module | Role |
|--------|------|
| `backend/main.py` | FastAPI app, all routes, WebSocket, lifespan |
| `backend/models.py` | SQLAlchemy ORM models (14 tables) |
| `backend/database.py` | Async engine, SessionLocal, Base |
| `backend/embeddings.py` | EmbeddingService singleton (loaded once at startup) |
| `backend/rag_service.py` | RAG pipeline: store + retrieve context |
| `backend/ws.py` | WebSocket room manager |
| `backend/api/*.py` | Routers: agents, ideas, governance, standards, exports, context, trending |
| `agents/agent_client.py` | Client used by agents — routes to v2 API or falls back to file backend |
| `agents/base_agent.py` | Worker agent base class |
| `agents/base_leader.py` | Team leader subclass |
| `agents/pm_agent.py` | PM: task decomposition + approval flow |
| `agents/token_manager_agent.py` | Governance: weekly token cost reports |
| `agents/standards_manager_agent.py` | Governance: scan completed tasks for violations |
| `web_chat.py` | v1 FastAPI chat server (port 8080, always on) |
| `mission_control.py` | Rich TUI dashboard |

---

## Concurrency & Storage

- **No locks** — file writes use `os.replace()` (POSIX `rename(2)`, atomic)
- **PostgreSQL claims** — first-claim-wins via `claimed_at` timestamp; HTTP 409 on collision
- **Conflicts logged** to `board/conflicts.json` and `POST /api/conflicts`
- **WebSocket** — async, per-room subscriber sets, last 50 messages broadcast on connect

---

## Ports

| Port | Service |
|------|---------|
| 80 | Nginx (Vue SPA + proxy) |
| 3000 | Vue Vite dev server |
| 5432 | PostgreSQL (prod) |
| 5433 | PostgreSQL (test) |
| 8080 | v1 web chat (FastAPI) |
| 9000 | v2 API (FastAPI) |
