# TASK 3006 — Log Streaming via WebSocket

**Assigned:** Qwen (took over from Claude)
**Status:** 🔄 in_progress
**Started:** 2026-03-06 (Qwen takeover)
**Phase:** 7B — Web-Based GUI

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Add log streaming to the WebSocket backend so the frontend can display
live agent logs.

## Requirements

- [ ] WebSocket endpoint: `WS /api/ws/logs`
- [ ] Tail log files in `logs/` directory
- [ ] Stream new log entries to connected clients
- [ ] Filter by agent name (optional)
- [ ] Message format: `{ type: "log", agent: "...", entry: "..." }`
- [ ] Buffer last 100 lines for new clients

## Acceptance Criteria

- [ ] Logs stream in real-time (< 1s delay)
- [ ] Multiple agents' logs can be viewed simultaneously
- [ ] Filter by agent works
- [ ] New clients receive recent history

## Dependencies

- Depends on TASK 3001 (FastAPI backend)

## Review

_Qwen reviews here_
