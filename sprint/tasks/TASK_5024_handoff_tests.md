# TASK 5024 — Tests: Handoff Protocol

**Assigned:** Qwen
**Status:** ⬜ todo
**Phase:** Sprint 5 — Config + Quality

## Description

Add test cases for the handoff protocol methods in `BaseAgent` to `tests/test_agent.py` (or a new `tests/test_handoff.py`).

## Requirements

Test cases to cover:

### handoff_task()
- Successful handoff sets task.handoff fields correctly
- handoff_task() fails if task not claimed by this agent
- handoff_task() fails if target agent not in agents.json
- handoff_task() fails if target agent is offline

### accept_handoff()
- Accepting changes claimed_by to accepting agent
- Accepting sets handoff.status to "accepted"
- Accepting fails if handoff is for different agent
- Accepting fails if handoff not in pending_acceptance state

### decline_handoff()
- Declining resets task to pending status
- Declining sets handoff.status to "declined" with reason
- Declining fails if handoff is for different agent

### cancel_handoff()
- Source agent can cancel pending handoff
- cancel fails if called by non-source agent
- cancel fails if handoff already accepted/declined

### get_pending_handoffs()
- Returns only handoffs targeted at this agent
- Returns only pending_acceptance status (not accepted/declined)

### check_handoff_expiry()
- 10+ minute old pending handoff gets marked expired
- Fresh handoff is not expired

## Acceptance Criteria

- [ ] All test cases implemented
- [ ] Tests use tmp_path fixture for isolated board files
- [ ] Tests pass with `pytest`
- [ ] Edge cases tested (missing tasks, wrong agent, bad state)
