# TASK 4031 — HealthMonitor Class

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** 8 — Health Monitoring (Sprint 4)

## Description

Create `agents/health_monitor.py` with a `HealthMonitor` class that checks agent heartbeats and reports their health status.

## Implementation Notes

Created `agents/health_monitor.py` containing:
- `AgentHealth` dataclass — name, status, last_seen, seconds_since, model, role
- `Alert` dataclass — agent, level, reason, timestamp
- `HealthMonitor` class with:
  - `check_agents()` → list of AgentHealth
  - `get_alerts()` → active alerts
  - `get_summary()` → dict for API responses
  - `start(interval)` / `stop()` — background thread mode
  - `_compute_status(seconds)` → "online" | "warning" | "offline" | "unknown"

## Acceptance Criteria

- [x] Reads agents.json and computes status from last_seen
- [x] Returns structured AgentHealth objects
- [x] Works standalone and as background thread
- [x] Respects HEALTH_WARNING_SECONDS / HEALTH_OFFLINE_SECONDS env vars
