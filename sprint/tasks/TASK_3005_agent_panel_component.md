# TASK 3005 — Agent Status Panel Component

**Assigned:** Qwen
**Status:** 🔄 in_progress
**Started:** 2026-03-06
**Phase:** 7B — Web-Based GUI

## Description

Create the agent status panel showing which agents are online,
their current task, and last seen timestamp.

## Requirements

- [ ] AgentPanel component in `src/components/AgentPanel.tsx`
- [ ] AgentCard for each agent showing:
  - Name and model
  - Status indicator (🟢 online, 🟡 idle, 🔴 offline)
  - Current task (if working)
  - Last seen timestamp
- [ ] Auto-refresh every 10 seconds
- [ ] Sort by status (online first)

## Acceptance Criteria

- [ ] Shows all registered agents
- [ ] Status updates in real-time
- [ ] Timestamps are human-readable (e.g., "2 min ago")
- [ ] Visual distinction between statuses is clear

## Dependencies

- Depends on TASK 3003 (React scaffold)

## Review

_Claude reviews here_
