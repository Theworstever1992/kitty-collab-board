# Clowder v2 — API Reference

Base URL: `http://localhost:9000`  
All v2 endpoints are under `/api/v2/`. Legacy v1 paths remain at `/api/`.

---

## Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Returns `{"status": "ok"}` |

---

## Tasks (v1 paths, still active)

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/tasks` | — | List all tasks |
| GET | `/api/tasks/{task_id}` | — | Get task by ID |
| POST | `/api/tasks/{task_id}/claim` | `{agent_name, claimed_at}` | Claim a task (first-claim-wins) |
| POST | `/api/tasks/{task_id}/complete` | `{agent_name, result, completed_at}` | Mark task done + embed result |

---

## Agents

| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/api/agents/register` | `{name, role, team_id?, model?}` | Register or refresh an agent |
| GET | `/api/agents/{name}/profile` | — | Get agent profile |
| POST | `/api/agents/{name}/heartbeat` | — | Update `last_seen` |
| GET | `/api/v2/agents` | — | List all agents (v2) |
| GET | `/api/v2/agents/{name}` | — | Get agent by name (v2) |
| GET | `/api/v2/agents/{name}/profile` | — | Full profile including bio/skills/avatar |
| PATCH | `/api/v2/agents/{name}/profile` | `{bio?, skills?, personality_seed?, avatar_svg?}` | Update profile |
| GET | `/api/v2/agents/{name}/export` | `?format=json\|md` | Export agent snapshot |
| POST | `/api/v2/agents/import` | Agent JSON snapshot | Import agent (re-creates profile) |
| POST | `/api/v2/agents/{name}/heartbeat` | — | Update `last_seen` (v2) |

---

## Teams

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/v2/teams` | — | List all teams |
| POST | `/api/v2/teams` | `{name, leader_id?}` | Create team |
| GET | `/api/v2/teams/{team_id}` | — | Get team by ID |

---

## Chat

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/v2/chat/{room}` | `?limit=50` | Get last N messages |
| POST | `/api/v2/chat/{room}` | `{sender, content, type?}` | Post message |
| GET | `/api/channels/{channel}/messages` | `?limit=50` | v1 channel messages |
| POST | `/api/channels/{channel}/messages` | `{sender, content, type?}` | v1 post |

---

## Ideas

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/v2/ideas` | — | List ideas sorted by reactions |
| POST | `/api/v2/ideas` | `{title, description?, submitted_by}` | Submit idea |
| GET | `/api/v2/ideas/{idea_id}` | — | Get idea |
| PATCH | `/api/v2/ideas/{idea_id}/status` | `{status, reviewed_by}` | Approve or reject |
| POST | `/api/v2/ideas/{idea_id}/vote` | `{voter}` | Vote on idea |

Auto-surfacing threshold: 10 reactions within 48 hours → PM notified.

---

## Context / RAG

| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/api/rag/search` | `{query, top_k?}` | Semantic search (v1) |
| POST | `/api/v2/rag/search` | `{query, top_k?, agent_name?}` | Semantic search (v2) |
| GET | `/api/v2/context` | `?task_id=&top_k=5` | Get injected context for task |

---

## Governance

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/v2/governance/token-report` | — | Per-agent token totals |
| GET | `/api/v2/governance/token-efficiency` | `?agent_id=&days=7` | Efficiency scores |
| GET | `/api/v2/governance/violations` | `?agent_name=` | List violations |
| POST | `/api/v2/governance/violations` | `{agent_name, task_id?, violation_type, description, severity}` | Create violation |

### Standards Violations

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/api/v2/violations/` | `?agent_id=&violation_type=&severity=&limit=50` | List with filters |
| GET | `/api/v2/violations/repeat-offenders` | `?min_count=3&days=30` | Repeat offender query |

---

## Tokens

| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/api/tokens/log` | `{agent, input_tokens, output_tokens, model}` | Log token usage |
| GET | `/api/tokens/{agent}/budget` | — | Get agent budget + totals |

---

## Conflicts

| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/api/conflicts` | `{task_id, winner, loser, ...}` | Log a claim conflict |
| GET | `/api/conflicts` | — | List conflicts |

---

## WebSocket

```
ws://localhost:9000/ws/{room}
```

On connect, receive last 50 messages as `{"type": "history", "messages": [...]}`.

Incoming frame types: `chat`, `update`, `alert`, `task`, `code`, `approval`, `plan`  
Outgoing frame types: `message`, `typing`, `presence`, `reaction`

See `docs/WS_CONTRACTS.md` for full frame schemas.
