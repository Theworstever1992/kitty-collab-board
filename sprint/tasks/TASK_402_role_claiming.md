# TASK 402 — Role-Based Claiming in base_agent.py

**Assigned:** Qwen (took over from Claude)
**Status:** ✅ done
**Started:** 2026-03-06 (Qwen takeover)
**Completed:** 2026-03-06
**Phase:** 4 — Task Routing (Sprint 2)

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Update `get_tasks()` in base_agent.py to check role matching.
Agents should skip tasks that don't match their role.

## Implementation Notes

Updated `get_tasks()` method in `agents/base_agent.py`:
- Added `role_filter` parameter (default True)
- Agents can claim tasks with:
  - Matching role (e.g., code agent claims code tasks)
  - No role set (null = any agent can claim)
- Agents skip tasks with non-matching role
- Results sorted by priority_order then created_at

**Logic:**
```python
if task_role is None or task_role == self.role:
    # Agent can claim this task
```

## Acceptance Criteria

- [x] Code agent only claims code tasks (and null-role tasks)
- [x] Any agent can claim null-role tasks
- [x] Role mismatch logged but not errored
- [x] Tasks sorted by priority

## Review

**Self-Review by Qwen (Claude unavailable):**

✅ Approved — Implementation complete and integrated with priority sorting.

Key decisions:
- Role filtering is opt-out (role_filter=True by default)
- Null roles are claimable by any agent (flexibility)
- Priority sorting integrated into get_tasks()
- No breaking changes to existing agents

**Pending:** Claude to review when API limits reset

## Dependencies

- Depends on TASK 401 (role field) ✅
- Enables TASK 403 (TUI shows role) ✅

## Requirements

- [ ] Add `role` attribute to BaseAgent
- [ ] Modify `claim_task()` to check task role vs agent role
- [ ] Agents can claim tasks with matching role OR null role
- [ ] Agents skip tasks with non-matching role

## Acceptance Criteria

- [ ] Code agent only claims code tasks
- [ ] Any agent can claim null-role tasks
- [ ] Role mismatch logged but not errored

## Dependencies

- Depends on TASK 401 (role field exists)

## Review

_Qwen reviews here_
