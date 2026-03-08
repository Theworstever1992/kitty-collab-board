# TASK 404 — Stale Task Watchdog

**Assigned:** Claude
**Status:** ⬜ todo
**Phase:** 5 — Reliability (missed in Sprint 1)

## Description

Tasks stuck in `in_progress` (e.g. from a crashed agent) should auto-reset to `pending`
after a configurable timeout (default 5 minutes). Add this as a method in `mission_control.py`
that can be called from the refresh loop.

## Implementation

```python
STALE_TIMEOUT_SECONDS = 300  # 5 minutes

def reset_stale_tasks():
    """Reset in_progress tasks older than STALE_TIMEOUT_SECONDS back to pending."""
    board = load_board()
    now = datetime.datetime.now()
    changed = False
    for task in board.get("tasks", []):
        if task.get("status") == "in_progress":
            claimed_at = task.get("claimed_at")
            if claimed_at:
                age = (now - datetime.datetime.fromisoformat(claimed_at)).total_seconds()
                if age > STALE_TIMEOUT_SECONDS:
                    task["status"] = "pending"
                    task["claimed_by"] = None
                    task["stale_reset_at"] = now.isoformat()
                    changed = True
    if changed:
        save_board(board)
```

Call `reset_stale_tasks()` at the top of each TUI refresh cycle.

## Acceptance Criteria

- [ ] `reset_stale_tasks()` in `mission_control.py`
- [ ] Called on each TUI refresh (both curses and simple loop)
- [ ] Only resets tasks with a `claimed_at` timestamp older than 5 min
- [ ] Adds `stale_reset_at` field to reset tasks for audit trail
- [ ] `save_board()` helper added if not already present (uses filelock)

## Review

_Qwen reviews here_
