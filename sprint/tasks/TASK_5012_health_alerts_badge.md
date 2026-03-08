# TASK 5012 — Health Alerts Badge in Frontend Navbar

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** Sprint 5 — Frontend Polish

## Description

Add a health alerts indicator to the frontend navbar that shows alert count and details on click.

## Implementation Notes

Created `web/frontend/src/components/HealthAlerts.tsx`:
- Heart pulse icon (BsHeartPulse) in navbar
- Red badge with alert count when alerts are active
- Click to open popover with alert list (level, agent, reason, timestamp)
- Polls /api/health every 15s
- Semi-transparent when no alerts (visual de-emphasis)

Wired into `App.tsx` navbar with `ms-auto` alignment (right side).

## Acceptance Criteria

- [x] Badge visible in navbar
- [x] Red count badge when alerts active
- [x] Click shows popover with alert details
- [x] Polls automatically every 15s
- [x] Graceful when backend unreachable (no crashes)
