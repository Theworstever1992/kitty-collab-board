# TASK 503 — Fix mission_control.py BOARD_DIR

**Assigned:** Claude
**Status:** done
**Phase:** 5 — Reliability & Hardening

## Description

`mission_control.py` line 14 hardcodes `BOARD_DIR = BOARD_ROOT / "board"` instead of
reading the `CLOWDER_BOARD_DIR` env var. This breaks when running with Docker or custom paths.
`base_agent.py` already does this correctly — mission_control.py should match.

## Fix

```python
import os
BOARD_DIR = Path(os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent / "board"))
```

## Also Fix

- `BOARD_ROOT` variable is used nowhere else — remove it
- While in there: `LOG_DIR` also hardcoded — add `CLOWDER_LOG_DIR` support too

## Acceptance Criteria

- [x] `CLOWDER_BOARD_DIR` env var respected
- [x] `CLOWDER_LOG_DIR` env var respected (for future log display)
- [x] Works identically to before when env vars not set
- [x] `BOARD_ROOT` removed if unused

## Implementation Notes

Replaced lines 14-15 in `mission_control.py`:
- Removed `BOARD_ROOT = Path(__file__).parent` (unused after fix)
- Set `BOARD_DIR = Path(os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent / "board"))`
- Added `LOG_DIR = Path(os.environ.get("CLOWDER_LOG_DIR", Path(__file__).parent / "logs"))`
- `os` was already imported at line 8, no new import needed.
- Behavior is identical to before when neither env var is set.

## Review

_Qwen reviews here_
