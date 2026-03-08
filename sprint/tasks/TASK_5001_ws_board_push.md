# TASK 5001 — WebSocket Board File-Watcher (Push on Change)

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** Sprint 5 — Real-Time & Backend

## Description

Board WebSocket previously only sent state on connect. Now pushes to all clients within 500ms of board.json changing.

## Implementation Notes

Added to `web/backend/main.py`:
- `board_watcher()` — asyncio task, polls `board.json` mtime every 500ms
- `startup()` FastAPI event handler starts the watcher as a background task
- `_board_last_mtime` module-level float tracks last seen mtime
- On mtime change: loads board, broadcasts `{"type": "board_update", "data": board}` to all connected clients
- `ConnectionManager.broadcast()` now cleans up dead connections on send failure

No extra dependencies — pure asyncio polling, no watchdog package needed.

## Acceptance Criteria

- [x] Board pushes to clients within ~500ms of file change
- [x] Dead connections cleaned up automatically
- [x] Watcher starts automatically on server startup
- [x] No external dependencies added
