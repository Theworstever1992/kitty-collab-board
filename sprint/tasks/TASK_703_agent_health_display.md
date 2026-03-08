# TASK 703 — Agent Health Display (Running vs Dead)

**Assigned:** Qwen (took over from Claude)
**Status:** 🔄 in_progress
**Started:** 2026-03-06 (Qwen takeover)
**Phase:** 7A — TUI (Sprint 2)

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Improve agent health display in Mission Control to distinguish:
- 🟢 Registered and running (recent heartbeat)
- 🟡 Registered but no recent heartbeat (may be dead)
- 🔴 Offline (deregistered)

## Requirements

- [ ] Check heartbeat age in mission_control.py
- [ ] Thresholds:
  - < 30s: online (green)
  - 30s - 60s: idle (yellow)
  - > 60s: possibly dead (orange)
  - offline: red
- [ ] Display in agent list

## Acceptance Criteria

- [ ] Health states clearly distinguished
- [ ] Thresholds configurable
- [ ] Display updates on refresh

## Review

_Qwen reviews here_
