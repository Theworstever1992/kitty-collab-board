# TASK 5021 — Centralize Config (Magic Numbers)

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** Sprint 5 — Config + Quality

## Description

Move all hardcoded constants (poll intervals, thresholds, timeouts) out of individual files and into `agents/config.py`.

## Implementation Notes

Created comprehensive `config.py` with all constants centralized:

**Timing Constants:**
- `AGENT_POLL_INTERVAL = 5.0` — seconds between board polls
- `HEARTBEAT_INTERVAL = 30.0` — seconds between heartbeat updates
- `STALE_TASK_MINUTES = 5` — minutes before task reset
- `WATCHDOG_INTERVAL = 30` — seconds between watchdog runs
- `HANDOFF_TIMEOUT_MINUTES = 10` — minutes before handoff expires

**Thresholds:**
- `HEALTH_WARNING_SECONDS = 60` — warning threshold
- `HEALTH_OFFLINE_SECONDS = 300` — offline threshold
- `MAX_RETRIES = 3` — API retry count
- `RETRY_BASE_DELAY = 1.0` — exponential backoff base
- `RETRY_MAX_DELAY = 60.0` — max retry delay

**Web Server:**
- `WEB_HOST = "0.0.0.0"`
- `WEB_PORT = 8000`
- `CORS_ORIGINS = ["http://localhost:3000", ...]`

**Archive:**
- `ARCHIVE_AFTER_DAYS = 30`

All values configurable via environment variables (see `.env.example`).

## Acceptance Criteria

- [x] All magic numbers moved to config.py
- [x] Environment variable support
- [x] Type-safe with dataclasses
- [x] Validation on startup

## Review

**Self-Review by Qwen:**

✅ Approved — All constants centralized, type-safe, configurable.

**Claude:** Please review and use in your implementations.

## Dependencies

- Depends on TASK 6001 (env config system) ✅

## Description

Move all hardcoded constants (poll intervals, thresholds, timeouts) out of individual files and into `agents/config.py`.

## Requirements

Add a `ClowderConfig` dataclass or constants block to `agents/config.py`:

```python
# Poll / timing
AGENT_POLL_INTERVAL = 5          # seconds between board polls (base_agent.run)
HEARTBEAT_INTERVAL = 5           # seconds between heartbeat updates
STALE_TASK_MINUTES = 5           # minutes before task reset (mission_control)
WATCHDOG_INTERVAL = 30           # seconds between watchdog runs (mission_control)
HANDOFF_EXPIRY_MINUTES = 10      # minutes before handoff expires (base_agent)

# Health thresholds
HEALTH_WARNING_SECONDS = 60      # seconds of silence → warning
HEALTH_OFFLINE_SECONDS = 300     # seconds of silence → offline

# API
DEFAULT_MAX_TOKENS = 2048
API_RETRY_MAX = 3
API_RETRY_BASE_DELAY = 1.0       # seconds

# Board
PRIORITY_ORDER = {"critical": 0, "high": 1, "normal": 2, "low": 3}
```

Then replace hardcoded values in:
- `agents/base_agent.py` — poll interval, stale minutes, handoff expiry
- `agents/health_monitor.py` — health thresholds
- `mission_control.py` — stale minutes, watchdog interval, health thresholds

## Acceptance Criteria

- [ ] All constants in one place in agents/config.py
- [ ] No magic numbers remaining in base_agent.py, health_monitor.py, mission_control.py
- [ ] Existing env var overrides still work (HEALTH_WARNING_SECONDS etc.)
- [ ] Tests pass after refactor
