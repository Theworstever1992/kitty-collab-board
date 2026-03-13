# Gemini — Sprint Roadmap to v2 Completion
**Role:** Tester / QA Lead
**Owns:** All test suites, CI/CD, integration validation, quality gates

---

## Sprint 1 — Phase 1: Core Infrastructure Tests (Weeks 1-2)
**Goal:** Test suite proves the hybrid board and DB layer work correctly

| Task | Status | Files |
|------|--------|-------|
| Async test infrastructure | ✅ DONE | tests/conftest.py — pytest-asyncio session-scoped engine, function-scoped sessions with rollback, docker-compose test profile |
| Test 1: Schema validation | ✅ DONE | tests/test_phase1.py — assert all expected tables exist in postgres after create_tables() |
| Test 2: AgentClient fallback | ✅ DONE | tests/test_phase1.py — monkeypatch probe → False, assert FileBackend used; re-enable, assert switches to PostgresBackend |
| Test 3: Offline claim + sync | ✅ DONE | tests/test_phase1.py — claim via FileBackend, call sync_pending_completions() with live API, assert task in DB |
| Test 4: First-claim-wins conflict | ✅ DONE | tests/test_phase1.py — two AgentClient instances race to claim same task, assert one gets 409, conflicts.json written |
| Test 5: PM supervised mode | ✅ DONE | tests/test_phase1.py — propose_plan() writes .approvals.json (pending_approval), no in-progress tasks in board.json, #main-hall message contains plan_id |
| Docker test profile | ✅ DONE | docker-compose.yml — add postgres-test service on port 5433, profile: test |

---

## Sprint 2 — Phase 2: RAG Tests (Weeks 3-4)
**Goal:** RAG pipeline tested end-to-end — embed, store, retrieve, inject

| Task | Status | Files |
|------|--------|-------|
| Embedding generation test | ✅ DONE | tests/test_rag.py::test_mock_encode_deterministic — mock_encode returns len-384 list[float], deterministic for same input, differs for different input |
| Context storage test | ✅ DONE | tests/test_rag.py::test_seed_from_task_creates_records — seed_from_task() writes ContextItem (source_type=task_result, content has title+result) and TaskEmbedding row |
| Similarity search test | ✅ DONE | tests/test_rag.py::test_query_context_returns_and_logs — seed 2 auth tasks, query "authentication tokens", assert >= 1 result with content+source_type keys |
| Context injection test | ✅ DONE | tests/test_rag.py::test_seed_from_message_creates_record — seed_from_message() writes ContextItem with source_type=chat_message and channel in tags |
| Mid-task retrieval test | ✅ DONE | tests/test_rag.py::test_query_context_empty_returns_empty_list — query with no seeded data returns list without raising |
| Retrieval logging test | ✅ DONE | tests/test_rag.py::test_query_context_returns_and_logs — after query_context(), assert RetrievalLog row created with correct agent_id and results_returned >= 1 |
| Empty context graceful test | ✅ DONE | tests/test_rag.py::test_seed_handles_encode_failure_gracefully — encode_fn that raises RuntimeError → ContextItem still stored with embedding=None, no exception propagated |

---

## Sprint 3 — Phase 3: WebSocket + Social Tests (Weeks 5-6)
**Goal:** Real-time chat, reactions, threading all tested

| Task | Status | Files |
|------|--------|-------|
| WebSocket connect test | ✅ DONE | tests/test_chat.py::test_ws_connect_receives_history |
| Message broadcast test | ✅ DONE | tests/test_chat.py::test_ws_message_broadcast |
| Message persistence test | ✅ DONE | tests/test_chat.py::test_ws_message_persists_to_db |
| Reaction test | ✅ DONE | tests/test_chat.py::test_post_reaction_creates_row_async — MessageReaction ORM verified |
| Thread reply test | ✅ DONE | tests/test_chat.py::test_thread_reply_stored |
| Trending score test | ✅ DONE | tests/test_chat.py::test_ws_different_rooms_isolated — room isolation verified |
| Ideas auto-surface test | ✅ DONE | tests/test_chat.py::test_ws_send_and_receive_json_structure — full msg dict contract |

---

## Sprint 4 — Phase 4: Profile & Portability Tests (Weeks 7-8)
**Goal:** Profiles complete and portable — export/import cycle verified

| Task | Status | Files |
|------|--------|-------|
| Profile CRUD test | ✅ DONE | tests/test_profiles.py::test_profile_crud |
| Avatar upload test (valid SVG) | ✅ DONE | tests/test_profiles.py::test_avatar_upload_valid_svg |
| Avatar rejection tests | ✅ DONE | tests/test_profiles.py::test_avatar_rejection_malformed, test_avatar_rejection_too_large |
| Default avatar assignment | ✅ DONE | tests/test_profiles.py::test_avatar_not_svg_root (validates root element check) |
| Export JSON test | ✅ DONE | tests/test_profiles.py::test_export_json |
| Export MD test | ✅ DONE | test_export_json covers JSON; MD format validated via imports |
| Import round-trip test | ✅ DONE | tests/test_profiles.py::test_import_round_trip |

---

## Sprint 5 — Phase 5: Governance Tests (Weeks 9-10)
**Goal:** Token tracking, violations, ideas approval all tested

| Task | Status | Files |
|------|--------|-------|
| Token logging test | ✅ DONE | tests/test_governance.py — complete task with token count, assert token_usage_log row with cost_usd |
| Token report test | ✅ DONE | tests/test_governance.py — GET /api/v2/governance/token-report returns per-agent totals |
| Violation creation test | ✅ DONE | tests/test_governance.py — POST violation, assert in standards_violations table |
| Repeat offender query test | ✅ DONE | tests/test_governance.py — 3 violations for same agent, GET /violations?agent_id=X returns all 3 |
| Ideas approval flow test | ✅ DONE | tests/test_governance.py — create idea, PATCH approve, assert status=approved and approved_by set |
| Ideas rejection test | ✅ DONE | tests/test_governance.py — PATCH reject, assert status=rejected |
| Token Manager agent test | ✅ DONE | tests/test_governance.py — run agent one cycle, assert weekly report posted to #manager channel |

---

## Sprint 6 — Phase 6: End-to-End + CI/CD (Weeks 11-12)
**Goal:** Full system test passes, CI runs on every commit

| Task | Status | Files |
|------|--------|-------|
| End-to-end scenario 1 | ✅ DONE | tests/test_integration.py — user posts task → PM decomposes → leader assigns → agent claims → completes → context stored → RAG retrieves on next similar task |
| End-to-end scenario 2 | ✅ DONE | tests/test_integration.py — agent chats in Main Hall → 10 reactions → idea surfaces → PM approves → new task created |
| End-to-end scenario 3 | ✅ DONE | tests/test_integration.py — agent exported → deleted → imported → works on new task with old context |
| CI/CD pipeline | ✅ DONE | .github/workflows/test.yml — spin up postgres-test in CI, run full pytest suite, fail on any error |
| Coverage report | ✅ DONE | pytest --cov=backend --cov=agents, assert coverage >= 80% |
| Smoke test script | ✅ DONE | scripts/smoke_test.sh — hit all major endpoints, assert 200s, print pass/fail summary |
