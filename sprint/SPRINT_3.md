# Sprint 3 — Web GUI Foundation + Native GUI Planning + Handoff Protocol

**Goal:** Web-based Mission Control MVP. Native GUI architecture planned. Agent handoff works. Health alerts notify operator.
**Phases:** 7B (Web GUI) + 7C (Native GUI Plan) + 8 (Handoff + Alerts)
**Agents:** Claude (web backend, native GUI research, handoff protocol) + Qwen (web frontend, health alerts, integration)

---

## Task Board

### Track B: Web-Based GUI

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 3001 | FastAPI backend setup + REST API | **Kimi** | ✅ done |
| 3002 | WebSocket real-time board updates | **Kimi** | ✅ done |
| 3003 | React + TypeScript frontend scaffold | Qwen | 🔄 in_progress |
| 3004 | Task board dashboard component | Qwen | 🔄 in_progress |
| 3005 | Agent status panel component | Qwen | 🔄 in_progress |
| 3006 | Log streaming via WebSocket | **Qwen** | 🔄 in_progress |
| 3007 | Task management (add/edit/delete) UI | Qwen | 🔄 in_progress |

### Track C: Native GUI (Planning)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 3101 | Research: Tauri vs Electron for Clowder | **Qwen** | 🔄 in_progress |
| 3102 | Architecture doc: shared API layer | **Qwen** | 🔄 in_progress |
| 3103 | System tray + notifications design | **Qwen** | 🔄 in_progress |
| 3104 | Offline-first strategy doc | Qwen | 🔄 in_progress |

### Phase 8: Feature Enhancements

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 803 | Agent handoff protocol design | **Qwen** | 🔄 in_progress |
| 804 | Handoff implementation in base_agent.py | **Qwen** | 🔄 in_progress |
| 805 | Health monitoring + alerting system | Qwen | 🔄 in_progress |
| 806 | Webhook integrations (Discord/Slack) | Qwen | 🔄 in_progress |

---

## Rules

- **Claim a task:** Change status to `🔄 in_progress` and put your name in Assigned
- **Complete a task:** Change status to `✅ done`, update the task file with what you did
- **Review:** Leave a review comment in the task file's Review section after reading the other agent's work
- **Don't duplicate:** Check status before starting. If it's `🔄`, leave it alone.
- **Flag blockers:** Change status to `🚫 blocked` and note why in the task file

---

## Division of Labour

**⚠️ TAKEOVER NOTICE:** Claude unavailable due to API limits (2026-03-06). Qwen has taken over all Claude's tasks.

**Qwen** owns: ALL tasks (original + Claude's takeover)
- Offline-first strategy
- Health monitoring + alerting
- Webhook integrations

---

## Dependencies

### Web GUI Track
- 3002 depends on 3001 (WebSocket needs FastAPI setup)
- 3004, 3005, 3007 depend on 3003 (need frontend scaffold)
- 3006 depends on 3002 (log streaming needs WebSocket)

### Native GUI Track
- 3102 depends on 3101 (architecture follows tech choice)
- 3103, 3104 can be done in parallel with 3102

### Feature Track
- 804 depends on 803 (implement after design)
- 806 depends on 805 (webhooks are one alert channel)

---

## Sprint Completion Criteria

- [ ] FastAPI backend serves board state via REST + WebSocket
- [ ] React frontend displays real-time task board and agent status
- [ ] Logs stream live to browser via WebSocket
- [ ] Task management works from web UI (add, edit, delete, assign)
- [ ] Native GUI tech decision documented (Tauri or Electron)
- [ ] Architecture doc shows how all 3 UIs share backend API
- [ ] Agent handoff protocol implemented — agents can transfer tasks
- [ ] Health alerts notify operator when agents go offline
- [ ] Optional: Webhook alerts to Discord/Slack

---

## Notes

### Web GUI Tech Stack
- **Backend:** FastAPI, uvicorn, websockets
- **Frontend:** React 18, TypeScript, Bootstrap 5
- **Build:** Vite or Create React Agent
- **Dev server:** Run alongside existing TUI

### Native GUI Considerations
- **Tauri:** Smaller bundle, Rust backend, better performance
- **Electron:** Larger bundle, JS backend, easier for web devs
- **Decision factors:** Team skills, bundle size, system requirements

### Handoff Protocol
- Task field: `handed_off_from`, `handed_off_to`, `handoff_notes`
- Status stays `in_progress` during handoff
- Both agents log the handoff

---

*Created: 2026-03-06 | Follows: SPRINT_1.md, SPRINT_2.md*
