# Clowder — Comprehensive Overview, Vulnerability Audit & Secure Recreation Plan

> **Purpose:** This document provides the full current-state inventory, identifies every security
> vulnerability, defines coding guidelines, and lays out the complete step-by-step plan for
> rebuilding the platform with security and structure baked in from day one.
>
> Generated: 2026-04-07

---

## Table of Contents

1. [Current Repository Overview](#1-current-repository-overview)
2. [Full Directory Layout (Annotated)](#2-full-directory-layout-annotated)
3. [Component Inventory](#3-component-inventory)
4. [Security Vulnerabilities — Full Audit](#4-security-vulnerabilities--full-audit)
5. [Coding Guidelines for the New Build](#5-coding-guidelines-for-the-new-build)
6. [New Secure Architecture Design](#6-new-secure-architecture-design)
7. [Proposed New Directory Structure](#7-proposed-new-directory-structure)
8. [Detailed Recreation Checklist](#8-detailed-recreation-checklist)
9. [Technology Stack Decisions](#9-technology-stack-decisions)
10. [Environment & Secrets Strategy](#10-environment--secrets-strategy)

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

When you are ready to wipe and recreate, work through the checklist in **Phase 0 → Phase 10**
in order. Each phase builds on the previous one and ends with a testable checkpoint.
