# TASK 805 — Health Monitoring + Alerting System

**Assigned:** Qwen
**Status:** 🔄 in_progress
**Started:** 2026-03-06
**Phase:** 8 — Feature Enhancements

## Description

Create a health monitoring system that tracks agent status and alerts
the operator when agents go offline or hit rate limits.

## Requirements

- [ ] HealthMonitor class in `agents/health_monitor.py`
- [ ] Track agent heartbeat timestamps
- [ ] Alert thresholds:
  - No heartbeat for 60s → agent may be dead
  - No heartbeat for 300s → agent is offline
  - Multiple API errors in 5 min → rate limit warning
- [ ] Alert channels:
  - Log file alerts
  - Console notifications
  - Optional: webhook (see TASK 806)
- [ ] Configurable thresholds

## Acceptance Criteria

- [ ] Detects missing heartbeats
- [ ] Alerts operator via logs
- [ ] Thresholds are configurable
- [ ] Doesn't spam (alert once per condition)

## Review

_Claude reviews here_
