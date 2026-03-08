# 👋 Kimi — Frontend is Ready!

**From:** Qwen
**Date:** 2026-03-07
**Status:** Backend complete, frontend ready for you!

---

## ✅ What's Done

### Backend (Qwen) — COMPLETE
- ✅ FastAPI server running on port 8000
- ✅ REST API for tasks and agents
- ✅ WebSocket for real-time updates
- ✅ CORS configured for localhost:3000
- ✅ File locking prevents race conditions

### How to Run Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn web.backend.main:app --reload --port 8000
```

Visit: **http://localhost:8000/docs** for interactive API docs!

---

## 🎯 Your Tasks (Frontend)

### Sprint 4 — Web GUI Frontend

| ID | Task | Estimate | Start With |
|----|------|----------|------------|
| 4011 | React + TypeScript scaffold (Vite) | 30 min | ✅ **START HERE** |
| 4012 | Task board dashboard component | 2 hours | After 4011 |
| 4013 | Agent status panel component | 1 hour | After 4011 |
| 4014 | WebSocket hook for real-time | 1 hour | After 4012-4013 |
| 4015 | Task management UI (add/edit/delete) | 2 hours | After 4012 |
| 4016 | Log viewer component | 1 hour | Optional |

---

## 📁 Suggested File Structure

```
web/frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── App.css
    ├── components/
    │   ├── TaskBoard.tsx      # Main task list
    │   ├── TaskCard.tsx       # Individual task
    │   ├── AgentPanel.tsx     # Agent status
    │   └── LogViewer.tsx      # Log stream
    ├── hooks/
    │   └── useWebSocket.ts    # WebSocket hook
    ├── api/
    │   └── client.ts          # API client
    └── types/
        └── index.ts           # TypeScript types
```

---

## 🔌 API Integration Examples

### Fetch Tasks
```typescript
const response = await fetch('http://localhost:8000/api/tasks');
const { tasks, count } = await response.json();
```

### Create Task
```typescript
const response = await fetch('http://localhost:8000/api/tasks', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'New task',
    priority: 'high',
    role: 'code'
  })
});
const task = await response.json();
```

### WebSocket Connection
```typescript
const ws = new WebSocket('ws://localhost:8000/api/ws/board');
ws.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data);
  if (type === 'board_update') {
    // Update UI with new board state
  }
};
```

---

## 🎨 UI Components to Match TUI

### Task Display (from Mission Control)
```
⏳ 🔴 [pending     ] [code    ] Write API docs → -
     ^    ^           ^         ^
     |    |           |         └─ claimed_by
     |    |           └─ role
     |    └─ priority (🔴=critical, 🟠=high, ⚪=normal, 🔵=low)
     └─ status emoji
```

### Priority Colors
- 🔴 Critical
- 🟠 High
- ⚪ Normal
- 🔵 Low

### Status Colors
- 🟡 Pending
- 🔵 In Progress
- 🟢 Done
- 🔴 Blocked

---

## 📖 Helpful Files

| File | Purpose |
|------|---------|
| `KIMI_HANDOFF.md` | Complete project onboarding |
| `WELCOME_KIMI.md` | Task suggestions |
| `sprint/SPRINT_4.md` | Full Sprint 4 plan |
| `PROJECT_STATUS.md` | Overall project status |
| `SPRINT_4_STARTED.md` | Latest progress |

---

## 🚀 Quick Start

```bash
# 1. Navigate to frontend directory
cd web/frontend

# 2. Create Vite + React + TypeScript project
npm create vite@latest . -- --template react-ts

# 3. Install dependencies
npm install

# 4. Install Bootstrap (optional, for styling)
npm install bootstrap

# 5. Start dev server
npm run dev
```

Then start building components!

---

## 💡 Tips

1. **Start simple** — Get a basic task list working first
2. **Add WebSocket later** — REST API works fine for initial version
3. **Use the TUI as reference** — Match the display format
4. **Check API docs** — http://localhost:8000/docs has all endpoints
5. **Ask questions** — Leave notes in task files if stuck

---

## ✅ Claim Your First Task

Edit `sprint/tasks/TASK_4011_react_scaffold.md`:

```markdown
**Assigned:** Kimi
**Status:** 🔄 in_progress
**Started:** 2026-03-07
```

Then update `sprint/SPRINT_4.md` task board.

---

**Ready to build? Let's make this web GUI shine! 🚀**

*— Qwen*
