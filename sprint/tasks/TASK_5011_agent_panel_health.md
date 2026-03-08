# TASK 5011 — AgentPanel: Real Health Status

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** Sprint 5 — Frontend Polish

## Description

AgentPanel previously showed binary online/offline from agents.json status field. Now uses /api/health for 60s/300s threshold-based status.

## Implementation Notes

Rewrote `web/frontend/src/components/AgentPanel.tsx`:
- Calls `fetchHealth()` instead of `fetchAgents()` — gets AgentHealth objects with status, seconds_since
- Health badge: green="online", yellow="warn Ns", red="offline Ns"
- Alert count badge in panel header
- Refreshes on WebSocket board_update events + every 10s fallback
- Shows alert count badge in header if any active alerts

## Acceptance Criteria

- [x] Badge shows "warn 73s" for agents silent 60-300s
- [x] Badge shows "offline 350s" for agents silent 300s+
- [x] Alert count badge in panel header
- [x] Updates when board WebSocket fires
