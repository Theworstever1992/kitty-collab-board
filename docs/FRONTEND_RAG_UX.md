# RAG UX Design — Clowder v2

**Sprint:** S2 — Phase 2 prep
**Owner:** Copilot
**Status:** Design complete — implementation deferred to Sprint 6 (Dashboard)

Defines how RAG context surfaces in the Vue 3 frontend: what agents and operators see,
when they see it, and how they interact with it. No Vue code this sprint — this feeds
Sprint 6's `ContextPanel.vue` and `RetrievalLog.vue`.

---

## Background

When a v2 agent claims a task, the backend automatically runs a semantic search
(`POST /api/rag/search`) and injects matching `ContextItem[]` into the agent's system
prompt before execution. The frontend's job is to make this invisible process visible —
so operators can understand what the agent knew, and agents (when running with a UI)
can request more.

RAG data model (from `frontend/src/types/index.ts`):
```typescript
ContextItem {
  id, source_type, source_id, content, tags,
  similarity_score,  // 0–1
  created_at
}
// source_type: 'task_result' | 'chat_message' | 'decision' | 'code_pattern' | 'standard'
```

---

## 1. Context Panel — Task Claim View

**When:** Operator opens a task card. If the task has been claimed, a context panel
appears showing what the agent received at claim time.

**Placement:** Right sidebar of `TaskBoard.vue`, slides in when a task is selected.
On mobile / narrow screens: bottom sheet.

### Wireframe

```
┌─────────────────────────────────────────────────────────┐
│  📋 Task: Implement JWT refresh endpoint                │
│  Claimed by: claude · 2 min ago                        │
├─────────────────────────────────────────────────────────┤
│  🧠 Context injected at claim  [▼ 3 items]             │  ← collapsible header
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ task_result ──────────────────────── score: 0.91 ─┐ │
│  │ "Implemented OAuth flow in S1. Used                │ │
│  │  python-jose for JWT, 15min expiry,                │ │
│  │  refresh in httpOnly cookie..."                    │ │
│  │ 🏷 jwt  auth  backend   · claude · 3 days ago      │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ decision ─────────────────────────── score: 0.87 ─┐ │
│  │ "Team agreed: no session storage.                  │ │
│  │  All auth state in signed JWT only."               │ │
│  │ 🏷 auth  decision   · war-room · 5 days ago         │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ standard ─────────────────────────── score: 0.82 ─┐ │
│  │ "Auth endpoints must return 401 (not               │ │
│  │  403) for unauthenticated requests."               │ │
│  │ 🏷 auth  standards   · gemini · 1 week ago          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  [ + Request more context ]                            │  ← mid-task action
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Behaviour

- **Collapsed by default** when task panel opens — one click to expand. Respects operator's choice (localStorage per task).
- **Score colour coding:**
  - ≥ 0.85 → green badge (highly relevant)
  - 0.70–0.84 → amber badge (related)
  - < 0.70 → grey badge (tangential — shown last, dimmed)
- **Source type icons:**
  - `task_result` → 📋
  - `chat_message` → 💬
  - `decision` → ⚖️
  - `code_pattern` → 🔷
  - `standard` → 📏
- **Click item** → opens source (task, message, or war-room thread) in a modal.
- **If no context injected** → panel shows: *"No relevant context found for this task."* (not hidden — operators need to know RAG fired and found nothing).
- **Pending task (not yet claimed)** → panel not shown. Context is generated at claim time, not before.

### API calls
```
GET /api/rag/retrieval-log?task_id={id}   → RetrievalLog (includes ContextItem[])
```
If retrieval log not yet available (task just claimed): show loading skeleton, poll once after 2s.

---

## 2. Mid-Task Context Request

**When:** Agent is working on a task and needs more context. Operator or agent (via
tool call) can trigger an additional RAG search with a refined query.

**Placement:** `[ + Request more context ]` button at bottom of context panel.
Only visible when task status is `claimed`.

### Wireframe — Request Modal

```
┌─────────────────────────────────────────────────────────┐
│  🔍 Request additional context                   [✕]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  What does the agent need to know more about?          │
│  ┌───────────────────────────────────────────────────┐  │
│  │ e.g. "error handling patterns for auth failures"  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  Retrieve top:  [ 3 ▾ ]   (max 10)                    │
│                                                         │
│  Scope:  ☑ task results   ☑ decisions   ☑ standards   │
│          ☑ chat messages  ☑ code patterns              │
│                                                         │
│              [ Cancel ]  [ Search & Inject → ]        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### After submission

1. `POST /api/rag/search` fires with the refined query + scope filters.
2. Results append to the context panel under a new section header:
   **"Manually requested · [timestamp]"** — visually distinct from auto-injected.
3. Results are also posted to the agent's team channel as a `[chat]` message so
   the agent sees the context in its next message loop:
   ```
   📎 Additional context injected for task {id}: "{query}"
   — {top_k} items retrieved, scores: 0.93, 0.88, 0.81
   ```
4. The modal closes. The task panel stays open.

### API calls
```
POST /api/rag/search   { query, top_k, source_types? }  → ContextItem[]
POST /api/channels/{team-channel}/messages              → notify agent
```

---

## 3. Retrieval Log — Operator View

**When:** Operator wants to audit what context every agent received across all tasks
over a time period. Accessed from the main Dashboard or via `ViolationLog` for
agents flagged for poor context usage.

**Placement:** Standalone page `RetrievalLog.vue` — accessible from the Dashboard
sidebar under "Insights" → "Context Audit".

### Wireframe

```
┌─────────────────────────────────────────────────────────┐
│  📊 Context Retrieval Log                              │
│                                                         │
│  Agent: [ All ▾ ]   Period: [ Last 7 days ▾ ]          │
│  Source type: [ All ▾ ]        [ Export CSV ]          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Agent    Task                    Query        Items  Time│
│  ──────  ─────────────────────── ──────────── ─────  ────│
│  claude  Implement JWT refresh   "JWT auth…"    3    2m   │
│  qwen    Expand models.py        "schema …"     5    5m   │
│  gemini  Write conftest          "async test…"  2    8m   │
│  claude  BaseLeader class        "leader pat…"  4    1h   │
│                                                         │
│  [ ← 1  2  3 … → ]                  Showing 1–20 of 47 │
├─────────────────────────────────────────────────────────┤
│  Click any row to expand:                               │
│                                                         │
│  ▼ claude — "Implement JWT refresh" — 3 items injected  │
│    ├─ task_result  "OAuth flow from S1…"   score: 0.91  │
│    ├─ decision     "No session storage…"   score: 0.87  │
│    └─ standard     "401 not 403…"          score: 0.82  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Behaviour

- **Row expand:** Click row → reveals `ContextItem[]` for that retrieval, same card style as the task context panel.
- **Filter by source type:** Useful for auditing if agents are getting too much chat noise vs. structured decisions.
- **Export CSV:** Dumps `agent, task_id, query, source_type, content_preview, similarity_score, timestamp` — for offline analysis.
- **Zero-result rows highlighted in amber** — indicates the RAG search fired but found nothing. Useful for diagnosing agents working "cold" (no relevant history yet).
- **Pagination:** 20 rows per page. No infinite scroll — operators need stable page references when citing audit rows.

### API calls
```
GET /api/rag/retrieval-log?agent={name}&period=7d&source_type={type}
→ RetrievalLog[]
```

---

## 4. Agent Panel — RAG Activity Indicator

**When:** An agent is actively retrieving context (or has recently). Visible in the
`AgentPanel.vue` right sidebar next to the agent's status dot.

### Wireframe (inline with agent row)

```
● claude     developer    🧠 retrieving…    team-claude
● qwen       collaborator ✓ 5 items         team-qwen
● gemini     developer                      team-gemini
● copilot    developer                      —
```

- **`🧠 retrieving…`** — animated, shown for ≤3s while search is in flight (WS event: `rag_searching`)
- **`✓ N items`** — shown for 10s after retrieval completes, then fades (WS event: `rag_complete`)
- Implemented via two new WS server→client events (add to `WS_CONTRACTS.md` in Sprint 3):

```json
{ "type": "rag_searching", "agent": "claude", "task_id": "abc123" }
{ "type": "rag_complete",  "agent": "claude", "task_id": "abc123", "items_found": 5 }
```

---

## 5. Empty States & Edge Cases

| Scenario | UI behaviour |
|----------|-------------|
| Task claimed, retrieval log not yet available | Skeleton loader in panel, auto-refresh after 2s |
| RAG search returns 0 results | Panel shows: "No relevant context found" with amber border — not hidden |
| All items score < 0.60 | Show items but add banner: "Low-confidence context — verify manually" |
| Mid-task request returns duplicates | Deduplicate by `ContextItem.id` client-side before rendering |
| Agent offline when context injected | Log still shows in retrieval log; `AgentPanel` indicator doesn't fire |
| Phase 1 (RAG stub) | `/api/rag/search` returns `[]`. Context panel renders "No context available yet (Phase 1)" — component exists, just empty |

---

## 6. Phase Dependencies

| Component | Needs from backend | Available in |
|-----------|--------------------|-------------|
| Context Panel (read) | `GET /api/rag/retrieval-log` | Phase 2 |
| Mid-task request | `POST /api/rag/search` (real, not stub) | Phase 2 |
| Agent Panel indicator | WS `rag_searching` / `rag_complete` events | Phase 3 |
| Retrieval Log page | `GET /api/rag/retrieval-log` with filters | Phase 2 |
| CSV export | Same endpoint + client-side CSV serialiser | Phase 6 |

The Vue components themselves ship in **Sprint 6** alongside the full dashboard.
This document gives Claude/Qwen the API contracts they need to design the
retrieval log endpoint correctly in Phase 2.

---

## 7. Notes for Backend Team (@claude @qwen)

1. **`GET /api/rag/retrieval-log`** needs to be a first-class endpoint in Phase 2 — not a debug endpoint. It's operator-facing. Needs filters: `agent`, `period`, `source_type`, pagination (`limit`, `offset`).
2. **`RetrievalLog` rows should store the full `ContextItem[]` results**, not just IDs. Operators need to see the content without re-fetching each item. A JSON column is fine.
3. **`rag_searching` / `rag_complete` WS events** are new — add them to the Phase 3 WS server. The payload needs `agent` and `task_id` at minimum.
4. **Similarity score must be returned in the API response.** The current `ContextItem` type has `similarity_score?: number` — make it non-optional in the retrieval log response.
5. **Source deduplication:** If the same context item is injected via auto-retrieval AND a manual request, deduplicate by `ContextItem.id` in the API response, not client-side.
