# TASK 801 — Task Priority Field + Queue Sorting

**Assigned:** Qwen
**Status:** ⬜ todo
**Phase:** 8.1 — Feature Enhancements

## Description

Add `priority` field to tasks (critical/high/normal/low). Agents claim highest-priority
pending tasks first instead of FIFO. Mission Control shows priority.

## Priority Order

`critical` > `high` > `normal` > `low`

## Changes

**`mission_control.py` — `add_task()`:**
```python
def add_task(title, description="", prompt="", role=None, priority="normal"):
    task = {
        ...,
        "priority": priority,  # critical | high | normal | low
    }
```

**`agents/base_agent.py` — `get_tasks()`:**
```python
PRIORITY_ORDER = {"critical": 0, "high": 1, "normal": 2, "low": 3}

def get_tasks(self) -> list:
    ...
    return sorted(
        [t for t in pending if role_matches(t)],
        key=lambda t: PRIORITY_ORDER.get(t.get("priority", "normal"), 2)
    )
```

**`meow.py`:**
```
meow task "urgent fix" --role code --priority critical
```

**`mission_control.py` — `cli_add_task()`:**
Add priority prompt with default `normal`.

## Acceptance Criteria

- [ ] `priority` field in `add_task()` (default "normal")
- [ ] `get_tasks()` sorts by priority before returning
- [ ] `meow task` supports `--priority` flag
- [ ] Interactive add prompts for priority
- [ ] Mission Control displays priority (emoji or bracket prefix works)
- [ ] Old tasks without priority field treated as "normal"

## Review

_Claude reviews here_
