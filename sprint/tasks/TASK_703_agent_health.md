# TASK 703 — Agent Health Display

**Assigned:** Claude
**Status:** ⬜ todo
**Phase:** 7A — TUI Enhancements

## Description

The agent list in Mission Control currently shows `status` from `agents.json` — but that status
is just what the agent last wrote. A crashed agent stays "online" forever.

Add real health detection: an agent is considered **alive** if its `last_seen` was within
the last 30 seconds (2x the 5s heartbeat interval with buffer).

## Logic

```python
AGENT_ALIVE_THRESHOLD_SECONDS = 30

def get_agent_health(info: dict) -> str:
    last_seen = info.get("last_seen")
    if not last_seen:
        return "unknown"
    age = (datetime.datetime.now() - datetime.datetime.fromisoformat(last_seen)).total_seconds()
    if age <= AGENT_ALIVE_THRESHOLD_SECONDS:
        return "alive"
    elif age <= 120:
        return "stale"
    return "dead"
```

Display:
- `alive` → green dot (or 🟢)
- `stale` → yellow dot (or 🟡) — heartbeating but slow
- `dead` → red dot (or 🔴) — not seen in 2+ minutes

## Acceptance Criteria

- [ ] `get_agent_health()` function in `mission_control.py`
- [ ] Both print and curses modes use health status (not just `status` field)
- [ ] Health colour shown in curses mode (green/yellow/red colour pairs)
- [ ] No crash if `last_seen` missing or unparseable

## Review

_Qwen reviews here_
