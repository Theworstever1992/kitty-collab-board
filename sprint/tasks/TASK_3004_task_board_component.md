# TASK 3004 — Task Board Dashboard Component

**Assigned:** Qwen
**Status:** 🔄 in_progress
**Started:** 2026-03-06
**Phase:** 7B — Web-Based GUI

## Description

Create the main task board dashboard component that displays all tasks
with their status, assignee, and priority.

## Requirements

- [ ] TaskBoard component in `src/components/TaskBoard.tsx`
- [ ] TaskCard component for individual tasks
- [ ] Filter by status (pending, in_progress, done, blocked)
- [ ] Sort by priority and created_at
- [ ] Color coding by status:
  - pending: 🟡 yellow
  - in_progress: 🔵 blue
  - done: 🟢 green
  - blocked: 🔴 red
- [ ] Click to expand task details

## Acceptance Criteria

- [ ] Displays all tasks from API
- [ ] Updates in real-time via WebSocket
- [ ] Filters work correctly
- [ ] Priority sorting works (critical first)
- [ ] Responsive design (works on mobile)

## Dependencies

- Depends on TASK 3003 (React scaffold)

## Review

_Claude reviews here_
