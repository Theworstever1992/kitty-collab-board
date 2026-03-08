# TASK 6045 — Troubleshooting Guide

**Sprint:** 6 | **Phase:** 11 (Documentation) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Summary

Wrote a practical troubleshooting guide covering the most common failure modes across all system layers.

## Output

`docs/TROUBLESHOOTING.md` — covers:

- Board issues: tasks stuck in_progress, corrupted board.json, stuck lock files
- Agent issues: not picking up tasks (role/skills mismatch diagnosis), crash-on-startup, repeated blocking, registration failures
- API issues: port conflicts, 503 on /health, CORS, WebSocket updates stopping
- Docker issues: containers exiting, volume mount problems, health check failures
- Frontend issues: stale data, npm install failure, TypeScript build errors
- Diagnostic command reference (board contents, agent registry, error grep, task counts)

## Files Created

- `docs/TROUBLESHOOTING.md`
