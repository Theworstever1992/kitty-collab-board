# TASK 4032 — Agent Heartbeat Tracking

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** 8 — Health Monitoring (Sprint 4)

## Description

Track agent heartbeats via last_seen timestamps and detect when agents go silent.

## Implementation Notes

Implemented in `agents/health_monitor.py`:
- `_seconds_since(iso_timestamp)` — computes age of last heartbeat in seconds
- `_compute_status(seconds)`:
  - `< HEALTH_WARNING` → "online"
  - `< HEALTH_OFFLINE` → "warning"
  - `>= HEALTH_OFFLINE` → "offline"
- Thresholds configurable via env vars:
  - `HEALTH_WARNING_SECONDS` (default: 60)
  - `HEALTH_OFFLINE_SECONDS` (default: 300)
- Same thresholds exposed in `mission_control.py` for TUI display

## Acceptance Criteria

- [x] Health computed from agents.json last_seen field
- [x] Warning at 60s, offline at 300s
- [x] Configurable via env vars
- [x] TUI shows health-based colors (green/yellow/red)
