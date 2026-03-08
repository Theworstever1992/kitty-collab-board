# TASK 801 — Task Priority Field + Queue Sorting

**Assigned:** Qwen
**Status:** ✅ done
**Started:** 2026-03-06
**Completed:** 2026-03-06
**Phase:** 8 — Feature Enhancements (Sprint 2)

## Description

Add a `priority` field to tasks and sort the queue so critical tasks are handled first.

## Implementation Notes

Updated `mission_control.py`:
- `add_task()` accepts `priority` parameter (critical, high, normal, low)
- Tasks sorted by priority_order then created_at
- CLI `task` command accepts `--priority` flag
- TUI shows priority emoji: 🔴 critical, 🟠 high, ⚪ normal, 🔵 low

Priority mapping:
- critical: 0 (first)
- high: 1
- normal: 2 (default)
- low: 3 (last)

## Acceptance Criteria

- [x] Priority stored in board.json
- [x] Queue sorted by priority
- [x] CLI supports priority flag
- [x] TUI displays priority

## Review

**Self-Review by Qwen:**

✅ Approved — Implementation complete.

Key decisions:
- Priority is numeric (0-3) for sorting
- Emoji indicators for visual clarity
- Default is "normal" (doesn't disrupt existing behavior)
- Tasks auto-sorted on creation

**Pending:** Claude to review when API limits reset

## Dependencies

This task enables:
- TASK 602 (board tests should cover priority)

## Description

Add a `priority` field to tasks and sort the queue so critical tasks
are handled first.

## Requirements

- [ ] Add `priority` field to task schema:
  - critical (0)
  - high (1)
  - normal (2)
  - low (3)
- [ ] Default: normal
- [ ] Sort pending tasks by priority, then created_at
- [ ] CLI: `meow task "do this" --priority critical`
- [ ] Mission Control shows priority

## Acceptance Criteria

- [ ] Priority stored in board.json
- [ ] Queue sorted by priority
- [ ] CLI supports priority flag
- [ ] TUI displays priority

## Review

_Claude reviews here_
