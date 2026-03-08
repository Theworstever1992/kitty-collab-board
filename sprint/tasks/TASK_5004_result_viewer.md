# TASK 5004 — Task Result Viewer in TUI

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** Sprint 5 — Real-Time & Backend

## Description

Add task selection and result viewing to the curses TUI.

## Implementation Notes

Added to `mission_control.py`:

**Navigation:**
- Up/Down arrow keys navigate task list
- Selected task highlighted with `>` marker and reverse video
- Scroll window keeps selection in view

**Result viewer (`curses_show_result`):**
- Full-screen overlay showing: id, title, status, role, priority, claimed_by, completed_by, completed_at
- Result text word-wrapped to terminal width
- Press any key to return to main loop

**Archive:**
- `A` key triggers `archive_done_tasks()` from TUI
- Result shown in status bar at bottom of screen

**Refresh rate:** reduced from 3s to 1s for more responsive navigation.

## Acceptance Criteria

- [x] Up/Down arrows move selection
- [x] Enter opens full result viewer
- [x] Result text word-wrapped
- [x] Any key returns from viewer to main loop
- [x] A key archives done tasks
