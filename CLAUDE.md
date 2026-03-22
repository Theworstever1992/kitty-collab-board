# Clowder — Claude Code Project Context

## What This Project Is

**Clowder** is a dual-mode multi-agent coordination platform. Humans and AI
agents (Claude, Qwen, Copilot, Gemini, etc.) coordinate via:

- **v1 (file-based, always on):** `board/` JSON files, `web_chat.py` server,
  port 8080
- **v2 (PostgreSQL + pgvector, production):** FastAPI REST API, port 9000,
  Vue 3 frontend on port 80 via Nginx

Both modes run simultaneously. `AgentClient` routes to v2 when the API is
reachable and silently falls back to v1 `FileBackend` otherwise.

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

# Run all tests (no PostgreSQL needed for file-backend tests)
pytest tests/

# Docker full stack (v2)
docker-compose --profile init up init   # first time only
docker-compose --profile v2 up -d       # postgres + api + nginx
```

No linter config — no flake8, pylint, or pyproject.toml. Python 3.11+.

---

## Architecture — Dual Backend

### v1 File Backend (`agents/file_backend.py`)
- All state in `board/` as JSON files
- All writes via `agents/atomic.py` → `atomic_write()` using `os.replace()`
- **Never** use `open(..., 'w')` on board files — always `atomic_write()`

### v2 PostgreSQL Backend (`backend/`)
- FastAPI app in `backend/main.py`, port 9000
- SQLAlchemy async engine with `asyncpg` driver
- Tables created at startup via FastAPI `lifespan` + `create_tables()`
- `pgvector` extension for 384-dim similarity search

### AgentClient Routing (`agents/agent_client.py`)
- `_probe_api()` hits `GET /api/health`, caches result 30 s
- Online → `PostgresBackend` (REST); offline → `FileBackend` (files)

---

## Key Conventions

- Python 3.11+, **type hints on all function signatures**, docstrings on
  public APIs
- Board files: always `atomic_write()` from `agents/atomic.py`
- Board modules cache `BOARD_DIR` at import — reload when
  `CLOWDER_BOARD_DIR` changes in tests (see `conftest.py`)
- Message `type` values: `chat` `update` `alert` `task` `code` `approval`
  `plan` — validated by `Channel.VALID_MESSAGE_TYPES`
- Avatar SVG: text only, max 50 KB, must parse as valid XML with `<svg>` root

## Test Conventions

- **Framework:** pytest + pytest-asyncio, `asyncio_mode = auto`
- **Do not** add `@pytest.mark.asyncio` manually — it is automatic
- v2 API tests must include the `db_session` fixture to trigger table creation
- Use `board_dir` fixture (monkeypatch + tmp_path) for file-backend tests

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLOWDER_BOARD_DIR` | `./board` | Board root path |
| `DATABASE_URL` | `postgresql+asyncpg://clowder:clowder@localhost:5432/clowder` | v2 DB |
| `TESTING` | unset | Set to `"1"` in tests; forces NullPool on DB engine |
| `TEST_DATABASE_URL` | `postgresql+asyncpg://clowder:clowder@localhost:5433/clowder_test` | Test DB |

---

## Port Map

| Port | Service |
|------|---------|
| 80 | Nginx → Vue SPA + /api proxy (v2 profile) |
| 3000 | Vue Vite dev server |
| 5432 | PostgreSQL production |
| 5433 | PostgreSQL test |
| 8080 | v1 web_chat.py (FastAPI, always on) |
| 9000 | v2 FastAPI (backend.main) |

---

## Security

This repository had a confirmed **malicious supply-chain backdoor** in `meow.py`
(commit `53e4b84`, Feb 27 – Mar 20, 2026 — now removed). A CI security scan
(`scripts/security_scan.py`) runs on every push. See `SECURITY.md` for the
full incident report and device-compromise checklist.

---

## Full Reference

See `.github/copilot-instructions.md` for exhaustive API endpoint docs,
database schema, RAG pipeline details, governance agents, and the complete
meow.py CLI reference.
