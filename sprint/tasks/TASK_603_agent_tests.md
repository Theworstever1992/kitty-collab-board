# TASK 603 — Agent Lifecycle Tests

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-06
**Completed:** 2026-03-06
**Phase:** 6 — Testing (Sprint 2)

## Description

Write pytest tests for agent lifecycle: register, heartbeat, deregister.

## Implementation Notes

Created `tests/test_agent.py` with test classes:
- `TestRegistration` — register() tests (2 tests)
- `TestDeregistration` — deregister() tests (1 test)
- `TestHeartbeat` — _heartbeat() tests (1 test)
- `TestGenericAgent` — GenericAgent tests (2 tests)
- `TestErrorHandling` — _mark_blocked() tests (1 test)

**Total: 7 tests**

## Acceptance Criteria

- [x] All lifecycle methods tested
- [x] Error handling verified
- [x] Tests pass consistently

## Review

**Self-Review by Qwen:**

✅ Approved — Full lifecycle coverage.

**Pending:** Claude to review when available

## Dependencies

- Depends on TASK 601 (pytest setup) ✅

## Description

Write pytest tests for agent lifecycle: register, heartbeat, deregister.

## Requirements

- [ ] Test `register()` adds agent to agents.json
- [ ] Test `deregister()` marks offline
- [ ] Test `_heartbeat()` updates last_seen
- [ ] Test agent never crashes on file errors
- [ ] Test GenericAgent initialization

## Acceptance Criteria

- [ ] All lifecycle methods tested
- [ ] Error handling verified
- [ ] Tests pass consistently

## Dependencies

- Depends on TASK 601 (pytest setup)

## Review

_Claude reviews here_
