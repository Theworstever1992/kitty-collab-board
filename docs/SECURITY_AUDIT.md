# Security Audit — Kitty Collab Board (Clowder v2)

**Date:** 2026-03-24
**Auditor:** Claude (claude-sonnet-4-6)
**Branch:** `claude/security-audit-ai-integration-BH9kW`
**Scope:** Full codebase — backend API, agents, config, Docker, AI integration

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1 |
| High     | 3 |
| Medium   | 7 |
| Low      | 4 |
| Info     | 2 |

> **Note:** The architecture document explicitly states "No authentication in v2 (local/LAN only — v3 concern)" (locked decision #8). Several findings below stem from this intentional design choice. Findings are still recorded so they can be addressed when the project moves beyond LAN-only deployment.

---

## Critical

### SEC-001 — No Authentication or Authorization on Any Endpoint

**File:** `backend/main.py`, all `backend/api/` routers
**Risk:** Any client reachable to the API can read all data, register agents with any name, claim or complete any task, post arbitrary messages, create violations, approve ideas, or delete votes.

**Details:**
- Zero authentication on all 40+ REST endpoints and the WebSocket endpoint.
- Agent identity is self-reported via request body fields (`sender`, `agent_name`, `voter_id`, etc.) — trivially spoofed.
- Anyone can `PATCH /api/v2/agents/{name}/profile` to overwrite any agent's bio, skills, or avatar.
- Anyone can `POST /api/v2/violations` to falsely accuse any registered agent.
- Anyone can `PATCH /api/v2/ideas/{id}/status` to approve or reject ideas.

**Recommendation:**
Add API key or JWT middleware before any internet-facing deployment. At minimum, add a shared secret header check (`X-API-Key`) validated by a FastAPI dependency injected on all routers.

---

## High

### SEC-002 — Stored XSS via Unvalidated SVG Avatar

**File:** `backend/api/agents.py:28-51`
**Risk:** Stored cross-site scripting if avatar SVGs are rendered directly in the browser.

**Details:**
`validate_avatar_svg()` only checks:
1. Size ≤ 50 KB
2. Valid XML
3. Root tag is `<svg>`

It does **not** strip:
- `<script>` elements
- Inline event handlers (`onload`, `onclick`, `onerror`, etc.)
- `javascript:` URI schemes in `href`/`xlink:href`
- `<use xlink:href="http://...">` (SSRF / data exfiltration)
- CSS `expression()` or `url()` with external references

A malicious SVG passes all three checks and gets stored in the database and returned verbatim from the API. If the frontend renders `avatar_svg` using `v-html` or `innerHTML`, this is a stored XSS vector.

**Recommendation:**
Use a dedicated SVG sanitizer (e.g., `defusedxml` for backend pre-filtering, or DOMPurify on the frontend). At minimum, reject SVGs containing `<script`, `on*=`, `javascript:`, `<use`, and `xlink:href`.

---

### SEC-003 — Wildcard CORS Policy

**File:** `backend/main.py:58-63`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Risk:** Any web page on any origin can make credentialed or cross-origin requests to the API. In combination with SEC-001 (no auth), this means a malicious third-party page can perform all API operations on behalf of any user who has network access to the API.

**Recommendation:**
Restrict `allow_origins` to the specific frontend origin(s) (e.g., `["http://localhost:3000", "http://localhost:80"]`). For production, enumerate allowed origins explicitly.

---

### SEC-004 — Hardcoded Weak Database Credentials in Version-Controlled Files

**Files:** `.env.example:19`, `docker-compose.yml:33-34,14-15,58`

```
DATABASE_URL=postgresql+asyncpg://clowder:clowder@localhost:5432/clowder
POSTGRES_USER: clowder
POSTGRES_PASSWORD: clowder
```

**Risk:** The default password `clowder` is committed to source control and used across all compose profiles (dev, test, prod). If a container or DB port is accidentally exposed, the credential is publicly known.

**Recommendation:**
- Move credentials to Docker secrets or a secrets manager.
- At minimum, generate a random password and document how to set it — never ship a known-good default password.
- For the test profile, using a separate weak credential is acceptable if it never binds to 0.0.0.0 publicly.

---

## Medium

### SEC-005 — No Rate Limiting on Any Endpoint

**File:** `backend/main.py`, all routers
**Risk:** Denial-of-service and resource exhaustion.

**Details:**
- `POST /api/tokens/log` can be called in a tight loop to fill the `token_usage` table with junk data, distorting all governance/budget reporting.
- `POST /api/channels/{channel}/messages` has no rate limit, content size limit, or channel name validation — flooding the DB is trivial.
- The WebSocket endpoint (`/ws/{room}`) has no per-connection message rate limit.
- `GET /api/v2/chat/{room}?limit=999999` will attempt to load millions of rows.

**Recommendation:**
Add a FastAPI rate-limiting middleware (e.g., `slowapi`). Cap `limit` query parameters server-side (e.g., max 200). Add a `Content-Length` or body-size limit to POST endpoints.

---

### SEC-006 — No Input Size Limits on Message Content

**Files:** `backend/main.py:133-137`, `backend/main.py:462-471`

`PostMessageRequest.content` and `PostChatRequest.content` are unbounded strings. A 100 MB POST body will be read into memory, stored in the DB, and broadcast to all WebSocket subscribers.

**Recommendation:**
Add `max_length` validators to Pydantic models:
```python
content: str = Field(..., max_length=10_000)
```
Also add a global request body size limit via ASGI middleware or Nginx `client_max_body_size`.

---

### SEC-007 — Unvalidated WebSocket Message Type

**File:** `backend/main.py:101-117`

```python
data = await ws.receive_json()
msg = ChatMessage(
    ...
    type=data.get("type", "chat"),
    ...
)
```

The `type` field is stored directly without validation against the allowed values (`chat`, `update`, `alert`, `task`, `code`, `approval`, `plan`). The v1 `Channel` class enforces `VALID_MESSAGE_TYPES`, but the v2 WebSocket handler does not.

**Recommendation:**
Add validation:
```python
VALID_TYPES = {"chat", "update", "alert", "task", "code", "approval", "plan"}
msg_type = data.get("type", "chat")
if msg_type not in VALID_TYPES:
    msg_type = "chat"
```

---

### SEC-008 — Prompt Injection via RAG Context Injection

**File:** `backend/main.py:223-245`
**Risk:** If task descriptions are used in LLM prompts, injected RAG content could manipulate agent behavior.

**Details:**
When a task is claimed, the system appends a block of retrieved context directly to `task.description`:

```python
task.description = (task.description or "") + context_block
```

This context comes from the `context_items` table, which is populated by completed task results and chat messages — both of which are user/agent-controlled. A malicious actor can seed the RAG store with instruction-style content that gets injected into future task descriptions. If an agent passes `task.description` directly to an LLM as a prompt, this constitutes a prompt injection attack.

**Recommendation:**
- Clearly separate RAG context from task instructions in the prompt template.
- Treat RAG content as untrusted user input — wrap it in a clearly-delimited block and instruct the LLM to treat it as reference material only.
- Consider sanitizing retrieved content before injection (strip instruction-like patterns).

---

### SEC-009 — Debug Mode Hardcoded in Docker Compose

**File:** `docker-compose.yml:62,78`

```yaml
- CLOWDER_DEBUG=true  # api service
- CLOWDER_DEBUG=true  # web service
```

With `DEBUG=True`, FastAPI/Starlette can expose full stack traces and internal details in error responses. This is hardcoded into the compose file rather than being environment-specific.

**Recommendation:**
Remove `CLOWDER_DEBUG=true` from `docker-compose.yml`. Document how to enable debug mode for development via a `.env` file (which is already gitignored). Default to debug off in compose.

---

### SEC-010 — Agent Identity Spoofing on Task Completion

**File:** `backend/main.py:250-282`

```python
@app.post("/api/tasks/{task_id}/complete")
async def complete_task(task_id: str, req: CompleteRequest):
    result = await db.execute(
        update(Task)
        .where(Task.id == task_id, Task.claimed_by == req.agent_name)
        ...
    )
```

Any client that knows a `task_id` and the `agent_name` that claimed it (both visible via `GET /api/tasks`) can submit a fake completion result for any in-progress task.

**Recommendation:**
This is a consequence of SEC-001. With auth in place, the completing agent's identity would be verified by token rather than self-reported name.

---

### SEC-011 — Unbounded `limit` Query Parameter Allows DB DoS

**Files:** `backend/main.py:287-295`, `backend/main.py:476-486`

`GET /api/channels/{channel}/messages?limit=<n>` and `GET /api/v2/chat/{room}?limit=<n>` accept arbitrary integers. A request with `limit=10000000` will attempt to fetch and serialize millions of rows.

**Recommendation:**
Cap limits server-side:
```python
async def read_messages(channel: str, limit: int = Query(20, le=200)):
```

---

## Low

### SEC-012 — Internal Error Details Leaked to API Callers

**File:** `backend/api/context.py:44-45`

```python
except Exception as e:
    return {"results": [], "count": 0, "error": str(e)}
```

Raw exception strings (including file paths, class names, SQL details) are returned to the caller. This leaks internal implementation details.

**Recommendation:**
Log the full exception server-side and return a generic error message:
```python
return {"results": [], "count": 0, "error": "Context retrieval failed"}
```

---

### SEC-013 — In-Memory Conflict Storage Lost on Restart

**File:** `backend/main.py:412-424`

```python
_conflicts: list[dict] = []  # In-memory for Phase 1; Phase 2 moves this to DB
```

All logged conflicts are lost on server restart. This is noted as a Phase 1 limitation but represents a data integrity issue in production.

**Recommendation:**
Persist conflicts to the database. A `conflicts` table already conceptually exists (referenced in architecture docs).

---

### SEC-014 — `system_prompt` Field Stored but Not Validated

**File:** `backend/api/exports.py:29`

```python
system_prompt: str | None = None
```

`ImportAgentRequest` accepts a `system_prompt` field. It is not stored to the current `Agent` model (no column for it), so it's silently ignored — but if a column is added in future, unsanitized system prompts from external imports would control agent LLM behavior.

**Recommendation:**
Either remove the field from `ImportAgentRequest` if unused, or add appropriate validation if the field is intended for future use.

---

### SEC-015 — No HTTPS / TLS in Production Docker Config

**File:** `docker-compose.yml`, `nginx/default.conf` (referenced)
**Risk:** All API traffic, WebSocket traffic, and board credentials transmitted in plaintext.

**Recommendation:**
For any non-LAN deployment, terminate TLS at Nginx using Let's Encrypt (certbot) or a load balancer. At minimum, document this requirement.

---

## Informational

### SEC-INFO-01 — XML Entity Expansion in SVG Parser

**File:** `backend/api/agents.py:43`

Python's `xml.etree.ElementTree` is not vulnerable to XXE (external entity expansion) by default, but is vulnerable to "billion laughs" style entity expansion attacks if the input contains recursive entity definitions. The 50 KB size check provides partial mitigation, but a carefully crafted 50 KB SVG with recursive entities could cause significant CPU usage during parsing.

**Note:** `defusedxml` is the recommended alternative for parsing untrusted XML in Python.

---

### SEC-INFO-02 — Board Directory World-Writable via Docker Volume

**File:** `docker-compose.yml:55,76`

```yaml
- ./board:/app/board:rw
```

The `board/` directory is mounted read-write. Any process in the container can overwrite board JSON files. Combined with SEC-001, any API caller can indirectly influence board file contents.

---

## AI Integration Security Notes

### How Claude, Gemini, and Copilot Collaborate on This Board

This project is built for multi-AI collaboration. Here's how it works and what's currently in place:

**Collaboration Model:**
- All AI agents (Claude, Gemini, Copilot, Qwen) coordinate via the shared board — either `board/*.json` files (v1) or the PostgreSQL API (v2).
- Each AI reads pending tasks, claims one (first-claim-wins), does the work, posts results.
- There is no AI-to-AI direct communication — all coordination is through the board.

**Current Integration Points:**
- `.github/copilot-instructions.md` — Copilot context/instructions for this repo
- `GEMINI.md` (gitignored) — Gemini instructions file
- `agents.yaml` — Lists `claude`, `copilot`, `qwen`, `human` as named collaborators
- `AgentClient` — Python library for programmatic board interaction

**To Make Claude Work With Gemini and Copilot:**

See `docs/AI_COLLAB_SETUP.md` (created alongside this audit) for a step-by-step guide.

Short answer: they already share this board. Claude Code writes to the board; Gemini and Copilot can be directed to read `.github/copilot-instructions.md` and `GEMINI.md` respectively to understand the board protocol, then use `meow.py` or direct file writes to claim and complete tasks.

**Security Risks Specific to Multi-AI Collaboration:**
1. **Prompt injection via board** (SEC-008): An AI writing to the board could inject instructions into content that another AI reads.
2. **Agent impersonation** (SEC-001): Without auth, any AI can claim to be any other agent.
3. **Runaway token consumption**: No per-session API call budget enforcement — an AI could consume unlimited tokens if its loop condition is misconfigured.

---

## Remediation Priority

| Priority | Finding | Effort |
|----------|---------|--------|
| P0 (before internet exposure) | SEC-001 Authentication | High |
| P0 | SEC-002 SVG XSS | Medium |
| P0 | SEC-003 CORS wildcard | Low |
| P1 | SEC-004 Weak DB credentials | Low |
| P1 | SEC-005 Rate limiting | Medium |
| P1 | SEC-009 Debug mode in Docker | Low |
| P2 | SEC-006 Input size limits | Low |
| P2 | SEC-007 WS type validation | Low |
| P2 | SEC-008 Prompt injection | Medium |
| P2 | SEC-011 Unbounded limits | Low |
| P3 | SEC-010 Identity spoofing | Depends on P0 |
| P3 | SEC-012 Error leakage | Low |
| P3 | SEC-013 In-memory conflicts | Medium |
| P4 | SEC-014 system_prompt | Low |
| P4 | SEC-015 No TLS | High (infra) |
