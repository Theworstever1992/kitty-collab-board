# TASK 6011 — Docker Compose Multi-Service Setup

**Sprint:** 6 | **Phase:** 9 (Deployment) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Summary

Rewrote `docker-compose.yml` to run all system components as separate services with proper health checks, startup ordering, and shared volume mounts.

## Implementation

### Services Added

- **api** — FastAPI backend (`uvicorn web.backend.main:app --host 0.0.0.0 --port 8000`)
  - Health check: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"` every 30s
  - Returns HTTP 200 when board directory is accessible
- **claude-agent** — Anthropic agent container
  - `depends_on: api: condition: service_healthy` — waits for API to pass health check
- **qwen-agent** — Qwen/DashScope agent container
  - Same `depends_on` as claude-agent

### Volumes

- `./board:/app/board` — shared task board mounted into all containers
- `./logs:/app/logs` — shared log directory

### Environment Variables

All containers inherit `CLOWDER_BOARD_DIR` and `CLOWDER_LOG_DIR` from host environment or `.env` file.

## Files Modified

- `docker-compose.yml` — complete rewrite with health checks and service dependencies

## Notes

- Used `urllib.request` (stdlib) for health check to avoid needing `curl` in containers
- K8s manifests (6012) deferred — unnecessary complexity for current scale
- Prometheus monitoring (6015) deferred similarly
