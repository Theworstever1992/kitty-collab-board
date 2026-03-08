# TASK 702 — Board Archival (done → archive.json)

**Assigned:** Qwen (took over from Claude)
**Status:** 🔄 in_progress
**Started:** 2026-03-06 (Qwen takeover)
**Phase:** 7A — TUI (Sprint 2)

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Move completed tasks to `board/archive.json` after N days to keep
the main board.json manageable.

## Requirements

- [ ] Configurable archive threshold (default: 7 days)
- [ ] Nightly archival process
- [ ] Move done tasks older than threshold
- [ ] Preserve all task data in archive
- [ ] CLI command: `meow archive` to manual trigger

## Acceptance Criteria

- [ ] Old done tasks archived automatically
- [ ] Archive file is valid JSON
- [ ] Main board stays small

## Review

_Qwen reviews here_
