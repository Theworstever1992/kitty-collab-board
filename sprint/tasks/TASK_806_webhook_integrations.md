# TASK 806 — Webhook Integrations (Discord/Slack)

**Assigned:** Qwen
**Status:** 🔄 in_progress
**Started:** 2026-03-06
**Phase:** 8 — Feature Enhancements

## Description

Add webhook integrations to send alerts to Discord or Slack channels.
This extends the health monitoring system (TASK 805).

## Requirements

- [ ] WebhookSender class in `agents/webhooks.py`
- [ ] Support Discord webhooks
- [ ] Support Slack webhooks
- [ ] Configurable via env vars:
  - `CLOWDER_DISCORD_WEBHOOK_URL`
  - `CLOWDER_SLACK_WEBHOOK_URL`
- [ ] Alert types:
  - Agent offline
  - Task blocked
  - Critical task added
  - Rate limit warning
- [ ] Rate limit webhook calls (max 1 per minute)

## Acceptance Criteria

- [ ] Webhooks send successfully
- [ ] Messages are formatted nicely
- [ ] Rate limiting prevents spam
- [ ] Works with health monitor

## Dependencies

- Depends on TASK 805 (health monitoring)

## Review

_Claude reviews here_
