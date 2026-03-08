# TASK 502 — Error Handling in run()

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-06
**Completed:** 2026-03-06
**Phase:** 5 — Reliability & Hardening

## Description

Wrap `handle_task()` in `agents/base_agent.py:run()` with try/except.
Currently an exception kills the entire agent process and leaves the task stuck in `in_progress`.

## Implementation Notes

- Added try/except around `handle_task()` call in `run()`
- Created `_mark_blocked()` method to mark failed tasks with status `blocked`
- Full traceback logged at DEBUG level using `traceback.format_exc()`
- Agent continues polling after failures - never crashes
- Task gets `blocked_by`, `blocked_at`, `block_reason` fields when failed

## Acceptance Criteria

- [x] Agent loop never dies from `handle_task` exceptions
- [x] Failed tasks show `blocked` status + error reason in board.json
- [x] Agent continues polling after a failure
- [x] Full traceback logged to agent's log file

## Review

_Claude reviews here_

## Description

Wrap `handle_task()` in `agents/base_agent.py:run()` with try/except.
Currently an exception kills the entire agent process and leaves the task stuck in `in_progress`.

## Current Code (base_agent.py ~line 149)

```python
if self.claim_task(task["id"]):
    result = self.handle_task(task)       # <-- no try/except, crashes agent
    self.complete_task(task["id"], result)
```

## Required Behaviour

```python
if self.claim_task(task["id"]):
    try:
        result = self.handle_task(task)
        self.complete_task(task["id"], result)
    except Exception as e:
        self.log(f"Task {task['id']} failed: {e}", "ERROR")
        self._mark_blocked(task["id"], reason=str(e))
```

## Also Add

- `_mark_blocked(task_id, reason)` method — sets status to `blocked`, writes reason to task
- Log the full traceback at DEBUG level (use `traceback.format_exc()`)

## Acceptance Criteria

- [ ] Agent loop never dies from `handle_task` exceptions
- [ ] Failed tasks show `blocked` status + error reason in board.json
- [ ] Agent continues polling after a failure
- [ ] Full traceback logged to agent's log file

## Review

**Claude review — APPROVED**

`run()` now has try/except around `handle_task()` — agent loop survives failures. `_mark_blocked()` correctly writes `blocked` status + reason + timestamp to board.json. Traceback logged at DEBUG level. Agent continues polling after failure. All acceptance criteria met.

Good work on this one.
