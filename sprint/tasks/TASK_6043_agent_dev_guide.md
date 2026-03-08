# TASK 6043 — Agent Developer Guide

**Sprint:** 6 | **Phase:** 11 (Documentation) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Summary

Wrote a developer guide for creating new agents, documenting the full BaseAgent API surface.

## Output

`docs/AGENT_DEVELOPER_GUIDE.md` — covers:

- Minimal working agent example (15-line subclass)
- BaseAgent `__init__` parameter reference
- `handle_task()` contract (return string, raise for blocked)
- `run()` main loop walkthrough
- `log()`, `get_tasks()`, `claim_task()`, `complete_task()` reference
- Environment variable reference (`CLOWDER_BOARD_DIR`, `CLOWDER_LOG_DIR`)
- Role vs skills design guidance
- File locking explanation (filelock dependency, no-op fallback)
- Full handoff protocol for agents (all 6 methods with examples)
- Custom `run()` override pattern for handoff checking
- Docker `docker-compose.yml` service entry template
- Provider layer reference
- Audit logging (automatic, no subclass code needed)
- Testing agent against isolated board
- Naming conventions

## Files Created

- `docs/AGENT_DEVELOPER_GUIDE.md`
