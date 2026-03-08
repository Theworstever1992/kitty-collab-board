# TASK 5023 — Tests: health_monitor.py

**Assigned:** Qwen
**Status:** ⬜ todo
**Phase:** Sprint 5 — Config + Quality

## Description

Add a test file `tests/test_health_monitor.py` covering the HealthMonitor and related classes.

## Requirements

Test cases to cover:

### AgentHealth computation
- Agent with recent last_seen → status "online"
- Agent with 90s old last_seen → status "warning"
- Agent with 400s old last_seen → status "offline"
- Agent with no last_seen → status "unknown"
- Agent with malformed last_seen → status "unknown" (no crash)

### Alert firing
- Alert fires on first threshold crossing
- Alert does NOT re-fire on second check at same level (no spam)
- Alert fires upgrade from warning → critical
- Alert clears when agent comes back online

### WebhookSender
- Discord payload has "content" key
- Slack payload has "text" key
- Returns False gracefully when requests not available

### AlertChannels
- Console channel calls print
- Log channel writes to file
- Multiple webhook URLs are all called

## Acceptance Criteria

- [ ] All test cases implemented
- [ ] Tests run with `pytest tests/test_health_monitor.py`
- [ ] No real API calls / no real file writes (use tmp_path fixture)
- [ ] Tests pass in CI
