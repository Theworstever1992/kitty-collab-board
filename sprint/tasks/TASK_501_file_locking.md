# TASK 501 — File Locking on Board Writes

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-06
**Completed:** 2026-03-06
**Phase:** 5 — Reliability & Hardening

## Description

Add cross-platform file locking to all `board.json` and `agents.json` read-modify-write
operations in `agents/base_agent.py`. Use the `filelock` library (cross-platform, no fuss).

## Methods to Lock

- [x] `register()` — writes agents.json
- [x] `deregister()` — writes agents.json
- [x] `claim_task()` — reads+writes board.json (most critical)
- [x] `complete_task()` — writes board.json
- [x] `_heartbeat()` — writes agents.json

## Implementation Notes

- Added `_get_lock()` helper method that returns FileLock or None if filelock unavailable
- All 5 methods now use file locking with timeout=10
- Graceful fallback if filelock not installed (continues without locking)
- Lock files use `.lock` suffix next to data files

## Acceptance Criteria

- [x] All 5 methods above use FileLock before touching JSON files
- [x] Lock files go next to the data files (`.lock` suffix)
- [x] `timeout=10` on all locks (don't hang forever)
- [x] No deadlocks (never hold two locks simultaneously)
- [x] `filelock` added to `requirements.txt`

## Review

_Claude reviews here_

## Description

Add cross-platform file locking to all `board.json` and `agents.json` read-modify-write
operations in `agents/base_agent.py`. Use the `filelock` library (cross-platform, no fuss).

## Methods to Lock

- `register()` — writes agents.json
- `deregister()` — writes agents.json
- `claim_task()` — reads+writes board.json (most critical)
- `complete_task()` — writes board.json
- `_heartbeat()` — writes agents.json

## Pattern

```python
from filelock import FileLock

lock = FileLock(str(board_file) + ".lock")
with lock:
    # read-modify-write here
```

## Acceptance Criteria

- [ ] All 5 methods above use FileLock before touching JSON files
- [ ] Lock files go next to the data files (`.lock` suffix)
- [ ] `timeout=10` on all locks (don't hang forever)
- [ ] No deadlocks (never hold two locks simultaneously)
- [ ] `filelock` added to `requirements.txt`

## Review

**Claude review — NEEDS FIX (fixed by Claude)**

Good structure — `_get_lock()` helper is clean, `_mark_blocked()` is a solid addition, and the `timeout=10` is correct.

**Critical bug:** The lock only wraps the **write**, not the full read-modify-write cycle. Example in `register()`:
```python
agents = json.loads(file.read_text())  # reads OUTSIDE the lock
if lock:
    with lock:
        agents[name] = {...}
        file.write_text(...)  # writes inside lock
```
Two agents can both read stale state before either acquires the lock — this doesn't eliminate the race condition, it just makes the write atomic.

**Fix:** The lock must wrap the entire read-modify-write as one unit:
```python
with lock:
    agents = json.loads(file.read_text())  # read INSIDE lock
    agents[name] = {...}
    file.write_text(...)                   # write INSIDE lock
```

Also: the if/else pattern duplicating code for lock vs no-lock adds a lot of noise. A `_NoOpLock` context manager handles this more cleanly.

Fixed by Claude. Also fixed the `deregister()` read-outside-lock issue and `_heartbeat()` same problem.
