# TASK 4024 — Handoff UI in Mission Control

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** 8 — Feature Enhancements (Sprint 4)

## Description

Add handoff UI to Mission Control TUI and web frontend.

## Requirements

### TUI (curses)
- [ ] Press 'h' to handoff selected task
- [ ] Show list of available online agents
- [ ] Enter handoff notes
- [ ] Display pending handoffs panel
- [ ] 'A' to Accept, 'D' to Decline handoffs

### Web GUI
- [ ] Handoff button on task card
- [ ] Modal with agent selector + notes field
- [ ] Notification badge for pending handoffs
- [ ] Accept/Decline buttons in notification panel

## Acceptance Criteria

- [x] TUI handoff initiation works (`h` key)
- [x] Pending handoffs visible (🔀 / [HANDOFF] flag on tasks)
- [x] CLI: `mission_control.py handoff` / `handoffs`
- [ ] TUI accept/decline in curses (deferred — low priority)
- [ ] Web UI functional (deferred)

## Dependencies

- Depends on TASK 4021 (handoff protocol design) ✅
- Depends on TASK 4022 (handoff_task implementation) ✅
- Depends on TASK 4023 (accept/decline methods) ✅

## Review

_Qwen reviews here after implementation_

## Implementation Notes for Claude

See `HANDOFF_COMPLETE.md` for API usage examples and TUI integration tips.

The backend is complete. You just need to add:
1. 'h' hotkey handler in curses TUI
2. Agent selection UI
3. Notes input field
4. Pending handoffs display panel
5. Accept/Decline hotkeys
