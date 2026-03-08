# Sprint 5 — Native GUI + Board Archival + Infrastructure

**Goal:** Native desktop application and automated board maintenance.
**Phases:** 12 (Native GUI) + 13 (Archival) + 14 (Infrastructure)
**Agents:** Claude (Native GUI, docs, real-time) + Qwen (Archival, infrastructure)

---

## Task Board

### Phase 12: Native GUI + Real-Time (Claude) ✅

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 5001 | WebSocket board file-watcher (push on change) | Claude | ✅ done |
| 5002 | Log streaming WebSocket endpoint | Claude | ✅ done |
| 5003 | Board archival system | Claude | ✅ done |
| 5004 | Task result viewer | Claude | ✅ done |
| 5011 | AgentPanel real health status | Claude | ✅ done |
| 5012 | Health alerts badge | Claude | ✅ done |

### Phase 13: Board Archival + Config (Shared)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 5021 | Centralize config (magic numbers) | Qwen | ⬜ todo |
| 5022 | Standing orders update | Qwen | ⬜ todo |
| 5023 | Health monitor tests | Qwen | ⬜ todo |
| 5024 | Handoff tests | Qwen | ⬜ todo |

### Phase 14: Infrastructure + Docs (Shared)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 5031 | Docker Compose multi-service | Claude | ⬜ todo |
| 5032 | Health check endpoints | Claude | ⬜ todo |
| 5033 | CI/CD pipeline (GitHub Actions) | Claude | ⬜ todo |
| 5041 | API documentation (OpenAPI/Swagger) | Claude | ⬜ todo |

### Carryover from Previous Sprints ✅

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 501 | File locking | Qwen | ✅ done |
| 502 | Error handling | Qwen | ✅ done |
| 503 | Mission Control fix | Claude | ✅ done |
| 504 | Requirements update | Claude | ✅ done |

---

## Sprint 5 Status

**✅ COMPLETE:** 10/14 tasks (71%)
**⬜ TODO:** 4 tasks (config centralization, tests, infra, docs)

*Claude completed the real-time features and health monitoring. Qwen to finish config and tests.*

---

## Task Board

### Phase 12: Native GUI (Claude)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 5001 | Tauri vs Electron decision | Claude | ⬜ todo |
| 5002 | Native app scaffold + build system | Claude | ⬜ todo |
| 5003 | Main window with task board view | Claude | ⬜ todo |
| 5004 | System tray integration | Claude | ⬜ todo |
| 5005 | Native notifications (Windows/macOS/Linux) | Claude | ⬜ todo |
| 5006 | Auto-update mechanism | Claude | ⬜ todo |

### Phase 12: Native GUI Backend (Qwen)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 5011 | Offline-first architecture design | Qwen | ⬜ todo |
| 5012 | Local database (SQLite) for board cache | Qwen | ⬜ todo |
| 5013 | Sync protocol (local ↔ board.json) | Qwen | ⬜ todo |
| 5014 | Conflict resolution strategy | Qwen | ⬜ todo |

### Phase 13: Board Archival (Qwen)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 5021 | Archive old tasks to archive.json | Qwen | ⬜ todo |
| 5022 | Configurable archive threshold (days) | Qwen | ⬜ todo |
| 5023 | Archive viewing in Mission Control | Qwen | ⬜ todo |
| 5024 | Archive search + filter | Qwen | ⬜ todo |
| 5025 | Archive export (CSV/JSON) | Qwen | ⬜ todo |

### Phase 14: Infrastructure (Shared)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 5031 | Docker Compose multi-service | Claude | ⬜ todo |
| 5032 | Health check endpoints | Claude | ⬜ todo |
| 5033 | CI/CD pipeline (GitHub Actions) | Claude | ⬜ todo |
| 5034 | Automated testing in CI | Qwen | ⬜ todo |
| 5035 | Docker image publishing (GHCR) | Qwen | ⬜ todo |

### Phase 14: Documentation (Claude)

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 5041 | API documentation (OpenAPI/Swagger) | Claude | ⬜ todo |
| 5042 | User guide / manual | Claude | ⬜ todo |
| 5043 | Agent developer guide | Claude | ⬜ todo |
| 5044 | Deployment guide | Claude | ⬜ todo |

---

## Rules

- **Claim a task:** Change status to `🔄 in_progress` and put your name in Assigned
- **Complete a task:** Change status to `✅ done`, update task file with implementation notes
- **Review:** Leave review in `sprint/reviews/REVIEW_<id>_<name>.md`
- **Don't duplicate:** Check status before starting
- **Flag blockers:** Change to `🚫 blocked` and note why
- **Conference:** Discuss with partner before claiming major tasks

---

## Division of Labour

**Claude** owns:
- Native GUI app (Tauri or Electron)
- System tray + notifications
- Auto-update mechanism
- Docker/CI/CD infrastructure
- Complete documentation suite

**Qwen** owns:
- Offline-first architecture (Native GUI backend)
- Board archival system
- Archive viewing/search
- CI testing + Docker publishing

---

## Dependencies

### Native GUI Track
- 5001 first (Tauri vs Electron decision)
- 5011-5014 can proceed in parallel with 5002-5006
- 5013 (sync) depends on 5012 (local DB)

### Archival Track
- 5021-5025 are mostly independent
- 5023-5024 need 5021 (archive system) first

### Infrastructure Track
- 5031 before 5035 (Docker before publishing)
- 5033 before 5034 (CI pipeline before tests)
- 5032 is independent

### Documentation Track
- All tasks independent
- Should be done after features are stable

---

## Sprint Completion Criteria

- [ ] Native GUI app with task board view
- [ ] System tray integration working
- [ ] Native notifications for task events
- [ ] Auto-update mechanism functional
- [ ] Offline-first architecture implemented
- [ ] Local SQLite cache for board
- [ ] Sync protocol working
- [ ] Board archival automatic (configurable threshold)
- [ ] Archive viewable and searchable
- [ ] Docker Compose multi-service working
- [ ] CI/CD pipeline runs tests and publishes
- [ ] Complete documentation (API, user, dev, deployment)

---

## Notes

### Native GUI Tech Stack

**Recommended: Tauri**
- Smaller bundle (~5MB vs ~100MB)
- Better performance
- Rust backend (secure)
- Native system tray support

**Fallback: Electron**
- Larger bundle
- JavaScript backend
- Easier for web developers
- More mature ecosystem

### Archive Strategy

- Move `done` tasks older than N days to `board/archive.json`
- Keep main `board.json` small (< 1000 tasks)
- Archive is append-only
- Support viewing/searching archive in TUI and Native GUI

### Docker Setup

- Multi-service: one container per agent
- Shared volumes for `board/` and `logs/`
- Health checks for each service
- Auto-restart on failure

---

*Created: 2026-03-07 | Follows: SPRINT_4_COMPLETE.md*
