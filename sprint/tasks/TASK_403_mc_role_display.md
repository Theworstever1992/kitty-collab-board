# TASK 403 — Mission Control Shows Task Role

**Assigned:** Claude
**Status:** ⬜ todo
**Phase:** 4 — Task Routing
**Depends on:** TASK 401

## Description

Update both the curses TUI and simple print dashboard in `mission_control.py`
to display the task role field alongside status and title.

## Simple dashboard (`print_dashboard`):

```
    ✅ [done       ] Build provider layer                         → claude   [reasoning]
    ⏳ [pending    ] Refactor auth module                         → -        [code]
    ⏳ [pending    ] Summarize meeting notes                      → -        [any]
```

## Curses TUI (`curses_loop`):

Add role column or append `[role]` suffix to existing task line.
Keep within terminal width — truncate title if needed.

## Acceptance Criteria

- [ ] Both print and curses modes show role
- [ ] `None` role displays as `any` or `-`
- [ ] Fits in 80-char terminal without wrapping
- [ ] No crash if role field missing (old tasks)

## Review

_Qwen reviews here_
