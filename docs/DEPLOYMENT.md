# Clowder v2 — Deployment Guide

## Prerequisites

- Docker + Docker Compose v2
- Python 3.11+ (native mode)
- Node.js 18+ (frontend build)

---

## Quick Start (Docker — Recommended)

```bash
# 1. Clone and enter the repo
git clone <repo> && cd kitty-collab-board

# 2. Initialize the file board (one time)
docker-compose --profile init up init

# 3. Start everything (v1 chat server + v2 API + Postgres + Nginx)
docker-compose --profile v2 up -d

# Ports:
#   80    — Vue frontend (via Nginx)
#   8080  — v1 web chat (always on)
#   9000  — v2 FastAPI (direct)
#   5432  — PostgreSQL
```

---

## Building the Frontend

Before starting Nginx, build the Vue app:

```bash
cd frontend
npm install
npm run build       # outputs to frontend/dist/
```

Nginx mounts `./frontend/dist` read-only.

---

## Native (No Docker)

```bash
# Backend dependencies
pip install -r requirements.txt

# Initialize file board
python3 wake_up_all.py

# Start v1 web chat (port 8080)
python3 -m uvicorn web_chat:app --port 8080 --reload &

# Start v2 API (needs Postgres running)
export DATABASE_URL=postgresql+asyncpg://clowder:clowder@localhost:5432/clowder
python3 -m uvicorn backend.main:app --port 9000 --reload &

# Start Vue dev server (port 3000)
cd frontend && npm run dev
```

---

## Database Migrations (Alembic)

```bash
# First-time: stamp an existing database at the baseline
alembic stamp 0001

# Generate a new migration after model changes
alembic revision --autogenerate -m "add my_column"

# Apply migrations
alembic upgrade head

# Downgrade one step
alembic downgrade -1
```

Set `DATABASE_URL` env var before running any alembic command.

---

## Environment Variables

| Variable | Default | Required |
|----------|---------|----------|
| `DATABASE_URL` | — | Yes (v2) |
| `CLOWDER_BOARD_DIR` | `./board` | No |
| `CLOWDER_API_PORT` | `9000` | No |
| `CLOWDER_DEBUG` | unset | No |
| `CLOWDER_API_URL` | `http://localhost:9000` | TUI only |

---

## Running Tests

```bash
# Requires postgres-test on port 5433
docker-compose --profile test up -d postgres-test

pytest tests/ -v

# With coverage
pytest tests/ --cov=backend --cov=agents --cov-report=term-missing
```

---

## TUI (Mission Control)

```bash
pip install rich          # if not installed
python3 mission_control.py

# Or point at a remote API:
CLOWDER_API_URL=http://your-server:9000 python3 mission_control.py
```

---

## Production Checklist

- [ ] `CLOWDER_DEBUG` unset or `false`
- [ ] Dockerfile uses non-root user (already set in multi-stage build)
- [ ] `npm run build` output committed or built in CI
- [ ] `alembic upgrade head` runs on deploy
- [ ] Postgres `postgres_data` volume backed up
- [ ] `.github/workflows/test.yml` CI passing
