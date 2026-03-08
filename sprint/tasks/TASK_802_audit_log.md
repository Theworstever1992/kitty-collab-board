# TASK 802 — Board Audit Log

**Assigned:** Qwen (took over from Claude)
**Status:** 🔄 in_progress
**Started:** 2026-03-06 (Qwen takeover)
**Phase:** 8 — Feature Enhancements (Sprint 2)

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Create an audit log that tracks all board state changes for debugging
and replay.

## Requirements

- [ ] Create `board/audit.json` with entries:
  - timestamp
  - action (created, claimed, completed, blocked, etc.)
  - task_id
  - agent (who did it)
  - old_state (before)
  - new_state (after)
- [ ] Append-only log
- [ ] Rotate/archive old entries (optional)

## Acceptance Criteria

- [ ] All mutations logged
- [ ] Audit file is valid JSON lines
- [ ] Can reconstruct board state from audit

## Review

_Qwen reviews here_
