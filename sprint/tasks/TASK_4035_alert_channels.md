# TASK 4035 — Configurable Alert Channels

**Assigned:** Claude
**Status:** ✅ done
**Started:** 2026-03-07
**Completed:** 2026-03-07
**Phase:** 8 — Health Monitoring (Sprint 4)

## Description

Allow operators to configure which alert channels are active.

## Implementation Notes

`AlertChannels` class in `agents/health_monitor.py`:
```python
# Default: console + log
channels = AlertChannels()

# Console only
channels = AlertChannels(channels=["console"])

# All channels with webhooks
channels = AlertChannels(
    channels=["console", "log", "webhook"],
    webhook_urls=["https://discord.com/api/webhooks/...", "https://hooks.slack.com/..."]
)

monitor = HealthMonitor(channels=channels)
```

Available channels:
- `"console"` — print to stdout
- `"log"` — append to `logs/health_monitor.log`
- `"webhook"` — POST to each URL in `webhook_urls`

## Acceptance Criteria

- [x] Default works with no configuration
- [x] Channels list controls which outputs are active
- [x] Multiple webhook URLs supported
- [x] Clean API for programmatic use
