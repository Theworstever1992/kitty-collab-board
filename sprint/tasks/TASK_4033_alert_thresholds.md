# TASK 4033 — Alert Thresholds + Notifications

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** 8 — Health Monitoring (Sprint 4)

## Description

Fire alerts when agent health crosses thresholds. Support multiple alert channels.

## Implementation Notes

`AlertChannels` class in `agents/health_monitor.py`:
- Channels: `"console"` (print), `"log"` (logs/health_monitor.log), `"webhook"`
- `fire(alert)` dispatches to all configured channels
- State tracking in `HealthMonitor._active_alerts` — only fires when status changes (no spam)
- Alert levels: `"warning"` (60s silence), `"critical"` (300s silence)
- Recovery: alert cleared when agent comes back online

## Acceptance Criteria

- [x] Alerts fire on first threshold crossing (not on every check)
- [x] Alert cleared when agent recovers
- [x] Console and log channels work without extra dependencies
- [x] Webhook channel requires `requests` (optional)
