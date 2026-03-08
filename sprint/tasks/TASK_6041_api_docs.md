# TASK 6041 — Complete API Documentation

**Sprint:** 6 | **Phase:** 11 (Documentation) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Summary

Wrote comprehensive REST + WebSocket API reference covering all endpoints, request/response schemas, TypeScript type definitions, and usage examples.

## Output

`docs/API.md` — covers:

- All REST endpoints: `/`, `/health`, `/api/board`, `/api/tasks`, `/api/tasks/{id}`, `/api/agents`, `/api/agents/{id}`, `/api/health`, `/api/health/alerts/active`, `/api/health/{agent}`
- Full request body tables for `POST /api/tasks` and `PUT /api/tasks/{id}`
- Status validation details (422 on invalid status)
- Both WebSocket endpoints: `/api/ws/board` (real-time board push) and `/api/ws/logs` (agent log streaming)
- JavaScript usage examples for both WebSocket endpoints
- Complete `Task` TypeScript interface with all fields including handoff schema
- Notes on Swagger UI at `/docs` and OpenAPI at `/openapi.json`

## Files Created

- `docs/API.md`
