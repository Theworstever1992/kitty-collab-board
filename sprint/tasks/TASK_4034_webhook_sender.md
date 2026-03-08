# TASK 4034 — WebhookSender (Discord/Slack)

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** 8 — Health Monitoring (Sprint 4)

## Description

Send health alerts to Discord or Slack webhooks.

## Implementation Notes

`WebhookSender` class in `agents/health_monitor.py`:
- Auto-detects Discord vs Slack from URL
- Discord: `{"content": "..."}` payload
- Slack/generic: `{"text": "..."}` payload
- Message format: `⚠️/🔴 **Clowder Health Alert** — agent \`name\` is WARNING/CRITICAL`
- Requires `requests` package (optional — degrades gracefully if missing)
- Configurable timeout (default 10s)

## Acceptance Criteria

- [x] Works with Discord webhook URLs
- [x] Works with Slack webhook URLs
- [x] Gracefully skips if requests not installed
- [x] Returns bool success/failure
