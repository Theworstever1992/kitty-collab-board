# TASK 5003 — Board Archival

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** Sprint 5 — Real-Time & Backend

## Description

Move done tasks to board/archive.json to keep the active board clean.

## Implementation Notes

Added `archive_done_tasks(min_age_minutes=0)` to `mission_control.py`:
- Reads board.json, separates done tasks
- Optional min_age_minutes: only archive tasks completed at least N minutes ago
- Loads existing archive.json (creates if missing), appends with `archived_at` timestamp
- Writes board.json (without archived tasks) and archive.json atomically

**CLI:**
```bash
python mission_control.py archive        # archive all done tasks
```

**TUI (curses):**
- Press `A` to archive done tasks
- Status bar shows count of archived tasks

## Acceptance Criteria

- [x] Done tasks moved to board/archive.json
- [x] archive.json is append-only (previous entries preserved)
- [x] `archived_at` timestamp added to each archived task
- [x] Active board.json cleaned of done tasks
- [x] CLI and TUI both trigger archival
