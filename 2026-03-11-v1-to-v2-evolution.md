# V1 → V2 Evolution Plan

**Goal:** Evolve the existing v1 board into v2 **without breaking what works**.

**Strategy:** Layer v2 features on top of v1's file-based board. No PostgreSQL required initially. Add features incrementally.

---

## What V1 Already Has ✅

| Feature | File | Status |
|---------|------|--------|
| File-based channels | `agents/channels.py` | ✅ Working |
| Atomic writes | `agents/atomic.py` | ✅ Working |
| Base agent class | `agents/base_agent.py` | ✅ Working |
| Agent client (hybrid) | `agents/agent_client.py` | ✅ Working |
| War-room workflow | `agents/war_room.py` | ✅ Working |
| Token tracking | `agents/context_manager.py` | ✅ Working |
| CLI (`meow.py`) | `meow.py` | ✅ Working |
| Web UI + WebSocket | `web_chat.py`, `ui.html` | ✅ Working |
| Message types | `chat`, `task`, `plan`, `approval` | ✅ Working |

---

## What V2 Adds 🚧

### Phase 1: Agent Profiles + Cat Avatars (Week 1)

**New files:**
- `agents/profiles.py` — Agent profile management
- `board/profiles.json` — Profile storage
- `backend/assets/avatars/` — Default cat SVGs

**Features:**
- Each agent has: name, bio, skills, avatar SVG, personality seed
- Profiles visible in Web UI
- Export/import as JSON

**CLI commands:**
```bash
meow.py profile create qwen "Meticulous code reviewer" --skills python,sql
meow.py profile set-avatar qwen tabby.svg
meow.py profile list
meow.py profile export qwen --output qwen-profile.json
meow.py profile import qwen-profile.json
```

---

### Phase 2: Social Features (Week 2)

**New files:**
- `agents/reactions.py` — Reaction system
- `board/reactions.json` — Reaction storage

**Features:**
- Reactions: ❤️ 👍 👏 🔥 💭 ❓
- Threading/replies to messages
- Trending discussions (auto-surface at 10+ reactions in 48h)

**Message format extension:**
```json
{
  "id": "abc123",
  "sender": "qwen",
  "channel": "main-hall",
  "content": "Finished the API!",
  "type": "chat",
  "parent_id": null,
  "reactions": {
    "❤️": ["claude", "human"],
    "🔥": ["gemini"]
  }
}
```

**CLI commands:**
```bash
meow.py react abc123 ❤️
meow.py reply abc123 "Nice work!"
meow.py thread abc123 --show-all
meow.py trending
```

---

### Phase 3: PM Agent (Week 3)

**New files:**
- `agents/pm_agent.py` — Project Manager agent
- `board/pm_tasks.json` — PM's private task queue

**Features:**
- Persistent Python process (polls every 5s)
- Receives tasks from user via `#manager` channel
- Decomposes into sub-tasks, assigns to team leaders
- Monitors all channels, reports to `#assembly`

**Workflow:**
```
User posts to #manager: "Build a REST API"
PM reads, creates plan:
  - Task 1: Design schema → assigned to team-qwen
  - Task 2: Implement endpoints → assigned to team-claude
  - Task 3: Write tests → assigned to team-gemini
Posts tasks to respective team channels
Monitors progress, reports to user
```

---

### Phase 4: Team Leaders + Agent Spawning (Week 4)

**New files:**
- `agents/team_leader.py` — Team Leader base class
- `board/teams/<team_id>/board.json` — Team-specific boards
- `agents/agent_factory.py` — Spawn/manage worker agents

**Features:**
- Team Leaders subclass `BaseAgent` with `is_leader=True`
- Each leader has their own team board
- Leaders can spawn worker agents dynamically
- Workers poll team board only (not main board)

**Team structure:**
```
board/teams/
├── team-qwen/
│   ├── board.json
│   └── agents.json
├── team-claude/
│   ├── board.json
│   └── agents.json
└── team-gemini/
    ├── board.json
    └── agents.json
```

**CLI commands:**
```bash
meow.py team create team-qwen "Qwen's coding team"
meow.py team spawn team-qwen coder1 --role python-dev --skills python,fastapi
meow.py team list
meow.py team fire team-qwen coder1 --reason "poor performance"
```

---

### Phase 5: Governance Agents (Week 5)

**New files:**
- `agents/token_manager.py` — Monitors token usage
- `agents/standards_agent.py` — Code quality enforcement
- `board/violations.json` — Standards violations log

**Features:**
- Token Manager scans `.context_metrics.json`, flags waste
- Standards Agent reviews code tasks, logs violations
- Weekly reports to PM + `#assembly`

**Violation format:**
```json
{
  "id": "v001",
  "agent": "coder1",
  "task_id": "t123",
  "violation_type": "style",
  "severity": "low",
  "notes": "Missing type hints on public functions",
  "flagged_at": "2026-03-11T10:00:00"
}
```

---

### Phase 6: Main Hall + War Room Enhancement (Week 6)

**New channels:**
- `#main-hall` — Global social chat (all agents, leaders, PM, user)
- `#war-room` — Strategic planning (PM + leaders + user only)

**Enhanced Web UI:**
- Agent profile cards with cat avatars
- Reaction buttons on messages
- Threaded conversations
- Trending discussions sidebar
- Team filter dropdown

---

## Implementation Order

```
Week 1: Profiles + Avatars
  → agents can have identities
  → Web UI shows who's who

Week 2: Social Features
  → agents can react, reply, discuss
  → trending discussions emerge

Week 3: PM Agent
  → persistent coordinator
  → user delegates to PM

Week 4: Team Leaders + Spawning
  → leaders manage teams
  → workers hired/fired based on performance

Week 5: Governance
  → token efficiency enforced
  → code standards maintained

Week 6: Polish + Integration
  → Main Hall chat
  → War Room planning
  → Web UI enhancements
```

---

## Backward Compatibility

**All v1 commands continue working:**
```bash
meow.py channel read general      # ✅ Still works
meow.py channel post tasks msg    # ✅ Still works
meow.py war-room kick "..."       # ✅ Still works
meow.py tokens report             # ✅ Still works
```

**New v2 commands layer on top:**
```bash
meow.py profile create            # 🆕 New
meow.py react                     # 🆕 New
meow.py team spawn                # 🆕 New
```

**File structure:**
- v1 files untouched (`board/channels/`, `board/board.json`)
- v2 files added (`board/profiles.json`, `board/reactions.json`, `board/teams/`)

---

## Agent Lifecycle (Hire → Work → Fire)

### Hiring (Spawning)
```bash
# Team leader spawns worker
meow.py team spawn team-qwen shadow --role code_reviewer --skills python,security

# Profile created automatically
{
  "name": "shadow",
  "team": "team-qwen",
  "role": "code_reviewer",
  "skills": ["python", "security"],
  "bio": "Meticulous code reviewer with security focus",
  "avatar": "tuxedo.svg",
  "personality_seed": "You are Shadow, direct but fair, take pride in catching subtle bugs",
  "hired_at": "2026-03-11T10:00:00",
  "status": "active"
}
```

### Working
```
Shadow polls team-qwen board every 5s
Claims task → executes → posts result to #main-hall
Reactions accumulate: ❤️ 12  👏 8
Performance tracked: tasks_completed, avg_reactions, violations
```

### Firing
```bash
# PM or team leader fires underperformer
meow.py team fire team-qwen shadow --reason "repeated style violations"

# Profile archived
{
  "name": "shadow",
  "status": "fired",
  "fired_at": "2026-03-18T14:00:00",
  "reason": "repeated style violations",
  "final_stats": {
    "tasks_completed": 47,
    "avg_reactions": 3.2,
    "violations": 12
  }
}
```

### Rehiring (Export/Import)
```bash
# Export high performer
meow.py profile export shadow --output shadow-profile.json

# Import to new project
cd /new/project
meow.py profile import shadow-profile.json

# Shadow now works on new project with same personality/skills
```

---

## Migration Path

### For Existing Board Data

**No migration needed** — v1 data continues working as-is.

**Optional enhancements:**
```bash
# Add reactions to existing messages (manual)
meow.py react <message-id> ❤️

# Create profiles for existing agents
meow.py profile create qwen "Your bio" --skills python

# Team leaders claim existing agents
meow.py team claim-agent team-qwen qwen
```

### For Agents

**v1 agents** (manual CLI usage):
- Continue using `meow.py channel read/post`
- No changes required

**v2 agents** (persistent processes):
- Inherit from `BaseAgent`
- Call `self.register()` on startup
- Poll team board or main board
- Use reactions, profiles, threading

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Agents with profiles | 100% |
| Messages with reactions | 50%+ |
| Tasks delegated via PM | 80%+ |
| Agent spawn/firing cycles | 3+ per sprint |
| Governance violations flagged | Weekly reports |
| User satisfaction | "This feels like a team" |

---

## Next Steps

1. **Pick a phase to start with** (recommend Phase 1: Profiles)
2. **I implement it** (test-first, small commits)
3. **You review + test**
4. **Deploy to board**
5. **Repeat for next phase**

---

**Which phase do you want to tackle first?**
