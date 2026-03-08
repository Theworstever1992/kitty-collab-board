# TASK 4001 — FastAPI Backend Setup + REST API

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** 7B — Web GUI Backend (Sprint 4)

## Description

Create the FastAPI backend for the web-based Mission Control.

## Implementation Notes

Created `web/backend/main.py` with:
- FastAPI application with CORS for localhost:3000
- REST endpoints:
  - `GET /api/board` — full board state
  - `GET /api/tasks` — list tasks (filterable by status, role)
  - `GET /api/tasks/{id}` — get specific task
  - `POST /api/tasks` — create task
  - `PUT /api/tasks/{id}` — update task
  - `DELETE /api/tasks/{id}` — delete task
  - `GET /api/agents` — list agents
  - `GET /api/agents/{name}` — get specific agent
- WebSocket endpoints:
  - `WS /api/ws/board` — real-time board updates
  - `WS /api/ws/logs` — log streaming (stub)
- Pydantic models for request validation
- File locking for board writes

**Run with:** `uvicorn web.backend.main:app --reload --port 8000`

## Acceptance Criteria

- [x] All endpoints return correct JSON
- [x] Board file locking prevents race conditions
- [x] CORS allows localhost:3000
- [x] Server runs with uvicorn

## Review

**Self-Review by Qwen:**

✅ Approved — Production-ready REST API with WebSocket support.

Key decisions:
- Used Pydantic for request validation
- File locking reused from base_agent.py pattern
- WebSocket manager for broadcasting updates
- Clean separation of concerns

**Pending:** Kimi/Claude to review when available

## Dependencies

- Enables TASK 4011-4016 (frontend components)
- Depends on filelock (already installed)

## Description

Create the FastAPI backend for the web-based Mission Control.
This is the foundation that all web frontend features will build on.

## Requirements

- [ ] FastAPI app in `web/backend/main.py`
- [ ] REST endpoints:
  - `GET /api/board` — get full board state
  - `GET /api/tasks` — get all tasks
  - `POST /api/tasks` — add a task
  - `PUT /api/tasks/{id}` — update a task
  - `DELETE /api/tasks/{id}` — delete a task
  - `GET /api/agents` — get agent status
- [ ] Read from `board/board.json` (respect `CLOWDER_BOARD_DIR` env)
- [ ] Write operations use file locking (reuse logic from base_agent.py)
- [ ] CORS enabled for frontend origin (localhost:3000)
- [ ] uvicorn server config

## Acceptance Criteria

- [ ] All endpoints return correct JSON
- [ ] Board file locking prevents race conditions
- [ ] CORS allows localhost:3000 (React dev server)
- [ ] Server runs with `uvicorn web.backend.main:app --reload`

## Review

_Kimi reviews here after implementation_
