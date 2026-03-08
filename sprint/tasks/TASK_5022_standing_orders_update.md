# TASK 5022 — Update STANDING_ORDERS.md

**Assigned:** Qwen
**Status:** ⬜ todo
**Phase:** Sprint 5 — Config + Quality

## Description

Update STANDING_ORDERS.md to document the handoff protocol and health monitoring behaviour that agents must follow.

## Requirements

Add sections covering:

### Handoff Protocol
- When to initiate a handoff (API limits, context exhaustion, wrong role)
- How to call `handoff_task(task_id, target, notes)` — what notes to include
- Receiving agent responsibility: check `get_pending_handoffs()` in the main loop
- What to include in handoff notes (current progress, blockers, context)
- Decline behaviour: if you can't handle it, decline with a clear reason

### Health Monitoring
- Agents MUST update heartbeat every 5s via `_heartbeat()` (already in base loop)
- Agents that stop heartbeating are flagged warning at 60s, offline at 300s
- Operator gets alerted via configured channels

### General Updates
- Note that board now has an archive (done tasks may be archived, check archive.json)
- Note priority system: agents should respect priority_order field

## Acceptance Criteria

- [ ] Handoff protocol clearly documented with examples
- [ ] Health monitoring section present
- [ ] Archive behaviour mentioned
- [ ] Document is clear enough for a new agent to follow
