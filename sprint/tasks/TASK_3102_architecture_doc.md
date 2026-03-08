# TASK 3102 — Architecture Doc: Shared API Layer

**Assigned:** Qwen (took over from Claude)
**Status:** 🔄 in_progress
**Started:** 2026-03-06 (Qwen takeover)
**Phase:** 7C — Native GUI (Planning)

## Takeover Notice

Originally assigned to Claude. Qwen took over on 2026-03-06 due to Claude's API usage limits.

## Description

Create an architecture document showing how all three UIs (TUI, Web, Native)
share a common backend API layer.

## Topics to Cover

- [ ] API layer abstraction
- [ ] How TUI calls backend (direct Python imports)
- [ ] How Web GUI calls backend (HTTP + WebSocket)
- [ ] How Native GUI would call backend (same as Web or local)
- [ ] Data flow diagrams
- [ ] Deployment options (local vs remote backend)

## Deliverable

Document in `docs/ARCHITECTURE_MULTI_UI.md` with:
- Architecture diagrams
- API interface definitions
- Deployment scenarios

## Acceptance Criteria

- [ ] All three UIs covered
- [ ] Data flow is clear
- [ ] Team can implement any UI against the API layer

## Review

_Qwen reviews here_
