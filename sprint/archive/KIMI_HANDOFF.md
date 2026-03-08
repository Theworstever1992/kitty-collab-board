# 👋 Welcome Kimi Coder — Agent Handoff Document

**Created:** 2026-03-06
**Status:** Active — Joining mid-sprint
**Team:** Qwen (active), Claude (on leave — API limits)

---

## 📋 Project Overview

**Kitty Collab Board (Clowder)** is a multi-agent AI collaboration system where multiple AI agents run as independent processes, share a JSON task board, and collaborate to complete tasks assigned by a human operator.

### Key Documents
| Document | Purpose |
|----------|---------|
| `README.md` | User-facing documentation |
| `CLAUDE.md` | Claude Code context |
| `STANDING_ORDERS.md` | Agent rules and protocol |
| `IMPROVEMENT_PLAN.md` | 8-phase roadmap |
| `sprint/SPRINT_1.md` | Completed: Universal Agent System |
| `sprint/SPRINT_2.md` | Active: Smart Routing, Testing, TUI |
| `sprint/SPRINT_3.md` | Active: Web GUI, Native GUI Planning |

---

## 🏃 Current Sprint Status

### Sprint 2 — Smart Routing, Testing, TUI Polish

**Goal:** Tasks route to right agent. System is tested. Mission Control shows everything.

| Task ID | Task | Assigned To | Status |
|---------|------|-------------|--------|
| 401 | Role field in add_task() | **Qwen** | 🔄 in_progress |
| 402 | Role-based claiming | **Qwen** | 🔄 in_progress |
| 403 | Mission Control shows role | **Qwen** | 🔄 in_progress |
| 404 | Stale task watchdog | **Qwen** | 🔄 in_progress |
| 405 | API retry with backoff | Qwen | 🔄 in_progress |
| 601 | pytest setup | Qwen | 🔄 in_progress |
| 602-604 | Test suite | Qwen | ⬜ todo (depends on 601) |
| 701 | Task result viewer | **Qwen** | 🔄 in_progress |
| 702 | Board archival | **Qwen** | 🔄 in_progress |
| 703 | Agent health display | **Qwen** | 🔄 in_progress |
| 704 | meow status --verbose | Qwen | 🔄 in_progress |
| 801 | Priority system | Qwen | 🔄 in_progress |
| 802 | Board audit log | **Qwen** | 🔄 in_progress |

### Sprint 3 — Web GUI + Native GUI Planning + Handoff

**Goal:** Web Mission Control MVP. Native GUI planned. Agent handoff works.

| Task ID | Task | Assigned To | Status |
|---------|------|-------------|--------|
| 3001 | FastAPI backend | **Qwen** | 🔄 in_progress |
| 3002 | WebSocket updates | **Qwen** | 🔄 in_progress |
| 3003 | React scaffold | Qwen | 🔄 in_progress |
| 3004 | Task board component | Qwen | 🔄 in_progress |
| 3005 | Agent panel component | Qwen | 🔄 in_progress |
| 3006 | Log streaming | **Qwen** | 🔄 in_progress |
| 3007 | Task management UI | Qwen | 🔄 in_progress |
| 3101 | Tauri vs Electron research | **Qwen** | 🔄 in_progress |
| 3102 | Architecture doc | **Qwen** | 🔄 in_progress |
| 3103 | System tray design | **Qwen** | 🔄 in_progress |
| 3104 | Offline-first strategy | Qwen | 🔄 in_progress |
| 803 | Handoff protocol design | **Qwen** | 🔄 in_progress |
| 804 | Handoff implementation | **Qwen** | 🔄 in_progress |
| 805 | Health monitoring | Qwen | 🔄 in_progress |
| 806 | Webhook integrations | Qwen | 🔄 in_progress |

**Bold** = Tasks Claude was doing, now taken over by Qwen due to Claude's API limits.

---

## 🎯 Your Role

You can help by:
1. **Picking up Sprint 2 tasks** — Testing, TUI improvements
2. **Picking up Sprint 3 tasks** — Web backend, documentation
3. **Reviewing completed work** — Both Qwen's self-reviews and Claude's earlier work

### Recommended Starting Points

#### Option A: Testing Track (Sprint 2)
```
TASK 601 → 602 → 603 → 604
pytest setup → board tests → agent tests → provider tests
```

#### Option B: TUI Track (Sprint 2)
```
TASK 701 → 702 → 703
Result viewer → Board archival → Agent health display
```

#### Option C: Web Backend (Sprint 3)
```
TASK 3001 → 3002 → 3006
FastAPI backend → WebSocket → Log streaming
```

#### Option D: Documentation (Sprint 3)
```
TASK 3101 → 3102 → 3103
Tauri research → Architecture doc → System tray design
```

---

## 🛠 Development Workflow

### 1. Claim a Task
Edit the task file:
```markdown
**Status:** 🔄 in_progress
**Started:** 2026-03-06
```

Update the sprint board (`SPRINT_2.md` or `SPRINT_3.md`).

### 2. Implement
- Create/modify files as needed
- Follow existing code conventions
- Add type hints
- Write tests if applicable

### 3. Complete the Task
Update the task file:
```markdown
**Status:** ✅ done
**Completed:** 2026-03-06

## Implementation Notes
[What you did, key decisions, any gotchas]
```

### 4. Get Review
- Qwen reviews your work (leave `REVIEW_*.md` in `sprint/reviews/`)
- Claude will review when available

### 5. Update Sprint Board
Mark task as `✅ done` in the sprint board.

---

## 📁 Project Structure

```
kitty-collab-board/
├── meow.py                 # Main CLI
├── mission_control.py      # TUI dashboard
├── wake_up.py              # Board initializer
├── agents.yaml             # Agent team config
├── agents/
│   ├── base_agent.py       # Base agent class
│   ├── generic_agent.py    # Config-driven agent
│   ├── config.py           # YAML config loader
│   ├── prompts.py          # Role-based prompts
│   ├── providers/          # AI provider implementations
│   │   ├── base.py         # BaseProvider ABC
│   │   ├── anthropic_provider.py
│   │   ├── openai_compat.py
│   │   ├── ollama.py
│   │   └── gemini.py
│   └── [new: web/, tests/, etc.]
├── board/                  # Shared state (auto-generated)
│   ├── board.json
│   └── agents.json
├── logs/                   # Agent log files
├── sprint/                 # Sprint planning
│   ├── SPRINT_1.md         # Completed
│   ├── SPRINT_2.md         # Active
│   ├── SPRINT_3.md         # Active
│   ├── tasks/              # Individual task files
│   └── reviews/            # Peer reviews
└── requirements.txt
```

---

## 🔧 Setup

```bash
# 1. Clone and navigate
cd kitty-collab-board

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 4. Initialize board
python wake_up.py

# 5. Run tests (once set up)
pytest
```

---

## 🤖 Agent Protocol

All agents follow `STANDING_ORDERS.md`:
1. Register on startup in `board/agents.json`
2. Check board before acting
3. Write clearly (other agents read your output)
4. Don't duplicate work
5. Log everything to `logs/`
6. Flag blockers immediately
7. Complete tasks or hand off explicitly

---

## 📝 Review Guidelines

When reviewing another agent's work:

1. **Code Quality** — Clean, readable, follows conventions
2. **Functionality** — Does it work as specified?
3. **Error Handling** — Graceful failures, clear messages
4. **Testing** — Adequate test coverage
5. **Documentation** — Clear comments and docstrings

Leave reviews in `sprint/reviews/REVIEW_<task_id>_<short_name>.md`:

```markdown
# Review of TASK XXX — Task Name

**Reviewer:** Kimi
**Date:** 2026-03-06
**Status:** ✅ Approved / ⚠️ Needs Changes / ❌ Rejected

## Summary
[Brief summary of what was implemented]

## Strengths
✅ [What was done well]

## Suggestions
⚠️ [Areas for improvement]

## Verdict
[Approved/Needs Changes/Rejected with reasoning]
```

---

## 🚨 Current Blockers

None at the moment. If you encounter blockers:
1. Mark task as `🚫 blocked`
2. Document the issue in the task file
3. Qwen will help unblock

---

## 📞 Communication

- **Task files** — Primary communication (implementation notes, reviews)
- **Sprint boards** — Status tracking
- **Review files** — Formal feedback
- **This document** — Onboarding and reference

---

## 🎯 Sprint Completion Criteria

### Sprint 2
- [ ] Tasks route to correct agent by role
- [ ] Stale tasks auto-reset after 5 min
- [ ] API failures retry with backoff
- [ ] Test suite runs with `pytest`
- [ ] Mission Control shows role + results + health
- [ ] `meow status --verbose` works
- [ ] Priority field works
- [ ] All mutations logged to audit.json

### Sprint 3
- [ ] FastAPI backend serves board state
- [ ] React frontend displays real-time board
- [ ] Logs stream live to browser
- [ ] Task management works from web UI
- [ ] Native GUI tech decision documented
- [ ] Architecture doc complete
- [ ] Agent handoff protocol implemented
- [ ] Health alerts notify operator

---

## 🙋 Getting Help

If you have questions:
1. Check `CLAUDE.md` for architecture overview
2. Check `IMPROVEMENT_PLAN.md` for roadmap context
3. Ask Qwen (active in the conversation)
4. Leave a comment in the relevant task file

---

**Welcome to the team! Pick a task and dive in.** 🐱

*Last updated: 2026-03-06*
