# Clowder — Comprehensive Overview, Vulnerability Audit & Secure Recreation Plan

> **Purpose:** This is the single source of truth for rebuilding Clowder from scratch with
> security baked in from day one. It contains the full current-state inventory, a complete
> security audit, coding guidelines, the proposed new architecture, and a sprint-by-sprint
> gameplay guide — from wiping the repo to production-ready in 8 sprints.
>
> Generated: 2026-04-07  |  Last updated: 2026-04-07

---

## Table of Contents

1. [Current Repository Overview](#1-current-repository-overview)
2. [Full Directory Layout (Annotated)](#2-full-directory-layout-annotated)
3. [Component Inventory](#3-component-inventory)
4. [Security Vulnerabilities — Full Audit](#4-security-vulnerabilities--full-audit)
5. [Coding Guidelines for the New Build](#5-coding-guidelines-for-the-new-build)
6. [New Secure Architecture Design](#6-new-secure-architecture-design)
7. [Proposed New Directory Structure](#7-proposed-new-directory-structure)
8. [Detailed Recreation Checklist (by phase)](#8-detailed-recreation-checklist)
9. [Technology Stack Decisions](#9-technology-stack-decisions)
10. [Environment & Secrets Strategy](#10-environment--secrets-strategy)
11. [🎮 Sprint-by-Sprint Gameplay Guide](#11-️-sprint-by-sprint-gameplay-guide)

---

## 1. Current Repository Overview

**What this project is:** Clowder is a dual-mode multi-agent coordination platform that lets
human operators and AI agents (Claude, Qwen, Copilot, Gemini, etc.) coordinate on tasks,
ideas, and governance through a shared board.

### Dual-Mode Architecture

| Mode | Layer | Port | Always On? |
|------|-------|------|-----------|
| **v1** | File-based JSON board (`board/`) | 8080 | Yes |
| **v2** | PostgreSQL + pgvector + FastAPI | 9000 | With `--profile v2` |

The `AgentClient` in `agents/agent_client.py` probes `GET /api/health` every 30 seconds and
silently routes to the PostgreSQL backend when available, or falls back to the file backend.

### Runtime Ports

| Port | Service |
|------|---------|
| 80   | Nginx → Vue SPA (production) |
| 3000 | Vue 3 Vite dev server |
| 5432 | PostgreSQL (production) |
| 5433 | PostgreSQL (test) |
| 8080 | v1 FastAPI web-chat server |
| 8765 | Raw WebSocket server (server.py, optional) |
| 9000 | v2 FastAPI REST + WebSocket API |

---

## 2. Full Directory Layout (Annotated)

```
kitty-collab-board/
│
├── .env.example              # Template for environment variables (credentials visible)
├── .gitignore
├── .dockerignore
├── Dockerfile                # Single image for all Python services
├── docker-compose.yml        # Multi-profile: default, v2, test, init, shell
├── start.sh                  # Dev startup helper
├── wake_up_all.py            # First-time board initialiser (creates channels etc.)
├── meow.py                   # CLI entry point (channel, task, war-room, token, profile cmds)
├── mission_control.py        # Rich TUI dashboard
├── server.py                 # Raw WebSocket + Watchdog server (port 8765)
├── web_chat.py               # v1 FastAPI chat server (port 8080)
├── ui.html                   # Single-file v1 Web UI (served from web_chat.py)
├── agents.yaml               # Agent definitions (name, role, model)
├── requirements.txt          # Python dependencies
├── pytest.ini                # asyncio_mode = auto
├── alembic.ini               # Alembic migration config
│
├── agents/                   # Python agent layer (v1 logic + client)
│   ├── __init__.py
│   ├── atomic.py             # atomic_write / atomic_read via os.replace()
│   ├── backend_protocol.py   # Protocol/interface definition for backends
│   ├── agent_client.py       # Routes to v2 API or FileBackend
│   ├── base_agent.py         # BaseAgent — all agents inherit this
│   ├── base_leader.py        # Team leader subclass of BaseAgent
│   ├── channels.py           # Channel class — read/write board/channels/<name>/
│   ├── context_manager.py    # Token usage tracking + budget enforcement
│   ├── file_backend.py       # FileBackend — pure delegation to v1 modules
│   ├── manager.py            # Manager registry (assign/revoke/handoff)
│   ├── onboarding.py         # Agent onboarding flow
│   ├── pm_agent.py           # PM agent — decomposes tasks, supervised mode
│   ├── profiles.py           # Agent profile helpers
│   ├── standards_manager_agent.py  # Scans task results for violations
│   ├── token_manager_agent.py      # Weekly token cost reports
│   └── war_room.py           # 5-step War Room approval workflow
│
├── backend/                  # v2 FastAPI backend (PostgreSQL + pgvector)
│   ├── __init__.py
│   ├── main.py               # FastAPI app, routes, WebSocket, lifespan
│   ├── config.py             # Settings from environment variables
│   ├── database.py           # Async SQLAlchemy engine + SessionLocal
│   ├── models.py             # 14 SQLAlchemy ORM models
│   ├── embeddings.py         # EmbeddingService singleton (sentence-transformers)
│   ├── rag_service.py        # RAG pipeline (store + query context_items)
│   ├── postgres_backend.py   # PostgresBackend (REST client mirror of FileBackend)
│   ├── ws.py                 # WebSocket ConnectionManager
│   └── api/
│       ├── __init__.py
│       ├── agents.py         # /api/v2/agents — profiles, avatar validation
│       ├── context.py        # /api/v2/context — seed/search context items
│       ├── exports.py        # /api/v2/agents/{name}/export
│       ├── governance.py     # /api/v2/governance — token report + efficiency
│       ├── ideas.py          # /api/v2/ideas — CRUD + voting
│       ├── standards.py      # /api/v2/governance/violations
│       └── trending.py       # /api/v2/trending
│
├── frontend/                 # Vue 3 + TypeScript + Vite SPA
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── router.ts         # Vue Router routes
│       ├── theme.css
│       ├── style.css
│       ├── api/
│       │   └── client.ts     # Fetch-based API client returning ApiResult<T>
│       ├── hooks/
│       │   └── useWebSocket.ts   # Auto-reconnect WS hook
│       ├── types/
│       │   └── index.ts      # TypeScript interfaces
│       ├── utils/
│       │   └── errors.ts
│       ├── components/       # Reusable components (14 components)
│       └── pages/            # Route pages (11 pages)
│
├── alembic/                  # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_initial_schema.py
│       ├── 46cbdc...add_task_status_team_index.py
│       └── 62f954...add_leadermeeting_created_at_index.py
│
├── nginx/
│   └── default.conf          # Nginx: SPA serving + /api + /ws proxy
│
├── tests/                    # pytest tests (30 test files)
│   ├── conftest.py           # Fixtures: test_engine, db_session, board_dir
│   └── test_*.py             # Unit + integration tests
│
├── docs/                     # Project documentation
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── DATA_MODEL.md
│   ├── DEPLOYMENT.md
│   ├── FRONTEND_API_MAP.md
│   ├── FRONTEND_RAG_UX.md
│   └── WS_CONTRACTS.md
│
└── scripts/
    └── smoke_test.sh
```

---

## 3. Component Inventory

### Database Schema (14 Tables)

| Table | Purpose |
|-------|---------|
| `tasks` | Task tracking with status, claims, priority, skills |
| `agents` | Agent registry: name, role, model, bio, avatar, skills |
| `chat_messages` | Per-channel messages + pgvector embedding |
| `token_usage` | Per-agent token cost log |
| `teams` | Team definitions with leader |
| `task_history` | Audit log of task status changes |
| `task_embeddings` | Vector embeddings of completed task results |
| `context_items` | RAG knowledge store (task results, messages, decisions) |
| `message_reactions` | Emoji reactions on messages |
| `trending_discussions` | Auto-surface score per message within 48h window |
| `ideas` | Surfaced ideas with status + approval |
| `idea_votes` | Per-voter vote records |
| `standards_violations` | Code quality violation log |
| `agent_exports` | Serialised agent profile exports |
| `retrieval_logs` | RAG query audit trail |
| `leader_meetings` | Agenda/decisions for team leader meetings |

### API Surface (v2)

| Group | Endpoints |
|-------|-----------|
| Health | `GET /api/health` |
| Tasks | `GET/POST /api/tasks`, `POST /api/tasks/{id}/claim`, `POST /api/tasks/{id}/complete` |
| Messages | `GET/POST /api/channels/{ch}/messages`, `GET/POST /api/v2/chat/{room}` |
| Agents | `POST /api/agents/register`, `GET/PATCH /api/v2/agents`, heartbeat |
| Tokens | `POST /api/tokens/log`, `GET /api/tokens/{agent}/budget` |
| RAG | `POST /api/rag/search`, `POST /api/v2/rag/search` |
| Conflicts | `POST/GET /api/conflicts` |
| Teams | `GET/POST /api/v2/teams`, `GET /api/v2/teams/{id}` |
| Chat | `GET/POST /api/v2/chat/{room}` |
| Governance | `GET /api/v2/governance/token-report`, violations, efficiency |
| Ideas | `GET/POST /api/v2/ideas`, vote, status patch |
| Context | `POST /api/v2/context/seed/*`, `GET /api/v2/context/search` |
| WebSocket | `WS /ws/{room}` |

---

## 4. Security Vulnerabilities — Full Audit

> **Severity scale:** 🔴 Critical · 🟠 High · 🟡 Medium · 🔵 Low

---

### 4.1 Authentication & Authorization

| # | Severity | File | Issue |
|---|----------|------|-------|
| A1 | 🔴 Critical | `backend/main.py`, `web_chat.py` | **No authentication on any endpoint.** Any actor on the network can register as any agent, claim any task, post any message, log any token usage, or modify any agent profile. |
| A2 | 🔴 Critical | `backend/main.py` line 206-247 | **Task claim impersonation.** `agent_name` in `ClaimRequest` is user-supplied and trusted. An attacker claims tasks as any agent. |
| A3 | 🔴 Critical | `backend/main.py` line 250-282 | **Task completion impersonation.** `agent_name` in `CompleteRequest` is user-supplied. An attacker can mark any in-progress task as done with arbitrary results. |
| A4 | 🔴 Critical | `web_chat.py` line 217-241 | **Agent registration is unauthenticated and unrestricted.** Anyone can register any name, role, or team. |
| A5 | 🟠 High | `backend/api/agents.py` line 110-135 | **Profile update with no ownership check.** `PATCH /api/v2/agents/{name}/profile` accepts updates for any agent without verifying the caller owns that agent. |
| A6 | 🟠 High | `backend/api/governance.py` | **Governance endpoints unauthenticated.** Any client can read token reports, efficiency scores, and violation logs — these contain operational intelligence. |
| A7 | 🟠 High | `backend/api/ideas.py` | **Idea approval unauthenticated.** Any client can approve or reject ideas. |

---

### 4.2 CORS Configuration

| # | Severity | File | Issue |
|---|----------|------|-------|
| B1 | 🔴 Critical | `backend/main.py` line 58-63 | **`allow_origins=["*"]`** — wildcard origin allows any web page to make cross-origin requests to the API. In a LAN/intranet deployment this exposes all data to malicious sites loaded in the operator's browser. |
| B2 | 🔴 Critical | `web_chat.py` line 32-39 | Same wildcard CORS **plus `allow_credentials=True`**. This combination is forbidden by the CORS spec and exploitable for credential theft. |

---

### 4.3 Secrets & Credentials

| # | Severity | File | Issue |
|---|----------|------|-------|
| C1 | 🟠 High | `docker-compose.yml` lines 12-14, 30-33 | **Hardcoded weak credentials** `clowder:clowder` for both production and test databases. These are committed to the repository. |
| C2 | 🟠 High | `docker-compose.yml` line 58 | `DATABASE_URL` with plaintext password embedded in docker-compose. Anyone with repo access has the DB password. |
| C3 | 🟠 High | `docker-compose.yml` line 61 | `CLOWDER_DEBUG=true` in production `api` service. Debug mode exposes stack traces, internal variables, and FastAPI's interactive docs. |
| C4 | 🟡 Medium | `.env.example` | The example file contains real-looking credentials (`clowder:clowder`). New developers often copy `.env.example` as-is, creating insecure deployments. |
| C5 | 🔵 Low | `firebase-debug.log` | Firebase debug log committed to the repository. May contain API keys, project IDs, or internal error details. Should be gitignored. |

---

### 4.4 Input Validation & Injection

| # | Severity | File | Issue |
|---|----------|------|-------|
| D1 | 🟠 High | `backend/main.py` line 77-119 | **WebSocket accepts arbitrary JSON with no validation.** `sender`, `content`, and `type` fields are accepted and stored without length limits or type validation. A malicious client can store multi-megabyte payloads. |
| D2 | 🟠 High | `backend/main.py` line 108 | **`sender` field user-controlled** in WebSocket messages. Any connection can impersonate any agent or user. |
| D3 | 🟡 Medium | `backend/api/agents.py` lines 38-51 | **SVG parsed with `xml.etree.ElementTree`** without `defusedxml`. While Python's ET does not load external entities by default in Python 3.8+, the standard library does not guarantee protection against all XML attacks (billion laughs, quadratic blowup). |
| D4 | 🟡 Medium | `backend/main.py`, `backend/api/*.py` | **No request body size limits.** Large payloads (e.g. huge `content` or `result` fields) can exhaust memory. FastAPI does not impose body size limits by default. |
| D5 | 🟡 Medium | `backend/main.py` line 412 | **`_conflicts` list is in-memory and unbounded.** Flooding `POST /api/conflicts` will exhaust process memory and is not persisted across restarts. |
| D6 | 🔵 Low | `web_chat.py` line 218 | Query parameters (`name`, `role`, `team`) used directly without sanitisation. Non-critical since no DB is involved but sets a bad precedent. |

---

### 4.5 Rate Limiting & Denial of Service

| # | Severity | File | Issue |
|---|----------|------|-------|
| E1 | 🟠 High | All endpoints | **No rate limiting on any endpoint.** `POST /api/tokens/log` can be spammed to inflate cost records. `POST /api/channels/{ch}/messages` can flood the database. |
| E2 | 🟠 High | `backend/main.py` line 376-389 | **Token logging unauthenticated and unthrottled.** Any client can fabricate token usage records for any agent, distorting governance reports. |
| E3 | 🟡 Medium | `backend/main.py` line 90-96 | **WebSocket history replay** fetches up to 50 rows per connection. With no connection limit or auth, an attacker can open thousands of connections and hammer the DB. |

---

### 4.6 Security Headers

| # | Severity | File | Issue |
|---|----------|------|-------|
| F1 | 🟡 Medium | `nginx/default.conf` | **No security headers.** Missing: `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security`. |
| F2 | 🟡 Medium | `nginx/default.conf` | **HTTP only — no TLS.** The server listens on plain port 80 with no HTTPS redirect. All data including any future auth tokens would be transmitted in cleartext. |
| F3 | 🔵 Low | `backend/main.py` line 51-56 | **FastAPI `debug=DEBUG`** passes the debug flag directly into the app. When `CLOWDER_DEBUG=true`, detailed internal error information is sent to clients. |

---

### 4.7 Data Integrity

| # | Severity | File | Issue |
|---|----------|------|-------|
| G1 | 🟡 Medium | `backend/main.py` line 222-245 | **RAG context appended to task description in-place.** When a task is claimed, AI-generated context text is appended to the operator-written task description and committed to the DB. This silently alters official task records. |
| G2 | 🟡 Medium | `backend/models.py` | **No field-level length constraints in ORM models.** `content` (Text), `result` (Text), `description` (Text) accept unlimited text. The 50KB check exists only for SVG avatars. |
| G3 | 🔵 Low | `backend/main.py` line 126-128 | **Task IDs are client-supplied** (via `claim` — the `task_id` is a path param from URL). Task IDs should be server-generated UUIDs to prevent enumeration and collision attacks. |

---

### 4.8 Dependency Security

| # | Severity | File | Issue |
|---|----------|------|-------|
| H1 | 🟡 Medium | `requirements.txt` | **No pinned dependency versions** (only `>=` lower bounds). A `pip install` will fetch the latest compatible versions, which may include newly published vulnerable releases. |
| H2 | 🟡 Medium | `requirements.txt` | **`sentence-transformers`** is a large ML dependency. It transitively pulls `torch`, `transformers`, and dozens of other packages. No lockfile (`requirements.lock`) ensures reproducible builds. |
| H3 | 🔵 Low | `requirements.txt` | **`pytest-cov>=4.1.0` appears twice** (lines 27 and 29). Suggests the file was modified without review. |

---

### 4.9 Infrastructure

| # | Severity | File | Issue |
|---|----------|------|-------|
| I1 | 🟠 High | `docker-compose.yml` line 55 | **`./:/app:ro` mounts the entire project root** into every container. This includes `.env`, `.git/`, and any local secrets. A compromised container can read them all. |
| I2 | 🟡 Medium | `docker-compose.yml` line 5432 | **PostgreSQL port 5432 exposed to host** without binding to `127.0.0.1`. On a machine with multiple network interfaces the database is reachable from the network. |
| I3 | 🔵 Low | `Dockerfile` | No non-root user defined. All processes run as root inside the container. |

---

## 5. Coding Guidelines for the New Build

### 5.1 Python

```
- Python 3.12+ minimum.
- Type hints required on ALL function signatures (parameters + return type).
- Docstrings required on every public class and function.
- No bare `except:` — always catch specific exceptions.
- All board/file writes via atomic_write() — never open(..., 'w') on shared files.
- No hardcoded secrets — read everything from environment variables via pydantic-settings.
- Use defusedxml for any XML parsing (SVG, etc.).
- Max line length: 100 characters.
- Imports: stdlib → third-party → local, each group separated by a blank line.
- Prefer explicit keyword arguments when calling functions with 3+ parameters.
- All Pydantic models must define field validators for untrusted user input.
- Every endpoint must enforce:
    (a) authentication (JWT or API key)
    (b) input size limits
    (c) rate limiting
```

### 5.2 TypeScript / Vue 3

```
- Strict TypeScript (`"strict": true` in tsconfig).
- No `any` type — use proper interfaces or `unknown` with type guards.
- All API calls must use the typed `ApiResult<T>` wrapper — never raw fetch without error handling.
- Composables (hooks) for shared stateful logic — no business logic in templates.
- Components: <100 lines recommended, <200 lines maximum.
- Props: always typed with defineProps<T>().
- Emits: always typed with defineEmits<T>().
- Never use `v-html` with user-generated content (XSS risk).
- All user-supplied text rendered via text nodes, never innerHTML.
```

### 5.3 Testing

```
- Every new endpoint requires at minimum one happy-path and one error-path test.
- asyncio_mode = auto — do NOT add @pytest.mark.asyncio.
- DB tests must use the db_session fixture to guarantee table creation.
- File-backend tests must use the board_dir fixture (monkeypatched tmp_path).
- Test coverage target: 80% per module.
- Security tests: at minimum one test per vulnerability class fixed.
- No test should rely on external network calls (mock httpx/aiohttp).
```

### 5.4 Git & CI

```
- Never commit: .env, *.log, board/, node_modules/, __pycache__/, *.pyc, frontend/dist/
- Secrets scanning in CI: gitleaks or detect-secrets on every push.
- Dependency vulnerability scanning: pip-audit (Python), npm audit (Node) in CI.
- All PRs require passing tests and lint (ruff for Python, eslint for TypeScript).
- Branch protection: no direct push to main.
- Signed commits recommended.
```

### 5.5 Docker

```
- All services run as a non-root user (USER 1001).
- Never mount the full project root into a container.
- Mount only the specific directories each service needs.
- PostgreSQL must bind to 127.0.0.1 (or internal Docker network only) in production.
- Use Docker secrets or an external vault for database credentials.
- No CLOWDER_DEBUG=true in production environments.
- Use multi-stage Dockerfile: builder stage (installs deps) → runtime stage (no dev tools).
```

---

## 6. New Secure Architecture Design

### 6.1 Authentication Layer

The new build introduces a lightweight token-based auth layer designed for a
LAN/intranet deployment (no user accounts needed — agents authenticate with API keys):

```
┌─────────────────────────────────────────────────────┐
│                Auth Middleware                      │
│                                                     │
│  Every request must carry one of:                   │
│  - X-API-Key: <agent-api-key>   (agent requests)   │
│  - X-Operator-Key: <admin-key>  (human operator)   │
│                                                     │
│  Keys are:                                          │
│  - Generated at startup / agent registration        │
│  - Stored hashed in the database                   │
│  - Never logged or included in responses            │
└─────────────────────────────────────────────────────┘
```

### 6.2 Secure CORS Policy

```python
# Allow only explicitly listed origins — no wildcard
ALLOWED_ORIGINS = [
    "http://localhost:3000",   # Vue dev
    "http://localhost:80",     # Production Nginx
    os.environ["ALLOWED_ORIGIN"],  # Production domain (required env var)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,   # No credentials unless HTTPS is enforced
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)
```

### 6.3 Request Validation Middleware

```python
# Applied globally via FastAPI middleware
MAX_BODY_SIZE = 512 * 1024     # 512 KB hard limit on all request bodies
MAX_MESSAGE_LENGTH = 10_000    # characters
MAX_TASK_RESULT_LENGTH = 50_000
MAX_BIO_LENGTH = 2_000
```

### 6.4 Rate Limiting

```
- slowapi (FastAPI-compatible limiter backed by Redis or in-memory)
- Default: 60 requests/minute per IP
- Token logging: 10/minute per agent (prevents fabrication)
- Message posting: 30/minute per sender
- Agent registration: 5/hour per IP
- WebSocket connections: 10 concurrent per IP
```

### 6.5 Nginx Security Headers

```nginx
# Add to all responses
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws://localhost:9000;" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# HTTPS redirect (when TLS cert is available)
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

### 6.6 Separation of Concerns — Mutable vs Read-Only Context

- RAG context is **never written back** to the operator-authored task description.
- Instead, context is returned as a separate field `context_items` in the claim response.
- The agent is responsible for incorporating context into its prompt — the DB record stays clean.

---

## 7. Proposed New Directory Structure

```
clowder-v3/                        ← rename from kitty-collab-board
│
├── .env.example                   ← No real credentials; all values are <PLACEHOLDER>
├── .gitignore                     ← Adds: *.log, .env, board/, frontend/dist/
├── .dockerignore
├── Dockerfile                     ← Multi-stage; non-root USER 1001
├── docker-compose.yml             ← Secrets via Docker secrets; no hardcoded passwords
├── pyproject.toml                 ← Replaces requirements.txt; uses pip-tools lockfile
├── requirements.lock              ← Pinned transitive deps for reproducible builds
├── alembic.ini
│
├── config/                        ← Centralised config (replaces scattered os.environ calls)
│   ├── __init__.py
│   ├── settings.py                ← pydantic-settings BaseSettings; validation on load
│   └── logging.py                 ← Structured JSON logging config
│
├── core/                          ← Shared primitives used by both v1 and v2
│   ├── __init__.py
│   ├── atomic.py                  ← atomic_write / atomic_read (unchanged logic, typed)
│   ├── auth.py                    ← API key hashing, validation, dependency injection
│   ├── errors.py                  ← Custom exception hierarchy
│   ├── rate_limit.py              ← Rate limiter wrappers (slowapi)
│   ├── sanitise.py                ← Input length/content validators
│   └── xml_safe.py                ← defusedxml-based SVG parser (replaces ET)
│
├── file_backend/                  ← v1 file-based backend (renamed from agents/)
│   ├── __init__.py
│   ├── channels.py
│   ├── context_manager.py
│   ├── file_backend.py
│   ├── manager.py
│   ├── war_room.py
│   └── profiles.py
│
├── agents/                        ← Agent business logic (renamed from agents/)
│   ├── __init__.py
│   ├── agent_client.py            ← Routes to v2 API or file backend
│   ├── base_agent.py
│   ├── base_leader.py
│   ├── pm_agent.py
│   ├── standards_manager_agent.py
│   └── token_manager_agent.py
│
├── api/                           ← v2 FastAPI backend (renamed from backend/)
│   ├── __init__.py
│   ├── app.py                     ← FastAPI app factory (replaces main.py)
│   ├── dependencies.py            ← Shared FastAPI dependencies (auth, db, rate limit)
│   ├── database.py
│   ├── models.py
│   ├── schemas.py                 ← Pydantic request/response schemas (separated from models)
│   ├── embeddings.py
│   ├── rag_service.py
│   ├── ws.py
│   └── routers/                   ← One file per domain (replaces api/)
│       ├── __init__.py
│       ├── agents.py
│       ├── chat.py
│       ├── context.py
│       ├── exports.py
│       ├── governance.py
│       ├── ideas.py
│       ├── standards.py
│       ├── tasks.py
│       ├── teams.py
│       ├── tokens.py
│       └── trending.py
│
├── frontend/                      ← Vue 3 + TypeScript (unchanged structure)
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts          ← Add X-API-Key header to all requests
│   │   │   └── auth.ts            ← API key storage (sessionStorage, not localStorage)
│   │   └── ...
│   └── ...
│
├── nginx/
│   ├── default.conf               ← Security headers + HTTPS redirect
│   └── ssl/                       ← TLS cert/key (gitignored)
│
├── scripts/
│   ├── generate_keys.py           ← Generates initial operator key + agent keys
│   ├── smoke_test.sh
│   └── db_seed.py                 ← Replaces wake_up_all.py
│
├── migrations/                    ← Renamed from alembic/versions/
│   └── ...
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_auth.py           ← NEW: API key validation tests
│   │   ├── test_sanitise.py       ← NEW: Input validation tests
│   │   ├── test_xml_safe.py       ← NEW: SVG validation tests
│   │   └── test_rate_limit.py     ← NEW: Rate limiting tests
│   ├── integration/
│   │   └── test_*.py
│   └── security/
│       ├── test_cors.py           ← NEW: CORS policy tests
│       ├── test_auth_endpoints.py ← NEW: 401/403 on unauthenticated requests
│       └── test_injection.py      ← NEW: Oversized payloads, malformed XML
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    ├── SECURITY.md                ← NEW: Security model, key management, threat model
    ├── CODING_GUIDELINES.md       ← NEW: Links to Section 5 of this doc
    ├── DEPLOYMENT.md
    └── RECREATION_PLAN.md         ← This document
```

---

## 8. Detailed Recreation Checklist

### Phase 0 — Preparation (before writing a line of code)

- [ ] Create fresh git repository with branch protection on `main`
- [ ] Add `.gitignore` that excludes: `.env`, `*.log`, `board/`, `frontend/dist/`, `__pycache__/`, `*.pyc`, `node_modules/`, `*.egg-info/`
- [ ] Configure gitleaks or detect-secrets as a pre-commit hook
- [ ] Set up CI pipeline (GitHub Actions) with: lint, type-check, test, pip-audit, npm audit
- [ ] Write `SECURITY.md` — threat model, key management, known limitations
- [ ] Create `config/settings.py` using pydantic-settings with required-field validation

### Phase 1 — Core Security Primitives

- [ ] **`core/auth.py`** — API key generation (secrets.token_hex(32)), PBKDF2/bcrypt hashing, FastAPI dependency
- [ ] **`core/rate_limit.py`** — slowapi integration; per-endpoint limits
- [ ] **`core/sanitise.py`** — length validators, content validators for all user-input fields
- [ ] **`core/xml_safe.py`** — defusedxml-based SVG parser replacing ET
- [ ] **`core/errors.py`** — structured error responses; no stack traces to clients
- [ ] Add `X-Request-ID` middleware for request tracing
- [ ] Add request body size limit middleware (512 KB hard cap)
- [ ] Write tests: `tests/unit/test_auth.py`, `tests/security/test_auth_endpoints.py`

### Phase 2 — Database & Schema

- [ ] Migrate to `pyproject.toml` + `requirements.lock` (pip-tools)
- [ ] **`api/models.py`** — add `CheckConstraint` for string field lengths on all Text columns
- [ ] Add `api_key_hash` column to `agents` table
- [ ] Create initial Alembic migration with all tables + constraints
- [ ] Add database connection pooling config with explicit pool size limits
- [ ] Change docker-compose to use Docker secrets (not environment variables) for DB password
- [ ] Bind postgres to `127.0.0.1:5432` in production compose
- [ ] Write tests: verify field length constraints

### Phase 3 — API Server (Secure Re-implementation)

- [ ] **`api/app.py`** — FastAPI app factory; CORS restricted to explicit origins from env
- [ ] **`api/dependencies.py`** — `require_agent_auth`, `require_operator_auth` FastAPI deps
- [ ] **`api/routers/agents.py`** — all endpoints require auth; profile update checks ownership
- [ ] **`api/routers/tasks.py`** — claim/complete require auth; server generates task IDs; RAG context returned separately (not merged into description)
- [ ] **`api/routers/chat.py`** — message posting requires auth; sender validated against API key identity
- [ ] **`api/routers/tokens.py`** — token logging requires agent auth; throttled to 10/min
- [ ] **`api/routers/governance.py`** — requires operator auth
- [ ] **`api/routers/ideas.py`** — voting/approval requires auth
- [ ] Replace in-memory `_conflicts` list with proper DB table
- [ ] Add `slowapi` rate limiting to all write endpoints
- [ ] Write tests: one happy-path + one auth-failure test per router

### Phase 4 — WebSocket Security

- [ ] **`api/ws.py`** — require API key in connection query param or first message frame
- [ ] Limit to 10 concurrent connections per IP
- [ ] Validate and limit message fields (sender verified against key identity, content ≤ 10,000 chars)
- [ ] Disconnect clients that fail validation instead of silently ignoring
- [ ] Write tests: `tests/integration/test_ws_auth.py`

### Phase 5 — v1 File Backend Hardening

- [ ] Remove `allow_credentials=True` from web_chat.py CORS; restrict origins
- [ ] Add `defusedxml` dependency; replace all ET usage
- [ ] Add input validation to `web_chat.py` message and agent endpoints
- [ ] `atomic.py` — verify BOARD_DIR is within the expected root (path traversal prevention)

### Phase 6 — Nginx & TLS

- [ ] **`nginx/default.conf`** — add all security headers (CSP, X-Frame-Options, etc.)
- [ ] Add HTTP → HTTPS redirect block
- [ ] Generate self-signed cert for local dev; document Let's Encrypt for production
- [ ] Tune `proxy_read_timeout` to reasonable value (300s, not 86400s)

### Phase 7 — Frontend Security

- [ ] **`frontend/src/api/client.ts`** — read API key from `sessionStorage`; add `X-API-Key` header to all requests
- [ ] **`frontend/src/api/auth.ts`** — key entry UI; store in sessionStorage (not localStorage)
- [ ] Audit all `v-html` usage; replace with text nodes or DOMPurify if HTML is required
- [ ] Add `Content-Security-Policy` meta tag as defence-in-depth
- [ ] Run `npm audit` and fix all high/critical vulnerabilities
- [ ] Write ESLint security plugin rules

### Phase 8 — CI/CD Pipeline

- [ ] **`.github/workflows/ci.yml`** — runs on every push/PR:
  - `ruff check` (Python lint)
  - `mypy --strict` (Python type check)
  - `pytest tests/` (Python tests)
  - `pip-audit` (Python dependency CVE scan)
  - `npm run build` (TypeScript type check + build)
  - `npm audit --audit-level=high` (Node dependency CVE scan)
  - `eslint` (TypeScript lint)
- [ ] **`.github/workflows/security.yml`** — weekly:
  - `gitleaks detect` (secret scanning)
  - `trivy image` (Docker image CVE scan)
- [ ] Add branch protection: require CI passing, require review

### Phase 9 — Documentation & Cleanup

- [ ] **`docs/SECURITY.md`** — threat model, key rotation instructions, limitations
- [ ] **`docs/CODING_GUIDELINES.md`** — Python + TypeScript + Docker guidelines
- [ ] **`docs/DEPLOYMENT.md`** — updated with TLS, Docker secrets, key generation steps
- [ ] Remove `firebase-debug.log` from repo history (`git filter-repo`)
- [ ] Rotate/invalidate any credentials that appeared in commit history
- [ ] Update `README.md` with security setup instructions
- [ ] Tag `v3.0.0-secure`

### Phase 10 — Final Verification

- [ ] Run full test suite: all tests pass
- [ ] Run `pip-audit`: no high/critical CVEs
- [ ] Run `npm audit`: no high/critical CVEs
- [ ] Run `gitleaks detect --source .`: no secrets found
- [ ] Test all API endpoints with missing/invalid API key → all return 401
- [ ] Test CORS with a disallowed origin → rejected
- [ ] Test oversized payload → 413 or 422 returned
- [ ] Test WebSocket without auth → connection refused
- [ ] Smoke test: agent registers, claims task, completes task, reads messages

---

## 9. Technology Stack Decisions

### Keep (proven, fits the use case)

| What | Why Keep |
|------|----------|
| Python 3.12 | Mature async support; all existing agent logic is Python |
| FastAPI | Excellent OpenAPI docs; async-native; Pydantic v2 integration |
| SQLAlchemy 2 async | Battle-tested; first-class asyncpg support |
| PostgreSQL + pgvector | Vector search without additional infra |
| Vue 3 + Vite + TypeScript | Fast build; Composition API is clean; strong type safety |
| Nginx | Reliable reverse proxy; easy header config |
| pytest + pytest-asyncio | Already integrated; `asyncio_mode=auto` works well |
| sentence-transformers | `all-MiniLM-L6-v2` is well-suited for 384-dim RAG |

### Replace / Add

| Old | New | Reason |
|-----|-----|--------|
| `xml.etree.ElementTree` | `defusedxml` | Protection against XML attacks |
| `requirements.txt` (loose) | `pyproject.toml` + `requirements.lock` | Reproducible builds |
| Scattered `os.environ.get()` | `pydantic-settings BaseSettings` | Type-safe, validated config |
| No auth | `X-API-Key` middleware | Minimum viable auth for LAN deployment |
| No rate limiting | `slowapi` | Prevents spam and token inflation |
| Hardcoded docker passwords | Docker secrets + `.env` (gitignored) | No credentials in repo |
| `allow_origins=["*"]` | Explicit origin list from env | Proper CORS |
| `ET.fromstring()` for SVG | `defusedxml.ElementTree.fromstring()` | XXE-safe parsing |

---

## 10. Environment & Secrets Strategy

### What Goes Where

| Variable | Where |
|----------|-------|
| `DATABASE_URL` | `.env` file (gitignored) or Docker secret |
| `POSTGRES_PASSWORD` | Docker secret (`/run/secrets/pg_password`) |
| `OPERATOR_API_KEY` | `.env` file (gitignored); generated by `scripts/generate_keys.py` |
| `ALLOWED_ORIGIN` | `.env` file |
| `CLOWDER_DEBUG` | `.env` file; must be `false` in production |
| `EMBEDDING_MODEL` | `.env` file (safe to commit if non-sensitive) |

### `.env.example` (safe template)

```dotenv
# Copy to .env and replace ALL <PLACEHOLDER> values before running.
# Never commit .env to version control.

DATABASE_URL=postgresql+asyncpg://<DB_USER>:<DB_PASSWORD>@localhost:5432/clowder
POSTGRES_USER=<DB_USER>
POSTGRES_PASSWORD=<DB_PASSWORD>

OPERATOR_API_KEY=<run: python scripts/generate_keys.py>
ALLOWED_ORIGIN=http://localhost:3000

CLOWDER_DEBUG=false
CLOWDER_BOARD_DIR=./board
CLOWDER_EMBEDDING_MODEL=all-MiniLM-L6-v2
CLOWDER_RAG_TOP_K=5
```

### Key Generation

```bash
# Generate operator key (run once on first deploy)
python scripts/generate_keys.py --type operator
# → prints: OPERATOR_API_KEY=clowder_op_<64-hex-chars>

# Generate agent key (run when registering a new agent)
python scripts/generate_keys.py --type agent --name my-agent
# → prints: AGENT_API_KEY=clowder_ag_<64-hex-chars>
```

Keys are 256-bit random hex strings with a type prefix for clarity.
Only the PBKDF2/bcrypt hash is stored in the database — the plaintext key is shown once.

---

## Summary

The current Clowder codebase has **~25 identified security issues** across authentication,
CORS, credentials management, input validation, rate limiting, and infrastructure. None of
these are architectural dead-ends — the core design (dual-mode file/postgres, FastAPI, Vue 3,
pgvector RAG) is sound and worth keeping.

The recreation plan above adds security in layers:
1. **Auth first** — every request is authenticated before any business logic runs
2. **Validate at the boundary** — all user input is size-limited and type-validated at entry
3. **Credentials out of code** — nothing sensitive in the repository, ever
4. **Defence in depth** — rate limiting, security headers, CORS restriction, and TLS

The existing tests provide a strong safety net. The new `tests/security/` directory will
give ongoing confidence that security regressions are caught automatically.

When you are ready to wipe and recreate, follow the sprint guide in Section 11 below — it
covers every step from the initial wipe through to production deployment.

---

## 11. 🎮 Sprint-by-Sprint Gameplay Guide

> **How to read this section:**
> Think of each sprint like a level in a game. Each level has:
> - A **Goal** — what you're building this sprint
> - **Day-by-day tasks** — exactly what to do each day
> - A **Security procedure** — specific security steps for this sprint
> - A **Definition of Done** — the checkpoint you must pass before moving on
>
> Sprint length: **1 week** each (5 working days). Total: ~8 weeks from wipe to production.
> Adjust sprint length to match your team's pace — the order must stay the same.

---

### 🗺️ Game Map (High-Level)

```
WIPE ──► Sprint 0 ──► Sprint 1 ──► Sprint 2 ──► Sprint 3
         Repo Setup   Security     Database     API Routers
                      Primitives   & Schema     (Secured)
                                                    │
         Sprint 7 ◄── Sprint 6 ◄── Sprint 5 ◄── Sprint 4
         Production   CI/CD &      Frontend     WebSocket &
         Readiness    Docker       Security     Real-time
```

---

### ⚠️ Pre-Game: The Wipe

> **Do this before Sprint 0 starts.**

This is a destructive operation. Back up anything you want to keep first.

```bash
# 1. Export any board data you want to preserve
python3 meow.py tokens report > /tmp/token-backup.json
cp -r board/ /tmp/clowder-board-backup/

# 2. Take note of your current database schema
# (the models.py and migration files are your reference — they stay)

# 3. Create a new empty repository
git init clowder-v3
cd clowder-v3
git checkout -b main

# 4. Copy over ONLY the reference files (not the broken code)
# - docs/RECREATION_PLAN.md   (this file — your bible)
# - docs/ARCHITECTURE.md      (system diagram)
# - docs/API_REFERENCE.md     (endpoint reference)
# - agents/agent_client.py    (agent routing logic — reuse after hardening)
# - backend/models.py         (ORM models — reuse after adding constraints)
# - frontend/src/types/index.ts  (TypeScript interfaces)
# - alembic/versions/          (migration history)
# - tests/conftest.py          (test fixtures)
# Everything else gets rewritten from scratch.

# 5. Set up git branch protection immediately
# In GitHub: Settings → Branches → Add protection rule:
#   Branch name: main
#   ✅ Require a pull request before merging
#   ✅ Require status checks to pass
#   ✅ Do not allow bypassing the above settings
```

---

### Sprint 0: Repo Foundation & Security Pre-commit Gates

**Duration:** 1 week  
**Goal:** Lay the bedrock — a clean repository that physically cannot accept bad commits.  
**Output:** Empty repo with hard guardrails. Zero code written yet. Zero vulnerabilities possible yet.

---

#### Day 1 — Repository Setup

```bash
# Inside the new clowder-v3/ directory

# ── Python toolchain ──────────────────────────────────────────────────────────
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip pip-tools

# Create pyproject.toml (replaces requirements.txt)
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "clowder"
version = "3.0.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "pgvector>=0.3.0",
    "alembic>=1.14.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "python-dotenv>=1.0.1",
    "defusedxml>=0.7.1",
    "slowapi>=0.1.9",
    "sentence-transformers>=3.0.0",
    "watchdog>=5.0.0",
    "pyyaml>=6.0.2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "httpx>=0.27.0",
    "respx>=0.21.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
    "pip-audit>=2.7.0",
]
EOF

# Generate pinned lockfile
pip-compile pyproject.toml --output-file requirements.lock --extra dev
pip install -r requirements.lock
```

#### Day 1 Todo Checklist

- [ ] Create new git repo and switch to `main` branch
- [ ] Create `.gitignore` (see template below)
- [ ] Create `pyproject.toml` with all pinned deps
- [ ] Run `pip-compile` to generate `requirements.lock`
- [ ] Commit: `chore: initial repo skeleton with locked dependencies`

```
# .gitignore template for Day 1
.env
*.log
board/
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
venv/
.venv/
env/
node_modules/
frontend/dist/
.pytest_cache/
.coverage
htmlcov/
.idea/
.vscode/
*.swp
nginx/ssl/
```

---

#### Day 2 — Pre-commit Security Hooks

```bash
pip install pre-commit detect-secrets
pre-commit install

cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: no-commit-to-branch
        args: ['--branch', 'main']
EOF

# Create initial secrets baseline (empty — no secrets yet)
detect-secrets scan > .secrets.baseline
```

#### Day 2 Todo Checklist

- [ ] Install `pre-commit` and `detect-secrets`
- [ ] Create `.pre-commit-config.yaml`
- [ ] Run `pre-commit run --all-files` — fix any issues
- [ ] Create `.secrets.baseline`
- [ ] Test: try to commit a fake password string — confirm it is blocked
- [ ] Commit: `chore: add pre-commit hooks (secret scanning, lint, format)`

---

#### Day 3 — GitHub Actions CI Skeleton

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["main"]

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.lock
      - run: ruff check .
      - run: ruff format --check .
      - run: mypy --strict src/ api/ core/ config/  # adjust to your package layout
      - run: pytest tests/ --cov --cov-fail-under=80
      - run: pip-audit --requirement requirements.lock

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
      - run: npm audit --audit-level=high
        working-directory: frontend
```

```yaml
# .github/workflows/security.yml
name: Security Scan
on:
  schedule:
    - cron: "0 8 * * 1"   # Every Monday at 08:00 UTC
  workflow_dispatch:

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2

  trivy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t clowder:scan .
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: "clowder:scan"
          severity: "HIGH,CRITICAL"
          exit-code: "1"
```

#### Day 3 Todo Checklist

- [ ] Create `.github/workflows/ci.yml`
- [ ] Create `.github/workflows/security.yml`
- [ ] Push branch and confirm CI runs (it will fail on missing code — that's expected)
- [ ] Enable branch protection on `main`: require CI to pass
- [ ] Commit: `ci: add GitHub Actions CI and weekly security scan`

---

#### Day 4 — Centralised Configuration

```python
# config/settings.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database — required; no default; will fail loudly at startup if missing
    database_url: str = Field(..., description="PostgreSQL async connection URL")

    # API
    api_host: str = Field("0.0.0.0", description="v2 API bind address")
    api_port: int = Field(9000, description="v2 API port")

    # Security
    operator_api_key: str = Field(..., description="Operator API key (hashed at startup)")
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="CORS allowed origins — never use * in production",
    )
    debug: bool = Field(False, description="Never true in production")

    # Board
    board_dir: str = Field("./board", description="Path to v1 board directory")

    # RAG
    embedding_model: str = Field("all-MiniLM-L6-v2")
    rag_top_k: int = Field(5)


def get_settings() -> Settings:
    """Return validated settings. Fails at startup if required fields are missing."""
    return Settings()
```

#### Day 4 Todo Checklist

- [ ] Create `config/__init__.py` and `config/settings.py`
- [ ] Create `config/logging.py` (structured JSON logging)
- [ ] Copy `.env.example` from old repo; replace all values with `<PLACEHOLDER>`
- [ ] Add note at top of `.env.example`: "Never commit .env — this file is the template only"
- [ ] Write `tests/unit/test_settings.py` — test that startup fails when `DATABASE_URL` is missing
- [ ] Commit: `feat(config): centralised pydantic-settings with required-field validation`

---

#### Day 5 — DOCS.md + Sprint 0 Review

- [ ] Write `docs/SECURITY.md` — copy the threat model from Section 4 of this document
- [ ] Write `docs/CODING_GUIDELINES.md` — copy Section 5 of this document
- [ ] Update `README.md` with setup instructions for the new repo
- [ ] Run `pre-commit run --all-files` — everything must pass
- [ ] Run the CI manually via `gh workflow run ci.yml`
- [ ] Sprint 0 review: all checkboxes above ticked ✅

**Sprint 0 Definition of Done:**
- [ ] Pre-commit blocks fake secrets from being committed
- [ ] CI pipeline runs and enforces lint + format on every push
- [ ] `config/settings.py` fails loudly if `DATABASE_URL` is absent
- [ ] `.env` is gitignored; `.env.example` has only `<PLACEHOLDER>` values
- [ ] Branch protection on `main` is enforced

---

### Sprint 1: Security Primitives

**Duration:** 1 week  
**Goal:** Build the security foundation that every subsequent sprint will depend on.  
**Output:** Working API key auth, rate limiter, input sanitiser, and safe XML parser — all tested.

---

#### Day 1 — API Key Module (`core/auth.py`)

```python
# core/auth.py
import hashlib
import hmac
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Agent


def generate_key(prefix: str = "clowder") -> str:
    """Generate a cryptographically random 256-bit key."""
    return f"{prefix}_{secrets.token_hex(32)}"


def hash_key(key: str) -> str:
    """One-way hash a key for safe database storage (SHA-256 + constant-time)."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_key(plaintext: str, stored_hash: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    return hmac.compare_digest(hash_key(plaintext), stored_hash)


async def require_agent_auth(
    x_api_key: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> Agent:
    """FastAPI dependency — validates X-API-Key and returns the authenticated agent."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    key_hash = hash_key(x_api_key)
    result = await db.execute(
        select(Agent).where(Agent.api_key_hash == key_hash)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return agent


async def require_operator_auth(
    x_operator_key: Annotated[str | None, Header()] = None,
) -> None:
    """FastAPI dependency — validates X-Operator-Key against the env var."""
    from config.settings import get_settings
    settings = get_settings()
    if not x_operator_key or not verify_key(x_operator_key, hash_key(settings.operator_api_key)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator authentication required",
        )
```

#### Day 1 Todo Checklist

- [ ] Create `core/__init__.py` and `core/auth.py`
- [ ] Create `scripts/generate_keys.py` (CLI tool to generate operator + agent keys)
- [ ] Write `tests/unit/test_auth.py`:
  - [ ] Test `generate_key` produces unique values each call
  - [ ] Test `verify_key` returns True for matching key/hash
  - [ ] Test `verify_key` returns False for wrong key
  - [ ] Test `require_agent_auth` raises 401 when header is missing
  - [ ] Test `require_agent_auth` raises 401 when key is invalid
  - [ ] Test `require_operator_auth` raises 403 when key is wrong
- [ ] Run `pytest tests/unit/test_auth.py` — all pass
- [ ] Commit: `feat(core/auth): API key generation, hashing, and FastAPI dependencies`

---

#### Day 2 — Rate Limiter (`core/rate_limit.py`)

```python
# core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Per-endpoint limit strings (use as decorator args)
LIMIT_DEFAULT = "60/minute"
LIMIT_MESSAGE_POST = "30/minute"
LIMIT_TOKEN_LOG = "10/minute"
LIMIT_AGENT_REGISTER = "5/hour"
LIMIT_WS_CONNECT = "10/minute"
```

#### Day 2 Todo Checklist

- [ ] Create `core/rate_limit.py`
- [ ] Add `slowapi` exception handler to the app factory (returns 429 JSON)
- [ ] Write `tests/unit/test_rate_limit.py` — test that 429 is returned after limit is hit
- [ ] Commit: `feat(core/rate_limit): slowapi rate limiter with per-endpoint limits`

---

#### Day 3 — Input Sanitiser (`core/sanitise.py`)

```python
# core/sanitise.py
from pydantic import field_validator


MAX_MESSAGE_LENGTH = 10_000      # chat message content
MAX_TASK_RESULT_LENGTH = 50_000  # task completion result
MAX_BIO_LENGTH = 2_000           # agent bio
MAX_CHANNEL_NAME_LENGTH = 64     # channel identifier
MAX_SENDER_LENGTH = 128          # agent name / sender identifier


def validate_length(value: str, max_len: int, field_name: str) -> str:
    """Reusable Pydantic field validator for string length."""
    if len(value) > max_len:
        raise ValueError(f"{field_name} exceeds maximum length of {max_len} characters")
    return value.strip()


def validate_channel_name(name: str) -> str:
    """Channel names: alphanumeric + hyphens only, 1-64 chars."""
    import re
    if not re.fullmatch(r"[a-z0-9\-]{1,64}", name):
        raise ValueError(
            "Channel name must be 1-64 lowercase alphanumeric characters or hyphens"
        )
    return name
```

#### Day 3 Todo Checklist

- [ ] Create `core/sanitise.py`
- [ ] Write `tests/unit/test_sanitise.py`:
  - [ ] Test that `validate_length` raises on oversized input
  - [ ] Test that `validate_channel_name` rejects names with spaces, slashes, `..`
  - [ ] Test path traversal in channel name is rejected
- [ ] Commit: `feat(core/sanitise): input length and content validators`

---

#### Day 4 — Safe XML Parser (`core/xml_safe.py`) + Body Size Middleware

```python
# core/xml_safe.py
import defusedxml.ElementTree as ET

from fastapi import HTTPException


def parse_svg(svg_text: str) -> None:
    """
    Validate an SVG string — safe XML parsing via defusedxml.

    Protects against: XXE injection, billion-laughs DoS, quadratic blowup.
    Raises HTTPException(422) on any violation.
    """
    MAX_SVG_BYTES = 51_200  # 50 KB

    if len(svg_text.encode()) > MAX_SVG_BYTES:
        raise HTTPException(status_code=422, detail="Avatar SVG exceeds 50 KB limit")

    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid SVG: {exc}") from exc

    tag = root.tag
    if not (tag == "svg" or tag.endswith("}svg")):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid SVG: root element is '{tag}', expected 'svg'",
        )
```

```python
# api/middleware.py  — request body size limiter
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

MAX_BODY_BYTES = 512 * 1024  # 512 KB


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > MAX_BODY_BYTES:
                return Response(
                    '{"detail":"Request body too large"}',
                    status_code=413,
                    media_type="application/json",
                )
        return await call_next(request)
```

#### Day 4 Todo Checklist

- [ ] Create `core/xml_safe.py`
- [ ] Create `api/middleware.py` with `BodySizeLimitMiddleware`
- [ ] Write `tests/unit/test_xml_safe.py`:
  - [ ] Test valid SVG passes
  - [ ] Test SVG > 50 KB raises 422
  - [ ] Test malformed XML raises 422
  - [ ] Test non-SVG root raises 422
  - [ ] Test XXE attempt is blocked (use `<!ENTITY xxe SYSTEM "file:///etc/passwd">`)
  - [ ] Test billion-laughs attempt is blocked
- [ ] Write `tests/security/test_body_size.py`:
  - [ ] POST with `content-length: 600000` → 413
- [ ] Commit: `feat(core): safe XML parser and body-size-limit middleware`

---

#### Day 5 — Custom Error Handler + Sprint 1 Review

```python
# core/errors.py
from fastapi import Request
from fastapi.responses import JSONResponse


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler — never expose stack traces to clients.
    Log the full traceback internally; return a sanitised message externally.
    """
    import logging
    import uuid
    request_id = str(uuid.uuid4())[:8]
    logging.exception(f"Unhandled error [{request_id}]: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )
```

#### Day 5 Todo Checklist

- [ ] Create `core/errors.py`
- [ ] Register the generic exception handler in the app factory
- [ ] Write `tests/security/test_auth_endpoints.py` — try every router without an API key → all return 401/403
- [ ] Run full `pytest tests/unit/ tests/security/` — all pass
- [ ] Sprint 1 review: all checkboxes above ticked ✅

**Sprint 1 Definition of Done:**
- [ ] `pytest tests/unit/test_auth.py` — all pass
- [ ] `pytest tests/unit/test_xml_safe.py` — XXE attempt is blocked
- [ ] `pytest tests/security/test_auth_endpoints.py` — every endpoint returns 401 without a key
- [ ] `pytest tests/unit/test_rate_limit.py` — 429 returned after limit hit
- [ ] `pytest tests/unit/test_sanitise.py` — oversized and path-traversal inputs rejected

---

### Sprint 2: Database & Schema

**Duration:** 1 week  
**Goal:** Secure database foundation — schema with constraints, migration history, and a test DB.  
**Output:** All 16 tables created (adding `api_keys` and `conflicts`), with field-length constraints.

---

#### Day 1 — ORM Models with Security Constraints

Key additions over the original `models.py`:

1. `api_key_hash` column on `Agent`
2. `CheckConstraint` on all Text fields for length limits
3. `conflicts` table (replaces in-memory `_conflicts` list)
4. `api_keys` table for key rotation support

```python
# Additions to api/models.py (excerpt)
from sqlalchemy import CheckConstraint, Text

class Agent(Base):
    # ... (existing columns) ...
    api_key_hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True)

    __table_args__ = (
        CheckConstraint("char_length(bio) <= 2000", name="ck_agents_bio_length"),
    )


class ChatMessage(Base):
    # ... (existing columns) ...
    __table_args__ = (
        CheckConstraint("char_length(content) <= 10000", name="ck_messages_content_length"),
    )


class Conflict(Base):
    __tablename__ = "conflicts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    local_agent: Mapped[str] = mapped_column(String(128), nullable=False)
    remote_agent: Mapped[Optional[str]] = mapped_column(String(128))
    local_result: Mapped[Optional[str]] = mapped_column(Text)
    remote_status: Mapped[Optional[str]] = mapped_column(String(32))
    logged_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

#### Day 1 Todo Checklist

- [ ] Update `api/models.py` — add `api_key_hash` to `Agent`
- [ ] Add `CheckConstraint` on `ChatMessage.content`, `Agent.bio`, `Task.result`
- [ ] Add `Conflict` table
- [ ] Write `tests/unit/test_models.py` — test length constraints raise `IntegrityError`
- [ ] Commit: `feat(api/models): add api_key_hash, field constraints, Conflict table`

---

#### Day 2 — Alembic Migration

```bash
# Generate migration for the new schema
alembic revision --autogenerate -m "v3_secure_schema"
alembic upgrade head

# Verify the migration creates all tables
psql clowder -c "\dt"
```

#### Day 2 Todo Checklist

- [ ] Run `alembic revision --autogenerate -m "v3_secure_schema"`
- [ ] Review the generated migration — check every constraint is present
- [ ] Test migration: `alembic upgrade head` on a clean database
- [ ] Test rollback: `alembic downgrade -1` then `alembic upgrade head` again
- [ ] Commit: `feat(migrations): v3 secure schema migration`

---

#### Day 3 — Docker Compose Hardening

```yaml
# docker-compose.yml (production-safe version)
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER_FILE: /run/secrets/pg_user
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
      POSTGRES_DB: clowder
    ports:
      # Bind to loopback only — not exposed to the network
      - "127.0.0.1:5432:5432"
    secrets:
      - pg_user
      - pg_password
    restart: unless-stopped

secrets:
  pg_user:
    file: ./secrets/pg_user.txt    # gitignored
  pg_password:
    file: ./secrets/pg_password.txt  # gitignored
```

#### Day 3 Todo Checklist

- [ ] Create `secrets/` directory; add to `.gitignore`
- [ ] Generate strong DB credentials: `openssl rand -base64 32 > secrets/pg_password.txt`
- [ ] Update `docker-compose.yml` to use Docker secrets
- [ ] Bind postgres to `127.0.0.1:5432` (not `0.0.0.0:5432`)
- [ ] Update `Dockerfile` — add `USER 1001` (non-root)
- [ ] Test: `docker-compose up postgres` and confirm connection works
- [ ] Commit: `feat(docker): Docker secrets, non-root user, localhost-only DB binding`

---

#### Day 4 — Test Database Fixtures

```python
# tests/conftest.py additions
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://clowder:clowder@localhost:5433/clowder_test",
)

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

#### Day 4 Todo Checklist

- [ ] Update `tests/conftest.py` with new fixture for v3 schema
- [ ] Add `postgres-test` service to `docker-compose.yml` under `--profile test`
- [ ] Write `tests/integration/test_db_constraints.py` — verify length constraints fire
- [ ] Run `docker-compose --profile test up -d postgres-test`
- [ ] Run `pytest tests/integration/test_db_constraints.py` — all pass
- [ ] Commit: `test: add DB fixture and constraint integration tests`

---

#### Day 5 — Sprint 2 Review

- [ ] `alembic upgrade head` on clean DB — no errors
- [ ] `docker-compose up postgres` — uses secrets, bound to loopback
- [ ] `pytest tests/unit/test_models.py` — length constraints enforced
- [ ] Run `pip-audit -r requirements.lock` — no high/critical CVEs

**Sprint 2 Definition of Done:**
- [ ] All 16 tables created by Alembic migration
- [ ] `api_key_hash` column exists on `agents` table
- [ ] PostgreSQL bound to `127.0.0.1:5432` in docker-compose
- [ ] DB credentials come from Docker secrets, not environment variables
- [ ] Dockerfile runs as `USER 1001` (non-root)

---

### Sprint 3: API Routers — Secured

**Duration:** 1 week  
**Goal:** Rebuild all API endpoints with auth, input validation, and rate limiting on every route.  
**Output:** A fully authenticated REST API that returns 401 to unauthenticated requests.

---

#### Day 1 — App Factory + Dependencies

```python
# api/app.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.middleware import BodySizeLimitMiddleware
from config.settings import get_settings
from core.errors import generic_exception_handler
from core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    init_embedding_service(get_settings().embedding_model)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Clowder v3",
        version="3.0.0",
        lifespan=lifespan,
        debug=False,   # NEVER pass settings.debug — always false in the app object
        docs_url="/docs" if settings.debug else None,   # hide docs in production
        redoc_url=None,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "X-API-Key", "X-Operator-Key"],
    )

    # Register routers
    from api.routers import agents, chat, tasks, tokens, teams, governance, ideas, context
    app.include_router(agents.router)
    app.include_router(chat.router)
    app.include_router(tasks.router)
    # ... etc.

    return app


app = create_app()
```

#### Day 1 Todo Checklist

- [ ] Create `api/app.py` with `create_app()` factory
- [ ] Create `api/dependencies.py` with `require_agent_auth` and `require_operator_auth`
- [ ] Register `BodySizeLimitMiddleware` and `slowapi` in the app factory
- [ ] Set `docs_url=None` in production (hide FastAPI's interactive docs)
- [ ] Commit: `feat(api): secure app factory with auth, rate limit, and CORS'`

---

#### Day 2 — Tasks Router (most critical auth surface)

Every task operation must authenticate:

```python
# api/routers/tasks.py (excerpt)
from core.auth import require_agent_auth
from core.rate_limit import limiter, LIMIT_DEFAULT
from core.sanitise import MAX_TASK_RESULT_LENGTH

@router.post("/{task_id}/claim")
@limiter.limit(LIMIT_DEFAULT)
async def claim_task(
    request: Request,
    task_id: str,
    req: ClaimRequest,
    current_agent: Agent = Depends(require_agent_auth),
    db: AsyncSession = Depends(get_db),
):
    # The agent in the token is authoritative — ignore req.agent_name if provided
    result = await db.execute(
        update(Task)
        .where(Task.id == task_id, Task.status == "pending")
        .values(status="claimed", claimed_by=current_agent.name, claimed_at=req.claimed_at)
    )
    await db.commit()
    claimed = result.rowcount == 1

    # RAG context returned SEPARATELY — never merged into task.description
    context_items = []
    if claimed:
        context_items = await _fetch_rag_context(db, task_id, current_agent.name)

    return {"claimed": claimed, "context_items": context_items}
```

#### Day 2 Todo Checklist

- [ ] Create `api/routers/tasks.py` with `claim` and `complete` requiring `require_agent_auth`
- [ ] Fix: agent identity comes from the API key, not from the request body
- [ ] Fix: RAG context returned as a separate field, never merged into `task.description`
- [ ] Fix: replace in-memory `_conflicts` list with `Conflict` DB table
- [ ] Write `tests/security/test_task_auth.py`:
  - [ ] Claim without API key → 401
  - [ ] Complete as different agent → 403
  - [ ] Claim same task twice → 409
- [ ] Commit: `feat(api/tasks): authenticated claim and complete; RAG context separated'`

---

#### Day 3 — Agents, Chat, and Tokens Routers

For each router, the pattern is identical:
1. Add `Depends(require_agent_auth)` or `Depends(require_operator_auth)`
2. Add `@limiter.limit(...)` decorator
3. Apply `sanitise` validators to string fields
4. Write one happy-path + one 401 test

#### Day 3 Todo Checklist

- [ ] Create `api/routers/agents.py` — profile update verifies caller owns agent
- [ ] Create `api/routers/chat.py` — `sender` field comes from API key identity, not request body
- [ ] Create `api/routers/tokens.py` — requires agent auth; throttled to 10/min
- [ ] Write security tests for each router
- [ ] Commit: `feat(api/routers): agents, chat, tokens — all authenticated + rate limited'`

---

#### Day 4 — Governance and Ideas Routers

Governance endpoints require **operator** auth (not agent auth):

```python
# api/routers/governance.py
@router.get("/token-report")
async def token_report(
    _: None = Depends(require_operator_auth),
    db: AsyncSession = Depends(get_db),
):
    ...
```

#### Day 4 Todo Checklist

- [ ] Create `api/routers/governance.py` — requires operator auth
- [ ] Create `api/routers/ideas.py` — voting requires agent auth; approval requires operator auth
- [ ] Create `api/routers/standards.py` — requires operator auth
- [ ] Write `tests/security/test_governance_auth.py` — operator endpoints return 403 to agents
- [ ] Commit: `feat(api/routers): governance and ideas — operator auth enforced'`

---

#### Day 5 — Sprint 3 Review

- [ ] Run `pytest tests/security/` — all pass (all endpoints return 401/403 without auth)
- [ ] Manually test with `curl`:
  ```bash
  # Should return 401
  curl -X POST http://localhost:9000/api/tasks/test-id/claim \
    -H "Content-Type: application/json" \
    -d '{"claimed_at": "2026-01-01T00:00:00"}'

  # Should return 200
  curl -X POST http://localhost:9000/api/tasks/test-id/claim \
    -H "Content-Type: application/json" \
    -H "X-API-Key: clowder_ag_yourkey..." \
    -d '{"claimed_at": "2026-01-01T00:00:00"}'
  ```

**Sprint 3 Definition of Done:**
- [ ] Every `POST`, `PATCH`, `DELETE` endpoint returns 401 without `X-API-Key`
- [ ] Governance endpoints return 403 to agent keys (operator key required)
- [ ] Task claim uses API key identity, not request-body `agent_name`
- [ ] RAG context is a separate response field — task description is never mutated
- [ ] `POST /api/conflicts` persists to DB, not in-memory list

---

### Sprint 4: WebSocket Security

**Duration:** 1 week  
**Goal:** Secure the real-time WebSocket layer.  
**Output:** Authenticated WS connections; impersonation and flooding are impossible.

---

#### Day 1 — Authenticated WebSocket Connection

```python
# api/ws.py (updated)
from fastapi import WebSocket, WebSocketDisconnect, Query, status
from core.auth import hash_key
from api.models import Agent

@app.websocket("/ws/{room}")
async def websocket_endpoint(
    room: str,
    ws: WebSocket,
    api_key: str | None = Query(None, alias="key"),
):
    # Authenticate before accepting the connection
    if not api_key:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with SessionLocal() as db:
        agent = await db.execute(
            select(Agent).where(Agent.api_key_hash == hash_key(api_key))
        )
        agent = agent.scalar_one_or_none()

    if not agent:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(room, ws)
    # ... rest of handler, with agent.name used as authoritative sender
```

**Frontend connection URL format:**
```typescript
const ws = new WebSocket(`ws://localhost:9000/ws/main-hall?key=${apiKey}`)
```

#### Days 1-2 Todo Checklist

- [ ] Update `api/ws.py` — require `?key=` query param before accepting connection
- [ ] Validate key against DB; reject with `1008 Policy Violation` if invalid
- [ ] Use `agent.name` from DB as authoritative `sender` — ignore any sender in message body
- [ ] Validate `content` length ≤ 10,000 chars before persisting
- [ ] Disconnect clients that send invalid messages (don't silently ignore)
- [ ] Write `tests/integration/test_ws_auth.py`:
  - [ ] Connect without `?key=` → connection closed immediately
  - [ ] Connect with invalid key → connection closed with 1008
  - [ ] Connect with valid key → messages can be sent/received
  - [ ] Message with `content` > 10,000 chars → connection closed

---

#### Day 3 — Connection Limits

```python
# api/ws.py — per-IP connection tracking
from collections import defaultdict

_connections_per_ip: dict[str, int] = defaultdict(int)
MAX_CONNECTIONS_PER_IP = 10

class ConnectionManager:
    async def connect(self, room: str, ws: WebSocket, client_ip: str) -> bool:
        if _connections_per_ip[client_ip] >= MAX_CONNECTIONS_PER_IP:
            await ws.close(code=1008)
            return False
        await ws.accept()
        _connections_per_ip[client_ip] += 1
        # ... add to room
        return True

    def disconnect(self, room: str, ws: WebSocket, client_ip: str) -> None:
        _connections_per_ip[client_ip] = max(0, _connections_per_ip[client_ip] - 1)
        # ... remove from room
```

#### Days 3-4 Todo Checklist

- [ ] Implement per-IP connection counter in `ConnectionManager`
- [ ] Return `1008 Policy Violation` when limit exceeded
- [ ] Write test: open 11 connections from same IP → 11th is rejected
- [ ] Add heartbeat ping/pong to detect dead connections

---

#### Day 5 — Sprint 4 Review

**Sprint 4 Definition of Done:**
- [ ] WebSocket connections without valid `?key=` are rejected before `accept()`
- [ ] WebSocket `sender` field is derived from API key, never from message body
- [ ] Messages with `content` > 10,000 chars are rejected and connection is closed
- [ ] Per-IP connection limit of 10 is enforced
- [ ] All WS tests pass

---

### Sprint 5: Frontend Security

**Duration:** 1 week  
**Goal:** Secure the Vue 3 frontend — API key management, no XSS vectors, strict TypeScript.  
**Output:** Frontend sends `X-API-Key` on every request; no `v-html` with untrusted content.

---

#### Day 1 — API Key Storage and Client Update

```typescript
// frontend/src/api/auth.ts
const KEY_STORAGE_KEY = "clowder_api_key"

export function getApiKey(): string | null {
  return sessionStorage.getItem(KEY_STORAGE_KEY)
}

export function setApiKey(key: string): void {
  // sessionStorage is cleared when the browser tab closes — safer than localStorage
  sessionStorage.setItem(KEY_STORAGE_KEY, key)
}

export function clearApiKey(): void {
  sessionStorage.removeItem(KEY_STORAGE_KEY)
}
```

```typescript
// frontend/src/api/client.ts (updated)
import { getApiKey } from "./auth"

function buildHeaders(body?: unknown): HeadersInit {
  const headers: Record<string, string> = {}
  if (body) headers["Content-Type"] = "application/json"
  const key = getApiKey()
  if (key) headers["X-API-Key"] = key
  return headers
}
```

```typescript
// frontend/src/hooks/useWebSocket.ts (updated)
import { getApiKey } from "../api/auth"

function buildWsUrl(room: string): string {
  const key = getApiKey()
  const base = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/${room}`
  return key ? `${base}?key=${encodeURIComponent(key)}` : base
}
```

#### Days 1-2 Todo Checklist

- [ ] Create `frontend/src/api/auth.ts` (sessionStorage key management)
- [ ] Create `frontend/src/pages/Login.vue` — minimal key-entry form
- [ ] Add `/login` route that redirects to `/chat/main-hall` on success
- [ ] Update `frontend/src/api/client.ts` — add `X-API-Key` header to every request
- [ ] Update `useWebSocket.ts` — append `?key=...` to WS URL
- [ ] Add route guard in `router.ts` — redirect to `/login` if no API key in sessionStorage
- [ ] Commit: `feat(frontend): API key auth — sessionStorage, headers, route guard`

---

#### Days 3-4 — XSS Audit

```bash
# Find all v-html usages in the frontend
grep -r "v-html" frontend/src/ --include="*.vue"

# For each result:
# - If content is user-generated → remove v-html, use {{ }} text interpolation
# - If content is trusted markup → add DOMPurify sanitisation
npm install dompurify
npm install --save-dev @types/dompurify
```

```typescript
// Safe pattern for trusted HTML (e.g. markdown render)
import DOMPurify from "dompurify"
const safeHtml = DOMPurify.sanitize(rawHtml, { ALLOWED_TAGS: ["p", "b", "em", "a"] })
```

#### Days 3-4 Todo Checklist

- [ ] Run `grep -r "v-html" frontend/src/` — audit every result
- [ ] Replace user-content `v-html` with text interpolation `{{ }}`
- [ ] For trusted HTML: wrap with `DOMPurify.sanitize()`
- [ ] Add `dompurify` to `package.json`
- [ ] Run `npm audit --audit-level=high` — fix all HIGH/CRITICAL findings
- [ ] Add `eslint-plugin-security` and configure XSS rules

---

#### Day 5 — TypeScript Strict Mode + Sprint 5 Review

```json
// frontend/tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUncheckedIndexedAccess": true
  }
}
```

- [ ] Enable `"strict": true` in `tsconfig.json`
- [ ] Fix all TypeScript errors introduced by strict mode
- [ ] Run `npm run build` — zero errors, zero warnings
- [ ] Run `npm audit` — no high/critical vulnerabilities

**Sprint 5 Definition of Done:**
- [ ] `npm run build` succeeds with `"strict": true`
- [ ] Every API call includes `X-API-Key` header
- [ ] WebSocket URL includes `?key=` query param
- [ ] No `v-html` with user-generated content
- [ ] `npm audit` returns no HIGH or CRITICAL findings
- [ ] Route guard redirects unauthenticated users to `/login`

---

### Sprint 6: CI/CD & Docker Production Hardening

**Duration:** 1 week  
**Goal:** Automated pipeline that enforces every security control on every push.  
**Output:** Pushing bad code to main is physically prevented by CI.

---

#### Day 1 — Multi-stage Dockerfile

```dockerfile
# Dockerfile
# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml requirements.lock ./
RUN pip install --no-cache-dir pip-tools && \
    pip install --no-cache-dir -r requirements.lock

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime
WORKDIR /app

# Non-root user — UID 1001 (not root, not the default "app" user)
RUN groupadd --gid 1001 clowder && \
    useradd --uid 1001 --gid clowder --no-create-home clowder

# Copy only installed packages from builder
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source — no .env, no .git, no secrets
COPY --chown=clowder:clowder api/ ./api/
COPY --chown=clowder:clowder agents/ ./agents/
COPY --chown=clowder:clowder config/ ./config/
COPY --chown=clowder:clowder core/ ./core/
COPY --chown=clowder:clowder alembic/ ./alembic/
COPY --chown=clowder:clowder alembic.ini ./

USER 1001

EXPOSE 9000
CMD ["python", "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "9000"]
```

#### Day 1 Todo Checklist

- [ ] Rewrite `Dockerfile` as multi-stage (builder + runtime)
- [ ] Add `USER 1001` to runtime stage
- [ ] Copy only necessary source directories — no `.env`, `.git`, `secrets/`, `board/`
- [ ] Test: `docker build .` succeeds; `docker run` starts the API
- [ ] Test: `docker run` process is not running as root (`whoami` inside container = `clowder`)

---

#### Day 2 — Docker Compose Production Profile

```yaml
# docker-compose.prod.yml (production overrides)
services:
  api:
    build:
      context: .
      target: runtime
    ports:
      - "127.0.0.1:9000:9000"    # Bind to loopback — nginx handles external traffic
    environment:
      - CLOWDER_DEBUG=false
    read_only: true               # Container filesystem is read-only
    tmpfs:
      - /tmp                      # Allow only /tmp to be writable
    security_opt:
      - no-new-privileges:true    # Prevent privilege escalation

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro   # TLS certs (gitignored)
    read_only: true
    tmpfs:
      - /var/cache/nginx
      - /var/run
      - /tmp
```

#### Day 2 Todo Checklist

- [ ] Create `docker-compose.prod.yml` with production security overrides
- [ ] Add `read_only: true` and `no-new-privileges:true` to api + nginx services
- [ ] Generate self-signed cert for local dev: `openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem`
- [ ] Add `nginx/ssl/` to `.gitignore`
- [ ] Document Let's Encrypt cert provisioning in `docs/DEPLOYMENT.md`

---

#### Day 3 — Nginx TLS + Security Headers (Final)

```nginx
# nginx/default.conf (final production version)

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: image/svg+xml; connect-src 'self' wss:; font-src 'self';" always;

    root /usr/share/nginx/html;
    index index.html;

    location / { try_files $uri $uri/ /index.html; }

    location /api/ {
        proxy_pass         http://api:9000/api/;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass         http://api:9000/ws/;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_read_timeout 300s;
    }

    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1024;
}
```

#### Day 3 Todo Checklist

- [ ] Update `nginx/default.conf` with HTTPS + HSTS
- [ ] Test: `curl -I http://localhost` → `301 to https`
- [ ] Test: `curl -I https://localhost --insecure` → `200`, headers present
- [ ] Run `ssllabs.com` scan (or `testssl.sh` locally) — no A/B grade issues

---

#### Days 4-5 — CI Pipeline Hardening + Sprint 6 Review

- [ ] Add `trivy` scan step to CI — fail on HIGH/CRITICAL container CVEs
- [ ] Add `gitleaks` scan step to CI
- [ ] Add `npm audit --audit-level=high` to CI frontend job
- [ ] Add branch protection rules: require 1 approval + all CI jobs passing
- [ ] Test CI end-to-end: push a branch, confirm every step runs

**Sprint 6 Definition of Done:**
- [ ] Docker container runs as UID 1001 (not root)
- [ ] Dockerfile uses multi-stage build
- [ ] PostgreSQL bound to `127.0.0.1:5432`
- [ ] Nginx serves HTTPS with TLS 1.2/1.3 only
- [ ] All 6 security headers present in responses
- [ ] HTTP → HTTPS redirect working
- [ ] CI pipeline fails on secret leaks, CVEs, lint errors, and failed tests

---

### Sprint 7: Testing, Docs & Production Readiness

**Duration:** 1 week  
**Goal:** Final polish — test coverage, updated documentation, production smoke test.  
**Output:** The system is production-ready. Tag `v3.0.0-secure`.

---

#### Day 1 — Test Coverage to 80%

```bash
# Run coverage report
pytest tests/ --cov=api --cov=core --cov=config --cov=agents \
  --cov-report=html --cov-report=term-missing

# Open coverage report
open htmlcov/index.html
```

- [ ] Identify uncovered modules from the HTML report
- [ ] Write tests for uncovered code paths (prioritise security-critical modules)
- [ ] Target: ≥80% coverage on every module in `api/`, `core/`, `config/`
- [ ] Commit: `test: increase coverage to ≥80%`

---

#### Day 2 — Full Security Test Suite

Run the complete `tests/security/` suite and verify everything passes:

```bash
pytest tests/security/ -v
```

Security test checklist (all must pass):

- [ ] `test_cors.py::test_disallowed_origin_rejected` — non-whitelisted origin returns 403
- [ ] `test_auth_endpoints.py::test_all_write_endpoints_require_auth` — every POST/PATCH/DELETE returns 401
- [ ] `test_auth_endpoints.py::test_governance_requires_operator_key` — agent key on governance → 403
- [ ] `test_injection.py::test_oversized_body_rejected` — 513 KB body → 413
- [ ] `test_injection.py::test_oversized_message_content` — 15,000 char message → 422
- [ ] `test_injection.py::test_xxe_svg_blocked` — XXE SVG → 422
- [ ] `test_injection.py::test_billion_laughs_blocked` — billion-laughs SVG → 422
- [ ] `test_ws_auth.py::test_ws_no_key_rejected` — WS without `?key=` → connection closed
- [ ] `test_ws_auth.py::test_ws_sender_from_key_not_body` — sender in response = key identity

---

#### Day 3 — Documentation Updates

- [ ] Update `docs/DEPLOYMENT.md` — new step-by-step deploy guide for v3
- [ ] Update `docs/API_REFERENCE.md` — add `X-API-Key` header to every endpoint
- [ ] Update `README.md` — first-run setup for v3 (generate keys, set .env, docker-compose up)
- [ ] Write `docs/SECURITY.md`:
  - [ ] Threat model (who might attack this, what they could do)
  - [ ] Key management (how to generate, rotate, and revoke API keys)
  - [ ] Known limitations (LAN only, no MFA, no secrets vault)
  - [ ] Incident response (what to do if a key is compromised)

---

#### Day 4 — Production Smoke Test

This is the final end-to-end verification. Perform every step manually:

```bash
# 1. Start the full production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile v2 up -d

# 2. Generate operator key
python scripts/generate_keys.py --type operator
# → copy to .env as OPERATOR_API_KEY

# 3. Register a test agent
python scripts/generate_keys.py --type agent --name test-agent
# → note the returned key

# 4. Register the agent via API
curl -X POST https://localhost/api/agents/register \
  --insecure \
  -H "Content-Type: application/json" \
  -H "X-API-Key: clowder_ag_yourkey..." \
  -d '{"name": "test-agent", "role": "general"}'
# → {"ok": true}

# 5. Unauthenticated request must fail
curl -X POST https://localhost/api/agents/register \
  --insecure \
  -H "Content-Type: application/json" \
  -d '{"name": "evil", "role": "admin"}'
# → 401 Unauthorized

# 6. Create a task (operator)
curl -X POST https://localhost/api/tasks \
  --insecure \
  -H "Content-Type: application/json" \
  -H "X-Operator-Key: clowder_op_yourkey..." \
  -d '{"title": "Smoke test task", "description": "Test"}'
# → {"id": "abc123", ...}

# 7. Claim the task
curl -X POST https://localhost/api/tasks/abc123/claim \
  --insecure \
  -H "Content-Type: application/json" \
  -H "X-API-Key: clowder_ag_yourkey..." \
  -d '{"claimed_at": "2026-04-07T00:00:00Z"}'
# → {"claimed": true, "context_items": []}

# 8. Complete the task
curl -X POST https://localhost/api/tasks/abc123/complete \
  --insecure \
  -H "Content-Type: application/json" \
  -H "X-API-Key: clowder_ag_yourkey..." \
  -d '{"result": "Done"}'
# → {"ok": true}

# 9. Check governance report (operator only)
curl https://localhost/api/v2/governance/token-report \
  --insecure \
  -H "X-Operator-Key: clowder_op_yourkey..."
# → [...]

curl https://localhost/api/v2/governance/token-report \
  --insecure \
  -H "X-API-Key: clowder_ag_yourkey..."
# → 403 Forbidden

# 10. Check WebSocket
wscat -c "wss://localhost/ws/main-hall?key=clowder_ag_yourkey..." --no-check
# → Connected, receives last 50 messages

wscat -c "wss://localhost/ws/main-hall"  --no-check
# → Connection closed immediately
```

Smoke test checklist:

- [ ] Docker stack starts cleanly: `docker-compose ps` — all services `Up`
- [ ] HTTP → HTTPS redirect works
- [ ] `GET /api/health` returns `{"status": "ok"}`
- [ ] Unauthenticated `POST /api/agents/register` → 401
- [ ] Authenticated agent registration → 200
- [ ] Task claim → `{"claimed": true, "context_items": []}`
- [ ] Task complete → `{"ok": true}`
- [ ] Governance endpoint with agent key → 403
- [ ] Governance endpoint with operator key → 200
- [ ] WebSocket without key → closed immediately
- [ ] WebSocket with valid key → connected, messages flow

---

#### Day 5 — Tag v3.0.0-secure

**Final pre-release checklist:**

```bash
# Automated checks
pytest tests/ --cov --cov-fail-under=80              # ✅ Tests pass, ≥80% coverage
pip-audit -r requirements.lock                        # ✅ No HIGH/CRITICAL Python CVEs
cd frontend && npm audit --audit-level=high           # ✅ No HIGH/CRITICAL Node CVEs
gitleaks detect --source .                            # ✅ No secrets in source
ruff check .                                          # ✅ No lint errors
mypy --strict api/ core/ config/                      # ✅ No type errors
docker build -t clowder:v3 .                          # ✅ Image builds cleanly
trivy image clowder:v3 --severity HIGH,CRITICAL       # ✅ No HIGH/CRITICAL container CVEs

# Manual checks
# ✅ All smoke test steps pass (Day 4)
# ✅ HTTPS working with security headers
# ✅ No hardcoded credentials in any file in the repo
# ✅ .env is gitignored (run: git status | grep .env → no output)
# ✅ README.md reflects v3 setup instructions
# ✅ docs/SECURITY.md written
```

```bash
# Tag and release
git tag -s v3.0.0-secure -m "Secure rebuild: auth, CORS, rate limiting, TLS, no hardcoded creds"
git push origin v3.0.0-secure

# Create GitHub release
gh release create v3.0.0-secure \
  --title "v3.0.0-secure — Rebuilt with security baked in" \
  --notes "Full changelog in docs/RECREATION_PLAN.md"
```

**Sprint 7 Definition of Done (= Production Ready):**
- [ ] All tests pass; coverage ≥80%
- [ ] `pip-audit` and `npm audit` — no HIGH/CRITICAL CVEs
- [ ] `gitleaks detect` — no secrets in source
- [ ] Smoke test passes end-to-end
- [ ] `docs/SECURITY.md` written
- [ ] `README.md` updated for v3
- [ ] Tagged `v3.0.0-secure` and GitHub Release created

---

### 📊 Sprint Summary Table

| Sprint | Name | Duration | Key Output |
|--------|------|----------|------------|
| Pre-game | The Wipe | 1 day | Old code gone; reference files saved |
| Sprint 0 | Repo Foundation | 1 week | Pre-commit gates, CI skeleton, typed config |
| Sprint 1 | Security Primitives | 1 week | Auth, rate limit, sanitise, defusedxml |
| Sprint 2 | Database & Schema | 1 week | 16 tables, constraints, Docker secrets |
| Sprint 3 | API Routers | 1 week | All endpoints authenticated + rate limited |
| Sprint 4 | WebSocket Security | 1 week | Authenticated WS, connection limits |
| Sprint 5 | Frontend Security | 1 week | API key in every request, no XSS vectors |
| Sprint 6 | CI/CD & Docker | 1 week | Multi-stage image, HTTPS, full CI pipeline |
| Sprint 7 | Testing & Release | 1 week | 80% coverage, smoke test, v3.0.0-secure tag |

**Total: ~8 weeks from wipe to production-ready.**

---

### 🔑 Security Procedures Reference Card

Keep this card visible throughout every sprint:

```
┌─────────────────────────────────────────────────────────────────┐
│                 CLOWDER SECURITY PROCEDURES                     │
├──────────────────────────────────┬──────────────────────────────┤
│  Before every commit             │  Before every sprint         │
│  ──────────────────────────────  │  ────────────────────────    │
│  ✅ pre-commit passes            │  ✅ pip-audit (no HIGH CVEs)  │
│  ✅ No .env in staged files      │  ✅ npm audit (no HIGH CVEs)  │
│  ✅ No secrets in code           │  ✅ gitleaks detect           │
│  ✅ Tests pass locally           │  ✅ All tests pass            │
├──────────────────────────────────┼──────────────────────────────┤
│  When a key is compromised       │  Before production deploy    │
│  ──────────────────────────────  │  ────────────────────────    │
│  1. Revoke key in DB immediately │  ✅ CLOWDER_DEBUG=false       │
│  2. Generate new key             │  ✅ DB bound to 127.0.0.1    │
│  3. Update agent's .env          │  ✅ Docker non-root user      │
│  4. Restart affected service     │  ✅ HTTPS with HSTS enabled   │
│  5. Review access logs           │  ✅ Secrets not in repo       │
└──────────────────────────────────┴──────────────────────────────┘
```
