# TASK 5002 — Real Log Streaming via WebSocket

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** Sprint 5 — Real-Time & Backend

## Description

The /api/ws/logs endpoint was a stub. Now tails actual agent log files and streams new lines to connected clients.

## Implementation Notes

Replaced stub in `web/backend/main.py`:

**Protocol:**
1. Client connects to `ws://localhost:8000/api/ws/logs`
2. Server waits up to 3s for client to send `{"agent": "claude"}` to select log
3. If no agent specified, tails all `*.log` files concurrently
4. Server streams `{"type": "log_line", "agent": "claude", "line": "..."}` for each new line
5. Seeks to end of file on connect (no history dump)

**Implementation:**
- `tail_file(log_file)` — async generator, reads new lines with 250ms sleep on EOF
- `stream_agent(agent)` — wraps tail_file, sends JSON messages
- Multiple agents: `asyncio.gather()` runs concurrent tail tasks
- Error case: sends `{"type": "log_error", "message": "..."}` if file not found

## Acceptance Criteria

- [x] New log lines appear in browser within ~250ms
- [x] Supports single-agent and all-agents modes
- [x] Graceful handling of missing log files
- [x] No history dump on connect (seeks to end)
