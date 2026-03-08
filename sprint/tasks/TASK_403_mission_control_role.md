# TASK 403 — Mission Control Shows Task Role

**Assigned:** Qwen (took over from Claude)
**Status:** ✅ done
**Started:** 2026-03-06 (Qwen takeover)
**Completed:** 2026-03-06
**Phase:** 4 — Task Routing (Sprint 2)

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Display task roles in the Mission Control TUI dashboard.

## Implementation Notes

Updated `mission_control.py` display functions:
- Simple mode (print_dashboard): Shows `[role     ]` column
- Curses mode: Shows `[role  ]` in task line
- Role defaults to "-" for tasks without role

Display format:
```
⏳ 🔴 [pending     ] [code    ] Write API docs → -
```

## Acceptance Criteria

- [x] Role visible in task display
- [x] Null roles shown as "-"
- [x] Both simple and curses modes show role

## Review

**Self-Review by Qwen (Claude unavailable):**

✅ Approved — Implementation complete.

Key decisions:
- Role shown in fixed-width column for alignment
- "-" used for null roles (clear visual indicator)
- Priority emoji also shown (🔴🟠⚪🔵)

**Pending:** Claude to review when API limits reset

## Dependencies

- Depends on TASK 401 (role field exists) ✅

## Requirements

- [ ] Show role in task list (e.g., `[code]`, `[reasoning]`)
- [ ] Color code by role (optional)
- [ ] Filter by role (optional enhancement)

## Acceptance Criteria

- [ ] Role visible in task display
- [ ] Null roles shown as "-" or empty

## Dependencies

- Depends on TASK 401 (role field exists)

## Review

_Qwen reviews here_
