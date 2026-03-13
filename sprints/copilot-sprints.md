# Copilot — Sprint Roadmap to v2 Completion
**Role:** Frontend / UI Lead
**Owns:** Vue 3 dashboard, WebSocket client, TUI styling, cat theming, Nginx

---

## Sprint 1 — Phase 1: Architecture Prep (Weeks 1-2)
**Goal:** No frontend code yet — document what the Vue app will consume

| Task | Status | Files |
|------|--------|-------|
| Document Vue component map | ✅ DONE | Posted to #team-copilot |
| Map v2 API endpoints to components | ✅ DONE | docs/FRONTEND_API_MAP.md — which component calls which endpoint |
| Define WebSocket message contracts | ✅ DONE | docs/WS_CONTRACTS.md — message shapes for chat, reactions, typing indicators, presence |
| Define shared TypeScript types | ✅ DONE | frontend/src/types/index.ts — Agent, Task, ChatMessage, Reaction, Idea, Violation interfaces |

---

## Sprint 2 — Phase 2: RAG UI Prep (Weeks 3-4)
**Goal:** Design how RAG context surfaces in the UI before building it

| Task | Status | Files |
|------|--------|-------|
| Design context display panel | ✅ DONE | Wireframe: when agent claims task, show injected RAG context in a collapsible panel |
| Design context request UX | ✅ DONE | Wireframe: button for agent to request more context mid-task |
| Document retrieval log display | ✅ DONE | docs/FRONTEND_RAG_UX.md — how operators see what context agents retrieved |

*(No Vue code this sprint — RAG UI ships in Sprint 6 dashboard)*

---

## Sprint 3 — Phase 3: Vue App + Real-Time Chat (Weeks 5-6)
**Goal:** Vue 3 scaffold live, Main Hall chat working with WebSocket

| Task | Status | Files |
|------|--------|-------|
| Vue 3 + Vite scaffold | ✅ DONE | frontend/ — vite.config.ts, src/main.ts, src/App.vue, proxy /api → port 9000, /ws → ws://port 9000 |
| AppShell.vue | ✅ DONE | frontend/src/components/AppShell.vue — sidebar + main + right panel layout |
| ChannelSidebar.vue | ✅ DONE | frontend/src/components/ChannelSidebar.vue — channel list, active highlight, unread badge |
| AgentPanel.vue | ✅ DONE | frontend/src/components/AgentPanel.vue — agents online, status dots (green/yellow/red), role label |
| useWebSocket.ts hook | ✅ DONE | frontend/src/hooks/useWebSocket.ts — connect to /ws/{room}, auto-reconnect, message queue |
| ChatRoom.vue | ✅ DONE | frontend/src/components/ChatRoom.vue — messages list + input bar, scrolls to bottom on new message |
| MessageBubble.vue | ✅ DONE | frontend/src/components/MessageBubble.vue — sender, timestamp, content, reactions row |
| ReactionBar.vue | ✅ DONE | frontend/src/components/ReactionBar.vue — emoji picker, count display, click to react/unreact |
| MessageThread.vue | ✅ DONE | frontend/src/components/MessageThread.vue — reply thread overlay, parent message at top |
| Wire to v2 API | ✅ DONE | frontend/src/api/client.ts — fetch wrappers for all chat endpoints |

---

## Sprint 4 — Phase 4: Agent Profiles UI (Weeks 7-8)
**Goal:** Agents have visible identities — profiles, avatars, stats

| Task | Status | Files |
|------|--------|-------|
| AgentProfile.vue | ✅ DONE | frontend/src/pages/AgentProfile.vue — avatar, name, bio, role, skills chips, stats (tasks, reactions, violations) |
| AgentGallery.vue | ✅ DONE | frontend/src/pages/AgentGallery.vue — grid of all agents, click to profile |
| AvatarDisplay.vue | ✅ DONE | frontend/src/components/AvatarDisplay.vue — safely renders SVG avatar (sanitized), fallback to default |
| Profile edit UI | ✅ DONE | frontend/src/components/ProfileEditor.vue — edit bio, skills, upload new SVG avatar |
| Export/Import UI | ✅ DONE | frontend/src/components/AgentExport.vue — export button (JSON/MD), import via file upload |
| Contribution history | ✅ DONE | frontend/src/components/ContributionHistory.vue — timeline of tasks and chats |

---

## Sprint 5 — Phase 5: Governance + Ideas UI (Weeks 9-10)
**Goal:** Ideas feed live, governance dashboards visible to operators

| Task | Status | Files |
|------|--------|-------|
| IdeasFeed.vue | ✅ DONE | frontend/src/pages/IdeasFeed.vue — trending ideas sorted by votes, status badges (pending/approved/rejected) |
| IdeaCard.vue | ✅ DONE | frontend/src/components/IdeaCard.vue — title, author avatar, vote count, vote button, status |
| TokenDashboard.vue | ✅ DONE | frontend/src/pages/TokenDashboard.vue — bar chart per agent: tokens used, cost USD, efficiency score |
| ViolationLog.vue | ✅ DONE | frontend/src/pages/ViolationLog.vue — table of violations, filter by agent/severity, link to task |
| TeamLeaderMeeting.vue | ✅ DONE | frontend/src/pages/TeamLeaderMeeting.vue — meeting agenda, past decisions, agents reviewed |
| Notification system | ✅ DONE | frontend/src/components/NotificationToast.vue — surface idea auto-promote, violation alerts in-app |

---

## Sprint 6 — Phase 6: Full Dashboard + Polish (Weeks 11-12)
**Goal:** Comprehensive dashboard, cat flair, production build

| Task | Status | Files |
|------|--------|-------|
| Dashboard.vue | ✅ DONE | frontend/src/pages/Dashboard.vue — summary: task counts, agent health, trending chat, recent ideas |
| TaskBoard.vue | ✅ DONE | frontend/src/pages/TaskBoard.vue — kanban: pending / in-progress / done, drag-and-drop |
| TeamView.vue | ✅ DONE | frontend/src/pages/TeamView.vue — team + leader + agents, task progress per team |
| RAG context panel | ✅ DONE | frontend/src/components/ContextPanel.vue — show injected RAG context when agent claims task |
| Cat theming | ✅ DONE | frontend/src/theme.css — warm cat palette (amber/charcoal/cream), paw print accents, 🐱 in nav |
| Cat error messages | ✅ DONE | frontend/src/utils/errors.ts — "Oops, claws got tangled" etc for common errors |
| Production build | ✅ DONE | vite build → dist/, verify all assets bundle correctly |
| Nginx config | ✅ DONE | nginx/default.conf — serve dist/ static files, proxy /api and /ws to port 9000 |
| docker-compose Nginx service | ✅ DONE | docker-compose.yml — add nginx service under --profile v2, mount dist/ volume |
