# TASK 3001 — FastAPI Backend Setup + REST API

**Assigned:** Qwen (took over from Claude)
**Status:** ✅ done
**Completed:** 2026-03-07
**Completed by:** Kimi
**Started:** 2026-03-06 (Qwen takeover)
**Phase:** 7B — Web-Based GUI

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Create the FastAPI backend for the web-based Mission Control.
This is the foundation that all web frontend features will build on.

## Implementation Notes

Kimi completed the FastAPI backend:
- Created `web/backend/main.py` with full REST API
- Endpoints implemented:
  - `GET /api/health` — health check
  - `GET /api/board` — full board state
  - `GET /api/tasks` — all tasks
  - `POST /api/tasks` — create task
  - `GET /api/tasks/{id}` — get task
  - `PUT /api/tasks/{id}` — update task
  - `DELETE /api/tasks/{id}` — delete task
  - `GET /api/agents` — all agents
  - `GET /api/agents/{name}` — single agent
  - `GET /api/logs/{name}` — agent logs
- WebSocket at `/ws` for real-time updates
- File locking for all write operations (reuses base_agent logic)
- CORS enabled for React dev servers (localhost:3000, 5173)
- Pydantic models for request/response validation
- Priority and role fields fully supported

## Requirements

- [x] FastAPI app in `web/backend/main.py`
- [ ] REST endpoints:
  - `GET /api/board` — get full board state
  - `GET /api/tasks` — get all tasks
  - `POST /api/tasks` — add a task
  - `PUT /api/tasks/{id}` — update a task
  - `DELETE /api/tasks/{id}` — delete a task
  - `GET /api/agents` — get agent status
- [ ] Read from `board/board.json` (respect `CLOWDER_BOARD_DIR` env)
- [ ] Write operations use file locking (reuse logic from base_agent.py)
- [ ] CORS enabled for frontend origin
- [ ] uvicorn server config

## Acceptance Criteria

- [ ] All endpoints return correct JSON
- [ ] Board file locking prevents race conditions
- [ ] CORS allows localhost:3000 (React dev server)
- [ ] Server runs with `uvicorn web.backend.main:app --reload`

## Review

_Qwen reviews here after implementation_
