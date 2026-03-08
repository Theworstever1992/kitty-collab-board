# TASK 6014 — Health Check Endpoints

**Sprint:** 6 | **Phase:** 9 (Deployment) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Summary

Added `/health` (Docker/K8s liveness probe) and `/api/health*` (agent health monitoring) endpoints to the FastAPI backend.

## Implementation

### `GET /health` — Infrastructure health check

Returns HTTP 200 when board directory is accessible, HTTP 503 otherwise. Used by Docker Compose health checks and K8s probes.

```python
@app.get("/health")
def health_check():
    board_file = BOARD_DIR / "board.json"
    board_readable = board_file.exists() or BOARD_DIR.exists()
    if not board_readable:
        return Response(content='{"status":"unhealthy",...}', status_code=503, ...)
    return {"status": "healthy", "service": "clowder-api", "board_dir": str(BOARD_DIR), "checked_at": ...}
```

### `/api/health` endpoints (agent health)

Delegates to `agents.health_monitor.HealthMonitor`:

- `GET /api/health` — full health summary (all agents + alert count)
- `GET /api/health/alerts/active` — list of active alerts
- `GET /api/health/{agent_name}` — health for a specific agent

### HealthMonitor singleton

`_health_monitor = HealthMonitor()` instantiated at module level. `HealthMonitor.check_agents()` reads `agents.json`, computes `seconds_since` from `last_seen`, maps to `online/warning/offline` status.

## Files Modified

- `web/backend/main.py` — added `/health`, `/api/health`, `/api/health/alerts/active`, `/api/health/{agent_name}` routes
- `agents/health_monitor.py` — created in Sprint 4/5 (this task wired it into the API)

## Notes

- Two separate health namespaces: `/health` = infra probe, `/api/health` = agent monitoring
- Docker Compose uses `/health` for `service_healthy` condition check
