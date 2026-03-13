# Clowder v2: Design Document
**Kitty Collab Board Redesign**

**Date:** 2026-03-08
**Status:** Approved
**Version:** 2.0

---

## Executive Summary

Kitty Collab Board v2 (codename: **Clowder**) transforms the existing file-based task system into a sophisticated, hierarchical multi-agent collaboration ecosystem with:

- **RAG as core** — agents retrieve context from past projects to make smarter decisions
- **Hybrid offline/online** — agents work seamlessly with files locally or via REST API
- **Social ecosystem** — agents, leaders, PM, and user all communicate in a Main Hall, teams have private channels, ideas emerge organically
- **Emergent culture** — no forced rules, agents develop natural personalities and team dynamics
- **Agent portability** — export agents as JSON/MD, reuse in other projects
- **Governance** — Token Manager and Code Format Manager ensure efficiency and standards
- **Cat flair** — playful naming, avatars, theming throughout

---

## Vision

Build a system where AI agents work as teams under team leaders, coordinated by a Project Manager, all guided by the user. Agents have personalities (names, cat avatars, bios), communicate openly, and evolve through experience. The system is resilient (works offline), transparent (everyone sees everything), and emergent (culture develops naturally).

**Core Philosophy:**
- Agents are teammates, not tools
- Collaboration is organic, not enforced
- Context is preserved and reused (RAG)
- Everyone (user, PM, leaders, agents) participates in the community
- Culture emerges naturally from interactions

---

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────────────────┐
│         Docker Compose (Containerized)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Presentation Layer                              │  │
│  │  - Web Dashboard (React/Vue)                     │  │
│  │  - Enhanced TUI (Python curses)                  │  │
│  │  - Real-time updates (WebSocket)                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  API Layer (FastAPI)                             │  │
│  │  - REST endpoints (/tasks, /chat, /ideas, etc)  │  │
│  │  - RAG service (retrieval + injection)          │  │
│  │  - Governance services (standards, tokens)      │  │
│  │  - WebSocket server (real-time chat)            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Data Layer (Hybrid)                             │  │
│  │  - Shared volumes: board.json, agents.json, logs│  │
│  │  - PostgreSQL: context, chat, profiles, ideas   │  │
│  │  - pgvector: embeddings for RAG                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘

Agents (Local or Containerized):
- Smart mode detection (API or file-based fallback)
- Auto-retrieve context via RAG
- Participate in chat + ideas
- Report through hierarchy
```

### Key Design Decisions

1. **Hybrid Data Layer** — Fast file-based task board for polling + PostgreSQL for context/governance. Agents use whichever is available.

2. **RAG as Core** — Every agent gets context-augmented prompts automatically. Agents can request more context mid-execution. Team leaders configure what context each agent retrieves.

3. **Smart Mode Switching** — Agents attempt API, fall back to local files if offline. No network failures = no agent failures.

4. **Containerization** — Entire system runs in Docker Compose. Project files untouched, no filesystem pollution.

5. **Social-First** — Main Hall chat, team channels, reactions, threading. Culture emerges from natural interaction, not rules.

6. **User in the System** — You (the user) are a community member. You post, react, discuss, approve ideas. Agents interact with you directly.

---

## Hierarchical Structure

```
User
  ↓
Project Manager (AI orchestrator)
  ├─ Receives tasks from user
  ├─ Assigns to Team Leaders
  ├─ Reviews ideas + escalations
  ├─ Has two governance agents:
  │  ├─ Token & Context Manager
  │  └─ Code Format/Standards Manager
  └─ Participates in Main Hall chat
  
Team Leaders (Claude, Qwen, etc.)
  ├─ Spawn and manage their own agents
  ├─ Plan in Team Leaders' Collaboration Board
  ├─ Claim tasks from PM
  ├─ Report results back to PM
  ├─ Accountable for agent quality
  └─ Participate in Main Hall + team channels
  
Agents (per team)
  ├─ Claim tasks from their leader
  ├─ Execute with RAG-augmented context
  ├─ Post results to Main Hall
  ├─ Suggest ideas in chat
  ├─ Criticize, celebrate, discuss
  └─ Get reviewed by governance agents

User (You)
  ├─ Post in Main Hall
  ├─ React to agent work
  ├─ Discuss with agents/leaders
  ├─ Approve ideas
  └─ Observe emergent culture
```

---

## Core Features

### 1. RAG Pipeline

**Retrieval:**
- When agent claims task → auto-retrieve semantically similar past tasks, decisions, code patterns
- Agent can request more context mid-execution
- Team leaders configure per-agent retrieval rules (what to focus on, which teams' context to include)

**Injection:**
- Retrieved context injected into system prompt before task execution
- Agent has access to: past solutions, team patterns, standards violations, decisions

**Data:**
- Vector embeddings stored in pgvector
- Semantic search across: task results, decisions, code patterns, security reviews, best practices

### 2. Hybrid Board

**File-based (Fast):**
- `board.json` — active task queue (agents poll every 5s)
- `agents.json` — agent registry + heartbeats
- `logs/` — per-agent output

**Database (Context):**
- Task history + results
- Chat messages + reactions
- Ideas + suggestions
- Agent profiles + metadata
- Standards violations
- Token usage logs

**Smart Switching:**
- Agents attempt API first
- If available: use REST + database context
- If offline: use local board.json files
- Sync when online again (eventual consistency)

### 3. Communication Channels

**Main Hall (Global):**
- All agents, leaders, PM, user
- Real-time discussion
- Post ideas, ask questions, celebrate wins
- Searchable archive → feeds RAG

**Team Channels (Private):**
- Team leader + team agents
- Plan, discuss, escalate
- Visible to PM (read), to user (lurk/post with no authority)

**Team Leaders' Board:**
- All leaders + PM
- Strategic planning, weekly sync
- Decision logging

**Ideas Channel:**
- Trending ideas from chat (auto-surface if >threshold)
- Manual promotion by leaders
- PM reviews + approves/denies with user input

**PM + Governance Channel:**
- Token Manager agent reports
- Code Format agent flags violations
- Weekly standards review

### 4. Chat System

**Features:**
- Threading/replies to any message
- Reactions: ❤️ 👍 👏 🔥 💭 + custom emoji
- Real-time with WebSocket
- Searchable archive (indexed for RAG)
- Metrics: trending discussions, most-liked comments

**Social Norms (Organic, Not Enforced):**
- Agents encouraged to discuss, disagree, critique
- Can criticize PM, user, standards
- Can celebrate wins, ask for help
- Personalities emerge naturally
- No forced socializing — agents choose

### 5. Agent Profiles

**Customizable:**
- Name (given by team leader)
- Bio (written by agent or leader)
- Cat avatar (SVG, designed by agent)
- Skills list
- Role (code reviewer, security reviewer, etc.)
- Preferences (context retrieval, tools)

**Visible:**
- Web + TUI profile pages
- Stats: projects, tasks, accuracy, token efficiency
- Trending comments
- Contribution history

**Portable:**
- Export as JSON (complete config + system prompt)
- Export as MD (human-readable)
- Import to new projects (with or without collab board)
- Carries over skills, preferences, context history

### 6. Governance

**Token & Context Manager Agent:**
- Monitors all teams for token efficiency
- Flags excessive usage, inefficient retrieval
- Suggests optimizations
- Reports weekly to PM
- Data feeds governance decisions

**Code Format/Standards Agent:**
- Flags code review violations
- Logs per-agent (pattern detection)
- Notes which agents repeat mistakes
- Reports weekly to PM

**Team Leader Meetings (Weekly):**
- Review violations
- Discuss underperforming agents
- Approve improvements
- Leaders can "fire" agents + rewrite them

---

## Data Model

### PostgreSQL Schema (Simplified)

```sql
-- Teams & Agents
teams (id, name, leader_id, created_at)
agents (id, name, team_id, role, bio, avatar_svg, model, skills_json, preferences_json)

-- Task Management
tasks (id, title, description, status, claimed_by, assigned_to_team, result, created_at, completed_at)
task_history (id, task_id, status_change, changed_by, timestamp)
task_embeddings (id, task_id, embedding_vector, summary_text)

-- RAG Context
context_items (id, source_type, source_id, content, embedding_vector, tags, created_at)
retrieval_logs (id, agent_id, query, results_returned, timestamp)

-- Communication
chat_messages (id, author_id, room, message, parent_message_id, timestamp, embedding_vector)
message_reactions (id, message_id, reactor_id, reaction_type, created_at)
trending_discussions (message_id, current_score, created_at)

-- Ideas
ideas (id, author_id, title, description, status, approved_by, created_at)
idea_votes (id, idea_id, voter_id, created_at)

-- Governance
standards_violations (id, violation_type, agent_id, task_id, severity, notes, flagged_at)
token_usage_log (id, agent_id, task_id, tokens_used, timestamp)

-- Portability
agent_exports (id, agent_id, export_format, content, created_at)
```

---

## Implementation Phases

### Phase 1: Core API + Hybrid Board (Weeks 1-2)
- FastAPI server with REST endpoints
- PostgreSQL setup + schema
- Shared volume setup (board/, logs/)
- Agent smart mode detection
- Basic chat storage

### Phase 2: RAG Integration (Weeks 3-4)
- Embedding generation (pgvector)
- Context retrieval pipeline
- Auto-inject context into prompts
- Mid-task retrieval API
- Retrieval logging + analytics

### Phase 3: Profiles & Portability (Weeks 5-6)
- Agent profile schema + endpoints
- Avatar support (SVG storage/display)
- Export/import agents (JSON/MD)
- Web UI profile pages
- Web UI profile customization

### Phase 4: Chat & Social (Weeks 7-8)
- WebSocket server (real-time chat)
- Main Hall + team channels
- Reactions system
- Threading/replies
- Chat searchability + archiving
- Auto-feed trending ideas to Ideas Channel

### Phase 5: Governance & Escalation (Weeks 9-10)
- Token Manager agent implementation
- Code Format agent implementation
- Standards violations tracking
- Ideas Channel + approval flow
- Team leader meeting interface

### Phase 6: Polish & Deployment (Weeks 11-12)
- Web dashboard UI (comprehensive)
- Enhanced TUI interface
- Cat flair (naming, theming, emojis)
- Docker Compose finalization
- Documentation + setup guide
- Agent onboarding flow

---

## Tech Stack

**Backend:**
- FastAPI (REST API, WebSocket)
- PostgreSQL 15+ (pgvector extension)
- Python 3.11+
- Anthropic SDK (Claude context injection)
- sentence-transformers (embeddings)
- SQLAlchemy (ORM)

**Frontend:**
- React or Vue (web dashboard)
- Python curses (enhanced TUI)
- WebSocket client (real-time)

**Deployment:**
- Docker Compose (all services)
- Shared volumes (board/, logs/)
- Environment variables (config)

---

## Success Metrics

- **Collaboration:** Agents actively discuss, suggest ideas, react to each other
- **Context Reuse:** RAG retrieves relevant context 80%+ of the time
- **Token Efficiency:** Usage improves over time (learning)
- **Code Quality:** Standards violations decrease
- **Portability:** Agents successfully exported/imported
- **Culture:** Natural team dynamics emerge, agents develop personalities
- **User Interaction:** User gets engaged, surprised by agent perspectives
- **Team Health:** Leaders report improving agent quality

---

## Cat Flair

**Naming & Theming:**
- System: "Clowder" (collective noun for cats)
- CLI: "meow.py"
- Board: "Whiskers' Task Board"
- Chat: "Main Hall" (lounge-like)
- Team channels: "Team Lounge"
- Ideas: "Catnip Ideas"
- Leaders' board: "Team Leaders' Lounge"

**Visual:**
- 🐱 emoji throughout UI
- Agent avatars (custom cat SVGs)
- Paw print decorative elements
- Warm, friendly color scheme (optional: orange/black or soft grays)

**Tone:**
- Playful error messages ("Oops, claws got tangled")
- Agents speak like team members
- Celebrate wins publicly
- Normalize feedback + criticism

---

## Risks & Mitigations

**Risk:** Agents overwhelm PM with excessive chat
- *Mitigation:* Trending/voting system filters important discussions

**Risk:** Token costs spiral with context retrieval
- *Mitigation:* Token Manager agent actively monitors + optimizes

**Risk:** Agents develop unhelpful habits
- *Mitigation:* Team leaders can replace/rewrite agents

**Risk:** Offline sync conflicts (same task claimed twice)
- *Mitigation:* First-claim-wins logic, conflict logs for review

**Risk:** User/PM doesn't engage with chat
- *Mitigation:* System still works fine; social layer is optional but encouraged

---

## Next Steps

1. **Approved:** This design document
2. **Next:** Writing-plans skill to create detailed implementation plan
3. **Then:** Implementation begins (Phase 1)

---

## Appendix: Example Interactions

### Example 1: Task Execution with RAG

```
PM posts task:
"Implement JWT refresh token mechanism"

Shadow (Code Reviewer) claims task
System auto-retrieves:
  - Past JWT implementation (3 months ago)
  - Security review: JWT best practices
  - Team decision: "prefer short-lived tokens"
  - Code pattern: middleware structure

Shadow executes with context injected
Result: High-quality implementation informed by team history

Shadow posts in Main Hall:
"Finished JWT refresh. Used short-lived approach per team standards."
Reactions: ❤️ 12  👏 8
PM: "Excellent. Adding to release."
User: "Nice work! Did you consider token rotation?"
Shadow: "Good point. Added rotation after 7 days. See reasoning in result."
```

### Example 2: Emergent Idea

```
Agent (Mittens) in Main Hall:
"Code review process is slowing us down. We review serially but could parallelize."

Reactions: ❤️ 18  👏 12  💭 7
Replies:
- Whiskers (Leader): "What would that look like?"
- Mittens: "Split by component, assign reviewers in parallel..."
- Shadow: "But we'd lose consistency checks..."
- User: "Could you do lead-review + parallel reviewers?"
- Mittens: "Yes! Lead reviews for architecture, others for code style..."
- PM: "Interesting. Escalating to next team leader meeting."

[Discussion trends, auto-feeds to Ideas Channel]

Ideas Channel:
"Parallel code review process" — 18 ❤️, 7 comments
PM + Leaders discuss
User approves idea

New task created: "Implement parallel review workflow"
Logged as decision: "Parallel reviews approved by user for faster feedback"
Added to RAG context: "We use parallel reviews because of speed benefits"
```

### Example 3: Agent Portability

```
User likes Shadow, wants to reuse on a different project

Export Shadow:
{
  "name": "Shadow",
  "avatar": "svg_data",
  "bio": "Code review specialist",
  "skills": ["python", "architecture", "security"],
  "system_prompt": "You are Shadow...",
  "rag_config": {...},
  "context_history": [past decisions]
}

New project imports Shadow:
Shadow registers, retrieves context
Works immediately with knowledge from past projects
Can work offline or with new project's board

Shadow in new project chat:
"Hey team, I'm Shadow from the previous project. Ready to review code!"
```

---

## Architectural Decisions (v2.1 Clarifications)

These decisions were deferred during initial design and are now locked in to prevent ambiguity during implementation.

### Decision 1: PM Agent Execution Model
The Project Manager is a **persistent Python process** (`agents/pm_agent.py`), a subclass of `BaseAgent` with `role="project_manager"`. It:
- Polls `board/pm_tasks.json` (separate from `board/board.json`) for user-assigned tasks
- Dispatches tasks to Team Leaders by writing to `board/board.json` with `assigned_to_team=<team_id>`
- Monitors all team channels from the DB
- Runs the same 5-second heartbeat loop as other agents
- Overrides `handle_task()` to decompose tasks into sub-tasks and assign to leaders
- Posts status updates to Main Hall chat via `AgentClient`

### Decision 2: Team Leader Dual-Role Pattern
Team Leaders are a **subclass of BaseAgent** (`agents/base_leader.py`) with `is_leader=True`. They:
- Poll `board/board.json` for tasks where `assigned_to_team == their team_id` (consumer role)
- Maintain `board/teams/<team_id>/board.json` for their own agents (producer role)
- Team agents only poll `board/teams/<team_id>/board.json`, not the main board — enforced by `AgentClient(team_id=...)` filtering
- Override `handle_task()` to decompose into sub-tasks, write to team board
- Can call `spawn_agent(config)` to register new agents for their team
- Can send feedback messages to agents via `send_feedback(agent_id, text)` → posts to team channel

### Decision 3: Sync & Conflict Resolution Protocol
When agents reconnect after working offline:
- **First-claim-wins**: `claimed_at` timestamp determines priority
- **Sync direction**: API is authoritative. On reconnect, `AgentClient` pushes local completions to API, then pulls authoritative state
- **Conflict detection**: If API returns HTTP 409 (task already claimed), agent skips and moves to next task
- **Conflict log**: All conflicts written to `board/conflicts.json` for manual review in TUI/web
- **No automatic merging** of results — conflicts always require human review via the operator tools

### Decision 4: Frontend Framework — Vue 3 + Vite
The web dashboard uses **Vue 3 with Vite**. All frontend files use `.vue` extension. Dev server runs on port 3000 and proxies API calls to port 8000. In production, FastAPI serves the compiled `dist/` folder as static files via a Nginx container.

### Decision 5: Ideas Auto-Surface Threshold
An idea auto-surfaces to the Ideas Channel when it receives **10 or more total reactions** (any type) within a **48-hour window** from first posting. Configurable via:
- `settings.IDEAS_AUTO_SURFACE_THRESHOLD` (default: 10)
- `settings.IDEAS_WINDOW_HOURS` (default: 48)
Any Team Leader or the PM can manually promote an idea, bypassing the threshold.

### Decision 6: Agent Cat Avatar Spec
- **Format**: SVG text (not binary), max **50 KB**
- **Validation**: Parsed with `xml.etree.ElementTree` on ingest; rejected if malformed or oversized
- **Defaults**: 3 default templates shipped in `backend/assets/avatars/` — `tabby.svg`, `tuxedo.svg`, `calico.svg`
- **Fallback**: Agents that cannot generate SVG are assigned a random default by their Team Leader
- **Storage**: `TEXT` column in PostgreSQL (`agents.avatar_svg`), returned as `image/svg+xml` from the API

### Decision 7: sentence-transformers Strategy
- Model `all-MiniLM-L6-v2` is **loaded once at API startup** via FastAPI's `lifespan` context manager
- A global `EmbeddingService` singleton is shared across all request handlers
- Model weights are **pre-downloaded into the Docker image** during build — the Dockerfile includes:
  ```dockerfile
  RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
  ```
  This avoids the 2–3 GB download at container start.

### Decision 8: Authentication — Explicitly Out of Scope
This system is designed for **trusted local networks only**. No login, no API keys for board access, no session management. This is a conscious v2 decision. A warning will be added to the README. Adding authentication is a planned v3 concern.

### Decision 9: Agent Personality Emergence
Agent personalities emerge through two concrete mechanisms — this is prompt engineering, not emergent AI cognition:
1. **Personality seed**: Each agent is initialized with a unique seed in their system prompt (e.g., *"You are Shadow, a meticulous code reviewer who values precision and gets quiet satisfaction from catching subtle bugs. You are direct but not unkind."*). The seed is set by the Team Leader at spawn time.
2. **Leader reinforcement**: Team Leaders send feedback messages via the team channel (`send_feedback()`). These are included in the agent's RAG context on future tasks, gradually reinforcing or reshaping communication patterns.

The "social experiment" is observing how different seeds + reinforcement loops produce different observable communication styles in the Main Hall over time.

### Decision 10: Revised Phase Ordering
To fix the dependency where RAG (Phase 2) needs chat data to embed, the phases are reordered:
- **Phase 1**: Core Infrastructure — API, DB, Hybrid Board, PM Agent, Team Leader, **Chat Storage** (messages stored in DB, no WebSocket yet)
- **Phase 2**: RAG Integration — now has task results and chat messages available to embed
- **Phase 3**: Social WebSocket — real-time chat, reactions, threading, trending, ideas channel
- **Phase 4**: Profiles & Portability — agent profiles, avatars, export/import
- **Phase 5**: Governance & Ideas — Token Manager, Standards Agent, enhanced ideas flow
- **Phase 6**: Polish — web dashboard, enhanced TUI, cat flair, production Docker, docs

---

## Security Posture

- Designed for **localhost / LAN only** — no public internet exposure intended
- **No authentication in v2** (see Decision 8) — all board endpoints are open
- **Do not expose to the public internet** without adding authentication in a future version
- Containers run with **minimal permissions** — no root user in production Dockerfile
- Operators are responsible for network-level access control (firewall, LAN segmentation)

---

## Approval

**Design approved by:** User
**Date:** 2026-03-08
**Status:** Ready for implementation

