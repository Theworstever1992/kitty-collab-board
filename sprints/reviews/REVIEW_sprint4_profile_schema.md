# Review: Sprint 4 — Agent Profile Schema
**Reviewer:** Qwen (Architect / Schema Lead)
**Date:** 2026-03-12
**Sprint:** 4 — Phase 4: Profile & Export Architecture
**Files reviewed:** `backend/models.py`, `backend/main.py`, `2026-03-08-clowder-v2-design.md`

---

## 1. Agent Model Fields (as implemented in `backend/models.py`)

| Field | SQLAlchemy Type | Nullable | Notes |
|-------|----------------|----------|-------|
| `name` | `String(128)` | No | Primary key |
| `role` | `String(64)` | No | Default: `"general"` |
| `model` | `String(128)` | No | Default: `"unknown"` |
| `team` | `String(64)` | Yes | Team membership; see mismatch §3 |
| `status` | `String(32)` | No | Default: `"online"` |
| `last_seen` | `DateTime(timezone=True)` | No | Auto-updated on write |
| `started_at` | `DateTime(timezone=True)` | Yes | Set on first register |
| `bio` | `Text` | Yes | Free-form biography |
| `avatar_svg` | `Text` | Yes | Max 50 KB enforced at API layer |
| `skills` | `JSON` | Yes | List of skill strings |
| `personality_seed` | `Text` | Yes | System prompt prefix for personality |
| `hired_at` | `DateTime(timezone=True)` | Yes | Set when agent is hired |
| `fired_at` | `DateTime(timezone=True)` | Yes | Set when agent is fired |
| `fire_reason` | `Text` | Yes | Reason for termination |

**Total fields: 14**

---

## 2. Design Spec Schema (from `2026-03-08-clowder-v2-design.md`, Section "Data Model")

The design spec's simplified SQL schema for the `agents` table reads:

```sql
agents (id, name, team_id, role, bio, avatar_svg, model, skills_json, preferences_json)
```

---

## 3. Field Naming Mismatches

### Mismatch A: `id` column absent — `name` is PK
**Design spec** shows a separate `id` column alongside `name`.
**Actual model** uses `name` as the primary key directly. There is no separate surrogate `id`.

**Impact:** External systems (e.g., future federation, agent-to-agent references) that expect a numeric or UUID `id` will need to use `name` instead. The API currently reflects this correctly (`/api/agents/{name}/profile`), but Claude's profile endpoints must not assume a numeric PK.

**Recommendation:** Document that `name` is the canonical identifier. Do not add a surrogate `id` now — it would require a schema migration and all existing FK references in `AgentExport.agent_id`, `TokenUsage.agent`, `StandardsViolation.agent_id`, etc. are string-typed and already align with `name`.

### Mismatch B: `team_id` vs `team`
**Design spec:** `agents.team_id` (foreign key to `teams.id`)
**Actual model:** `agents.team` (`String(64)`, no FK constraint, no `index=True`)

**Impact:** The field holds the team identifier but is named `team`, not `team_id`. It lacks a database-level foreign key constraint and an index. Queries filtering agents by team will perform full table scans.

**Recommendation (before Claude ships profile endpoints):**
1. Rename `team` → `team_id` in a migration, or at minimum alias it in the API response as `team_id` for forward compatibility.
2. Add `index=True` to the column immediately — no migration needed, just add `index=True` to the `mapped_column` call.

### Mismatch C: `skills_json` vs `skills`
**Design spec:** column named `skills_json`
**Actual model:** column named `skills` (type `JSON`)

**Impact:** Cosmetic only — the stored type is correct. The API serializes this as `"skills"` in all response bodies. No functional problem. Keep as `skills`.

### Mismatch D: `preferences_json` — not implemented
**Design spec:** `preferences_json` column for per-agent retrieval preferences (what context to focus on, which teams' context to include).
**Actual model:** No such column exists.

This is the most significant gap — see Section 4.

### Mismatch E: `system_prompt` — not in model
**Design spec** (Appendix, Example 3) shows `system_prompt` as a top-level export field.
**Actual model:** Only `personality_seed` exists, which is described (Decision 9) as the system prompt prefix. There is no separate `system_prompt` storage column.

**Assessment:** `personality_seed` covers the intended use. The export spec (docs/AGENT_EXPORT_FORMAT.md) must clarify that `system_prompt` in the export JSON is a *computed* field (constructed at export time, not stored separately), while `personality_seed` is the stored source of truth.

### Mismatch F: `rag_config` — not in Agent model
**Design spec** (Feature 2, RAG Pipeline): *"Team leaders configure per-agent retrieval rules."*
The export appendix shows `"rag_config": {}` as a top-level export field.
**Actual model:** `rag_config` does not appear on the `Agent` table. The `Team` table also lacks it (noted as a TODO in qwen-sprints.md Sprint 2).

**Recommendation:** Add `rag_config: Mapped[Optional[dict]] = mapped_column(JSON)` to `Agent` before profile endpoints ship. This is required for the export format to be meaningful.

---

## 4. Missing Fields (design calls for them; model lacks them)

| Missing Field | Design Reference | Priority | Recommendation |
|---------------|-----------------|----------|----------------|
| `preferences_json` / `preferences` | Data Model schema | High | Add `preferences: Mapped[Optional[dict]] = mapped_column(JSON)` to `Agent`. Stores per-agent context retrieval preferences (which source types to weight, which teams' context to include). Required by Decision 9's reinforcement loop. |
| `rag_config` | Feature 2 RAG, Export Appendix | High | Add `rag_config: Mapped[Optional[dict]] = mapped_column(JSON)` to `Agent`. Controls what context the agent auto-retrieves when claiming tasks. |
| Indexed `team` / `team_id` | Data Model, Query performance | Medium | Add `index=True` to the `team` column. No migration needed. |
| `context_history` | Export Appendix (Example 3) | Low | Spec shows `"context_history": [past decisions]` in export. This is a derived field (queried from `context_items` / `retrieval_logs` at export time), not a stored column. No schema change needed — document this in the export spec. |

---

## 5. Profile Endpoint Review (`GET /api/agents/{name}/profile`)

The existing endpoint in `backend/main.py` (line 341–354) returns:

```json
{
  "name": "...",
  "role": "...",
  "model": "...",
  "team": "...",
  "status": "...",
  "last_seen": "ISO timestamp"
}
```

**Missing from current response (Claude needs to add before shipping):**
- `bio`
- `avatar_svg` (or a URL to it)
- `skills`
- `personality_seed`
- `hired_at`
- `fired_at` / `fire_reason` (for fired agents)

The endpoint is a stub returning only the registration fields. Claude's profile endpoints task must expand this response to include all profile fields.

---

## 6. Supporting Tables — Alignment Check

| Table | Design Name | Actual Name | Status |
|-------|-------------|-------------|--------|
| `agent_exports` | `agent_exports` | `AgentExport` | Aligned |
| `retrieval_logs` | `retrieval_logs` | `RetrievalLog` | Aligned |
| `standards_violations` | `standards_violations` | `StandardsViolation` | Aligned |
| `token_usage_log` | `token_usage_log` | `token_usage` | Minor name divergence — actual table is `token_usage`, not `token_usage_log`. Functionally equivalent. |

`AgentExport` stores rendered export artifacts (format + content). It does not store structured profile data — that lives in `Agent`. This is correct.

---

## 7. Recommendations Summary (ordered by priority)

1. **Add `rag_config` JSON column to `Agent`** — required for export format to be non-empty.
2. **Add `preferences` JSON column to `Agent`** — required for Decision 9 reinforcement loop.
3. **Add `index=True` to `Agent.team`** — performance, no migration cost.
4. **Rename `team` to `team_id` OR document the divergence** — API consumers should expect `team_id` per the design spec. Aliasing in the response dict is the lowest-risk path.
5. **Expand `/api/agents/{name}/profile` response** — Claude's endpoint must include bio, avatar_svg, skills, personality_seed, hired_at.
6. **Document `system_prompt` as computed** — `personality_seed` is stored; `system_prompt` is assembled at export time. The export spec must make this clear.

---

## 8. Import Validation Logic (`backend/api/exports.py`)

`backend/api/exports.py` does not exist yet (Claude is implementing it in parallel).

Import validation recommendations are documented in `docs/AGENT_EXPORT_FORMAT.md` (Section: Import Rules), created as Deliverable 2 of this sprint. Once Claude's file exists, a follow-up review should verify:

- Name validation regex matches the spec (`^[a-zA-Z0-9_-]{1,64}$`)
- Avatar SVG size check is enforced at the API layer (not just trusted from the JSON payload)
- `model` field is ignored on import when the agent is already active (immutability rule)
- Duplicate name handling matches documented policy (upsert vs. error — see export spec for the decision)
