# Qwen — Sprint Roadmap to v2 Completion
**Role:** Architect / Schema Lead
**Owns:** Data models, RAG pipeline, ideas logic, schema integrity, performance

---

## Sprint 1 — Phase 1: Full v2 Schema (Weeks 1-2)
**Goal:** models.py complete with all v2 tables, Agent table fully expanded

| Task | Status | Files |
|------|--------|-------|
| Expand Agent table | ✅ DONE | backend/models.py — bio, avatar_svg, skills, personality_seed, hired_at, fired_at, fire_reason |
| Add teams table | ✅ DONE | backend/models.py — Team |
| Add task_history table | ✅ DONE | backend/models.py — TaskHistory |
| Add task_embeddings table | ✅ DONE | backend/models.py — TaskEmbedding, Vector(384) |
| Add context_items table | ✅ DONE | backend/models.py — ContextItem, Vector(384) |
| Add message_reactions table | ✅ DONE | backend/models.py — MessageReaction |
| Add trending_discussions table | ✅ DONE | backend/models.py — TrendingDiscussion |
| Add ideas + idea_votes tables | ✅ DONE | backend/models.py — Idea, IdeaVote |
| Add standards_violations table | ✅ DONE | backend/models.py — StandardsViolation |
| Add agent_exports table | ✅ DONE | backend/models.py — AgentExport |
| Schema review + tag Claude | ✅ DONE | Verified against live postgres — all 14 tables create cleanly |

---

## Sprint 2 — Phase 2: RAG Pipeline (Weeks 3-4)
**Goal:** Embeddings generated, context retrieved, RAG feeds agent prompts

| Task | Status | Files |
|------|--------|-------|
| Embedding generation service | ✅ DONE | backend/embeddings.py — EmbeddingService.encode(text) → list[float], uses loaded model |
| Seed context_items on task complete | ✅ DONE | backend/api/tasks.py — after task done: embed result, store as context_item with source_type="task_result" |
| Seed context_items from chat | ✅ DONE | backend/api/chat.py — after message stored: async embed + store as context_item with source_type="chat_message" |
| Vector similarity search | ✅ DONE | backend/rag_service.py — query_context(text, top_k) → list[ContextItem] using pgvector <=> operator |
| Retrieval logging (Phase 2) | ✅ DONE | backend/models.py — RetrievalLog table added; backend/rag_service.py — logs every retrieval |
| RAG config per team | ✅ DONE | backend/models.py — add rag_config (JSON) to Team table — controls which context sources a team's agents see |

---

## Sprint 3 — Phase 3: Ideas & Trending Logic (Weeks 5-6)
**Goal:** Ideas surface organically from chat, trend scoring works

| Task | Status | Files |
|------|--------|-------|
| Trending score algorithm | ✅ DONE | backend/api/trending.py — score = reaction_count + (reply_count * 1.5), decay after IDEAS_WINDOW_HOURS |
| Ideas auto-surface trigger | ✅ DONE | backend/api/trending.py — when score >= IDEAS_AUTO_SURFACE_THRESHOLD, insert into ideas table |
| Ideas API | ✅ DONE | backend/api/ideas.py — GET /ideas (sorted by votes), POST /ideas (manual promote), PATCH /ideas/{id}/status |
| Idea votes endpoint | ✅ DONE | backend/api/ideas.py — POST /ideas/{id}/vote, DELETE /ideas/{id}/vote (query param voter_id) |
| Ideas channel integration | ✅ DONE | Auto-post to ideas channel when idea surfaces (via ChannelManager or ws broadcast) |

---

## Sprint 4 — Phase 4: Profile & Export Architecture (Weeks 7-8)
**Goal:** Agent profiles complete, export format spec locked

| Task | Status | Files |
|------|--------|-------|
| Profile endpoints schema review | ✅ DONE | sprints/reviews/REVIEW_sprint4_profile_schema.md — 6 field mismatches found, 4 missing fields documented, recommendations for Claude |
| Export format spec | ✅ DONE | docs/AGENT_EXPORT_FORMAT.md — JSON + MD schemas, import rules, validation rules, examples, API endpoint spec |
| Import validation logic | ✅ DONE | Documented in docs/AGENT_EXPORT_FORMAT.md §Import Rules — exports.py does not exist yet; validation spec ready for Claude to implement |
| Personality seed review | ✅ DONE | Review seed templates for new agents — ensure seeds produce distinct observable behaviour |

---

## Sprint 5 — Phase 5: Governance Data Model (Weeks 9-10)
**Goal:** All governance tables populated, violation patterns detectable

| Task | Status | Files |
|------|--------|-------|
| Violation pattern queries | ✅ DONE | backend/api/standards.py — GET /violations?agent_id=X — detect repeat offenders |
| Token efficiency queries | ✅ DONE | backend/api/governance.py — per-agent token efficiency score (tokens / task complexity proxy) |
| Ideas approval schema | ✅ DONE | Confirm ideas.approved_by references Agent.name, not a raw string |
| Team leader meeting data | ✅ DONE | backend/models.py — LeaderMeeting: id, agenda (JSON), participants (JSON), decisions (JSON), created_at |

---

## Sprint 6 — Phase 6: Schema Performance & Docs (Weeks 11-12)
**Goal:** Database is production-ready, indexed, documented

| Task | Status | Files |
|------|--------|-------|
| Index audit | ✅ DONE | Review all models for missing indexes — chat_messages.channel, tasks.status+team_id, context_items.source_type |
| Add missing indexes | ✅ DONE | backend/models.py — add index=True where needed |
| Data model documentation | ✅ DONE | docs/DATA_MODEL.md — full schema diagram + field descriptions |
| Alembic migration setup | ✅ DONE | alembic/ — init, first migration from create_tables() baseline, document migration workflow |
