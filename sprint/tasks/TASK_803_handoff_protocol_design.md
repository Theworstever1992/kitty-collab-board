# TASK 803 — Agent Handoff Protocol Design

**Assigned:** Qwen (took over from Claude)
**Status:** 🔄 in_progress
**Started:** 2026-03-06 (Qwen takeover)
**Phase:** 8 — Feature Enhancements

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Design the agent handoff protocol allowing agents to explicitly transfer
tasks to other agents with context notes.

## Requirements

Document in `docs/HANDOFF_PROTOCOL.md`:
- [ ] Task fields for handoff:
  - `handed_off_from` (agent name)
  - `handed_off_to` (agent name)
  - `handed_off_at` (timestamp)
  - `handoff_notes` (context for receiving agent)
- [ ] Handoff workflow:
  1. Agent A decides to hand off task
  2. Agent A selects target agent B
  3. Agent A adds handoff notes
  4. Task status stays `in_progress`
  5. Agent B receives notification
  6. Agent B accepts task (or declines)
- [ ] Board state transitions
- [ ] Notification mechanism

## Acceptance Criteria

- [ ] Protocol is clear and complete
- [ ] Edge cases covered (agent B offline, task already claimed)
- [ ] Ready for implementation

## Review

_Qwen reviews here_
