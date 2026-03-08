# Sprint 4 — Web GUI MVP + Handoff Protocol + Health Alerts

**Goal:** Web-based Mission Control is functional. Agent handoff works. Health monitoring alerts operator.
**Phases:** 7B (Web GUI completion) + 8 (Handoff + Health + Alerts)
**Agents:** Qwen (backend + alerts) + Claude (handoff protocol) + Kimi (frontend - incomplete)

---

## Task Board

### Track B: Web GUI Backend (Qwen) ✅

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 4001 | FastAPI backend setup + REST API | Qwen | ✅ done |
| 4002 | WebSocket real-time board updates | Qwen | ✅ done |
| 4003 | Log streaming endpoint | Qwen | ✅ done |
| 4004 | CORS + security configuration | Qwen | ✅ done |

### Track B: Web GUI Frontend (Kimi → Claude)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 4011 | React + TypeScript scaffold (Vite) | Kimi | ✅ done |
| 4012 | Task board dashboard component | Kimi | ✅ done |
| 4013 | Agent status panel component | Kimi | ✅ done |
| 4014 | WebSocket hook for real-time updates | Kimi | ✅ done |
| 4015 | Task management UI (add/edit/delete) | Kimi | ✅ done |
| 4016 | Log viewer component | Kimi | ✅ done |

*Note: Frontend is functional but needs polish. Claude to review/refine.*

### Phase 8: Handoff Protocol ✅

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 4021 | Handoff protocol design doc | Qwen | ✅ done |
| 4022 | handoff_task() in base_agent.py | Qwen | ✅ done |
| 4023 | accept_handoff() / decline_handoff() | Qwen | ✅ done |
| 4024 | Handoff UI in Mission Control | **Claude** | ✅ done |

### Phase 8: Health Monitoring + Alerts ✅

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 4031 | HealthMonitor class | **Claude** | ✅ done |
| 4032 | Agent heartbeat tracking | **Claude** | ✅ done |
| 4033 | Alert thresholds + notifications | **Claude** | ✅ done |
| 4034 | WebhookSender (Discord/Slack) | **Claude** | ✅ done |
| 4035 | Configurable alert channels | **Claude** | ✅ done |

---

## Rules

- **Claim a task:** Change status to `🔄 in_progress` and put your name in Assigned
- **Complete a task:** Change status to `✅ done`, update task file with implementation notes
- **Review:** Leave review in `sprint/reviews/REVIEW_<id>_<name>.md`
- **Don't duplicate:** Check status before starting
- **Flag blockers:** Change to `🚫 blocked` and note why

---

## Division of Labour

**Qwen** owns:
- Web backend (FastAPI, WebSocket, REST API)
- Log streaming backend
- Handoff implementation
- Health monitoring + alerts
- Webhook integrations

**Kimi** owns:
- Web frontend (React + TypeScript + Vite)
- Dashboard components (task board, agent status)
- Task management UI
- Log viewer component
- Handoff protocol design
- Handoff UI

**Claude** (when available):
- Review completed work
- Native GUI track (if interested)

---

## Dependencies

### Web GUI Track
- ✅ 4012, 4013, 4015 depend on 4011 (need scaffold first)
- ✅ 4014 depends on 4002 (WebSocket backend)
- ✅ 4016 depends on 4003 (log streaming)

### Handoff Track
- 4022, 4023 depend on 4021 (design first)
- 4024 depends on 4022 (need backend implementation)

### Health Track
- 4032 depends on 4031 (HealthMonitor class)
- 4033 depends on 4032 (need heartbeat tracking)
- 4034, 4035 depend on 4033 (need alert system)

---

## Sprint Completion Criteria

- [x] FastAPI backend serves board state via REST + WebSocket
- [x] React frontend displays real-time task board
- [x] Agent status panel shows online/offline/working
- [x] Logs stream live to browser
- [x] Task management works (add, edit, delete, assign)
- [x] Agent handoff protocol implemented and documented
- [x] Handoff UI allows transferring tasks between agents
- [x] HealthMonitor tracks agent heartbeats
- [x] Alerts notify operator when agents go offline
- [x] Webhook integrations work (Discord/Slack)

---

## Quick Start

### Start Backend
```bash
pip install -r requirements.txt
uvicorn web.backend.main:app --reload --port 8000
```

### Start Frontend
```bash
cd web/frontend
npm install
npm run dev
```

Then open http://localhost:3000

---

## Notes

### Web GUI Tech Stack
- **Backend:** FastAPI 0.104+, uvicorn, websockets
- **Frontend:** React 18, TypeScript, Vite, Bootstrap 5, React Icons
- **Dev server:** Run alongside existing TUI
- **Port:** Backend on 8000, Frontend on 3000

### Handoff Protocol
- Task fields: `handed_off_from`, `handed_off_to`, `handed_off_at`, `handoff_notes`
- Status stays `in_progress` during handoff
- Receiving agent can accept or decline
- Both agents log the handoff

### Health Monitoring
- Thresholds:
  - No heartbeat 60s → warning (yellow)
  - No heartbeat 300s → offline (red)
  - Multiple API errors → rate limit warning
- Alert channels: console, log file, webhook

---

*Created: 2026-03-07 | Updated: 2026-03-07 | Follows: SPRINT_2.md (finishing), SPRINT_3.md (partially complete)*
