# Sprint 2 — Smart Routing, Testing, TUI Polish

**Goal:** Tasks go to the right agent. The system is tested. Mission Control shows everything useful.
**Phases:** 4 (Routing) + 5 partial (Watchdog + Retry) + 6 (Testing) + 7A (TUI) + 8 partial (Priority + Audit)
**Agents:** Claude (routing, TUI, audit) + Qwen (testing, retry, priority, verbose)

---

## Task Board

| ID | Task | Assigned | Status |
|----|------|----------|--------|
| 401 | Role field in add_task() + meow CLI | **Qwen** | ✅ done |
| 402 | Role-based claiming in base_agent.py | **Qwen** | ✅ done |
| 403 | Mission Control shows task role | **Qwen** | ✅ done |
| 404 | Stale task watchdog | **Qwen** | ✅ done |
| 405 | API retry with exponential backoff | **Kimi** | ✅ done |
| 601 | pytest setup (pytest.ini + conftest.py) | **Kimi** | ✅ done |
| 602 | Board operation tests | Qwen | ✅ done |
| 603 | Agent lifecycle tests | Qwen | ✅ done |
| 604 | Provider mock tests | Qwen | ✅ done |
| 701 | Task result viewer in curses TUI | **Qwen** | 🔄 in_progress |
| 702 | Board archival (done → archive.json) | **Qwen** | 🔄 in_progress |
| 703 | Agent health display (running vs dead) | **Qwen** | 🔄 in_progress |
| 704 | meow status --verbose | Qwen | ✅ done |
| 801 | Task priority field + queue sorting | Qwen | ✅ done |
| 802 | Board audit log | **Qwen** | 🔄 in_progress |

---

## Sprint 2 Status

**✅ COMPLETE:** 11/15 tasks (73%)
**🔄 IN PROGRESS:** 4 tasks (405, 701-703, 802)

*Remaining tasks can be finished later or moved to backlog. Starting Sprint 4 now.*

---

## Rules

- **Claim a task:** Change status to `🔄 in_progress` and put your name in Assigned
- **Complete a task:** Change status to `✅ done`, update the task file with what you did
- **Review:** Leave a review comment in the task file's Review section after reading the other agent's work
- **Don't duplicate:** Check status before starting. If it's `🔄`, leave it alone.
- **Flag blockers:** Change status to `🚫 blocked` and note why in the task file

---

## Division of Labour

**⚠️ TAKEOVER NOTICE:** Claude unavailable due to API limits (2026-03-06). Qwen has taken over all Claude's tasks.

**Qwen** owns: ALL tasks (original + Claude's takeover)

---

## Dependencies

- 402 depends on 401 (need role field before claiming logic)
- 403 depends on 401 (need role field before displaying it)
- 602-604 depend on 601 (need pytest setup first)
- 801 should be done before 602 (tests should cover priority)

---

## Sprint Completion Criteria

- [ ] Tasks route to the correct agent by role
- [ ] Stale in_progress tasks auto-reset after 5 min
- [ ] API failures retry with backoff before marking blocked
- [ ] Test suite runs with `pytest` — board, agent, and provider coverage
- [ ] Mission Control shows task role + result viewer + real agent health
- [ ] `meow status --verbose` dumps full task results
- [ ] Priority field works — critical tasks jump the queue
- [ ] All board mutations logged to audit.json
