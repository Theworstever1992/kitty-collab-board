# Claude — Sprint Roadmap to v2 Completion
**Role:** Developer / Manager / Backend Lead
**Owns:** API server, PM Agent, RAG service, governance agents, TUI, deployment

---

## Sprint 1 — Phase 1: Core Infrastructure (Weeks 1-2)
**Goal:** Working v2 API with hybrid board and PM Agent

| Task | Status | Files |
|------|--------|-------|
| Docker + Postgres (pgvector) | ✅ DONE | docker-compose.yml |
| Requirements + Dockerfile | ✅ DONE | requirements.txt, Dockerfile |
| Complete REST endpoints | ✅ DONE | backend/main.py — POST/GET /api/v2/teams, POST/GET /api/v2/chat/{room}, POST /api/v2/agents/{name}/heartbeat, POST /api/v2/rag/search stub |
| PM Agent skeleton | ✅ DONE | agents/pm_agent.py — supervised mode, polls pm_tasks.json, proposes via war_room |
| BaseLeader class | ✅ DONE | agents/base_leader.py — claim_task, complete_task, spawn_agent, send_feedback, run loop |
| AgentClient v2 routing | ✅ DONE | agents/agent_client.py — update endpoint paths to match v2 API |

---

## Sprint 2 — Phase 2: RAG Integration (Weeks 3-4)
**Goal:** Agents get context-augmented prompts automatically

| Task | Status | Files |
|------|--------|-------|
| EmbeddingService singleton | ✅ DONE | backend/embeddings.py — load all-MiniLM-L6-v2 once at lifespan, shared across handlers |
| RAG endpoint | ✅ DONE | backend/api/rag.py — POST /api/v2/rag/search wired through rag_service.query_context |
| Auto-inject context into task prompts | ✅ DONE | backend/api/tasks.py — on claim, retrieve context, prepend to task description |
| Mid-task retrieval API | ✅ DONE | backend/api/context.py — POST /api/v2/context/query (agent requests more context mid-run) |
| Seed context on task completion | ✅ DONE | backend/api/tasks.py — on complete, embed result and store as context_item |

---

## Sprint 3 — Phase 3: Social WebSocket (Weeks 5-6)
**Goal:** Real-time chat with rooms, fully replacing the v1 WebSocket

| Task | Status | Files |
|------|--------|-------|
| WebSocket server (room-based) | ✅ DONE | backend/ws.py — ConnectionManager with per-room subscribers, broadcast, disconnect cleanup |
| Mount on FastAPI | ✅ DONE | backend/main.py — @app.websocket("/ws/{room}") |
| Reconnect + missed messages | ✅ DONE | On connect, send last 50 messages from DB for that room |
| Message persistence | ✅ DONE | Every ws message written to chat_messages table |
| Trending score updater | ✅ DONE | backend/api/trending.py — score = reactions + (replies * 1.5), decay after 48h |
| Ideas auto-surface trigger | ✅ DONE | POST /api/v2/trending/update triggers maybe_surface_idea() for scores >= threshold |

---

## Sprint 4 — Phase 4: Profiles & Portability (Weeks 7-8)
**Goal:** Agents have persistent identities, exportable to other projects

| Task | Status | Files |
|------|--------|-------|
| Avatar SVG validation | ✅ DONE | backend/api/agents.py — validate_avatar_svg(): size gate → xml.etree.ElementTree parse → root tag check |
| Agent export endpoint | ✅ DONE | backend/api/exports.py — GET /api/v2/agents/{name}/export?format=json|md |
| Agent import endpoint | ✅ DONE | backend/api/exports.py — POST /api/v2/agents/import — upsert: update if exists, create if new |
| Onboarding flow | ✅ DONE | agents/onboarding.py — pick_default_avatar() + onboard_agent() async flow |
| Default avatars | ✅ DONE | backend/assets/avatars/ — tabby.svg, tuxedo.svg, calico.svg (ship 3 defaults) |

---

## Sprint 5 — Phase 5: Governance (Weeks 9-10)
**Goal:** Token Manager and Standards agents running, ideas flow complete

| Task | Status | Files |
|------|--------|-------|
| Token Manager agent | ✅ DONE | agents/token_manager_agent.py — persistent process, reads token_usage_log, posts weekly report to #manager |
| Standards agent | ✅ DONE | agents/standards_manager_agent.py — scans completed tasks for violations, posts to standards_violations table |
| Governance API | ✅ DONE | backend/api/governance.py — GET /violations, GET /token-report, POST /violations |
| Ideas approval endpoint | ✅ DONE | backend/api/ideas.py — PATCH /api/v2/ideas/{id}/approve (PM or leader only) |

---

## Sprint 6 — Phase 6: Polish & Deployment (Weeks 11-12)
**Goal:** Production-ready, documented, fully containerized

| Task | Status | Files |
|------|--------|-------|
| Restore TUI (mission_control.py) | ✅ DONE | mission_control.py — rewrite with v2 API backend (was deleted), include chat + profiles + ideas |
| Production Dockerfile | ✅ DONE | Dockerfile — multi-stage, non-root user, no --reload |
| Production docker-compose | ✅ DONE | docker-compose.yml — add Nginx service for Vue dist/, production env vars |
| API documentation | ✅ DONE | docs/API_REFERENCE.md — all v2 endpoints documented |
| Deployment guide | ✅ DONE | docs/DEPLOYMENT.md — setup, env vars, first-run steps |
| Architecture doc | ✅ DONE | docs/ARCHITECTURE.md — system diagram, data flow, agent hierarchy |
