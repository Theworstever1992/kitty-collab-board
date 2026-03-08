# TASK 4023 — accept_handoff() / decline_handoff()

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** 8 — Handoff Protocol (Sprint 4)

## Description

Implement accept/decline/cancel/expiry methods in BaseAgent.

## Implementation Notes

Implemented by Qwen in `agents/base_agent.py`:
- `accept_handoff(task_id)` — claims task for self, sets handoff.status = "accepted"
- `decline_handoff(task_id, reason)` — resets task to pending, records decline reason
- `cancel_handoff(task_id)` — source agent cancels pending handoff
- `get_pending_handoffs()` — returns tasks with handoff.to == self.name and status == pending_acceptance
- `check_handoff_expiry()` — marks 10min+ pending handoffs as expired (call periodically)

## Acceptance Criteria

- [x] accept_handoff() transfers task ownership
- [x] decline_handoff() returns task to queue
- [x] cancel_handoff() only works for source agent
- [x] get_pending_handoffs() filters correctly
- [x] check_handoff_expiry() handles 10min timeout
