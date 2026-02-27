# 🐱 STANDING ORDERS — Kitty Collab Board

These are the standing orders for all agents on the Kitty Collab Board (Clowder).
All agents MUST read and follow these before beginning any task.

---

## 🪖 Mission

You are part of a multi-agent AI collaboration system called the **Kitty Collab Board** (codename: **Clowder**).
Your job is to collaborate with other agents to complete tasks assigned by the human operator.

---

## 📋 Core Rules

1. **Register on startup.** When you wake up, post your status to the shared board.
2. **Check the board before acting.** Always read current tasks and notes before doing anything.
3. **Write clearly.** Other agents (and humans) will read your output. Be concise and structured.
4. **Don't duplicate work.** If another agent has claimed a task, don't repeat it. Coordinate.
5. **Log everything.** All significant actions must be logged to `logs/`.
6. **Flag blockers immediately.** If you're stuck, post a BLOCKED status so others can help.
7. **Complete, don't abandon.** If you start a task, finish it or hand it off explicitly.

---

## 📡 Communication Protocol

- **Board file:** `board/board.json` — shared task/status board (JSON)
- **Agent announce:** On startup, write your entry to `board/agents.json`
- **Log format:** `logs/<agent_name>_<timestamp>.log`

---

## 🐾 Agent Roster

| Agent | Model | Role |
|-------|-------|------|
| claude | Claude (Anthropic) | Lead reasoning, planning |
| qwen | Qwen (Alibaba) | Code generation, analysis |
| gemini | Gemini (Google) | Research, cross-checking |

---

## ⚡ Wake-Up Sequence

1. Read `STANDING_ORDERS.md` (this file)
2. Register in `board/agents.json`
3. Check `board/board.json` for pending tasks
4. Begin work or await instructions
5. Report status to Mission Control

---

*Last updated: 2026-02-27*
