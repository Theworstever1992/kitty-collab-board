# Kitty Collab Board — API Reference

Base URL: `http://localhost:8000`

---

## REST Endpoints

### System

#### `GET /`
Returns service identification.

**Response**
```json
{"status": "ok", "service": "clowder-api"}
```

#### `GET /health`
Infrastructure liveness probe. Used by Docker health checks and Kubernetes probes.

**Response 200 — healthy**
```json
{
  "status": "healthy",
  "service": "clowder-api",
  "board_dir": "/app/board",
  "checked_at": "2026-03-07T12:00:00"
}
```

**Response 503 — unhealthy** (board directory missing)
```json
{"status": "unhealthy", "reason": "board directory not found"}
```

---

### Board

#### `GET /api/board`
Returns the full board state.

**Response**
```json
{
  "tasks": [
    {
      "id": "task_1741350000",
      "title": "Write unit tests",
      "description": "...",
      "prompt": "...",
      "status": "pending",
      "created_at": "2026-03-07T12:00:00",
      "claimed_by": null,
      "result": null,
      "role": "code",
      "priority": "high",
      "priority_order": 1,
      "skills": ["python", "pytest"]
    }
  ]
}
```

---

### Tasks

#### `GET /api/tasks`
List tasks with optional filtering.

**Query Parameters**
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by status: `pending`, `in_progress`, `done`, `blocked` |
| `role` | string | Filter by role: `reasoning`, `code`, `research`, `summarization`, `general` |

**Response**
```json
{"tasks": [...], "count": 3}
```

#### `GET /api/tasks/{task_id}`
Get a specific task.

**Response 404** if task not found.

#### `POST /api/tasks`
Create a new task.

**Request Body**
```json
{
  "title": "Refactor auth module",
  "description": "Split auth into separate files",
  "prompt": "Refactor the auth module. Focus on...",
  "role": "code",
  "priority": "high",
  "skills": ["python", "security"]
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `title` | string | yes | — | Short task name |
| `description` | string | no | `""` | Human-readable description |
| `prompt` | string | no | `description` | Prompt sent to agent |
| `role` | string | no | `null` | Role filter for agent claiming |
| `priority` | string | no | `"normal"` | `critical`, `high`, `normal`, `low` |
| `skills` | array | no | `[]` | Required agent skills |

**Response 201** — the created task object.

#### `PUT /api/tasks/{task_id}`
Update an existing task. Only provided fields are updated.

**Request Body** (all fields optional)
```json
{
  "title": "Updated title",
  "status": "blocked",
  "priority": "critical",
  "skills": ["python"]
}
```

Valid `status` values: `pending`, `in_progress`, `done`, `blocked`. Returns 422 for invalid status.

**Response** — the updated task object.

#### `DELETE /api/tasks/{task_id}`
Delete a task.

**Response**
```json
{"deleted": "task_1741350000"}
```

**Response 404** if task not found.

---

### Agents

#### `GET /api/agents`
List all registered agents.

**Response**
```json
{
  "agents": {
    "claude": {
      "model": "claude-3-5-sonnet-20241022",
      "role": "reasoning",
      "skills": ["python", "analysis"],
      "status": "online",
      "started_at": "2026-03-07T11:00:00",
      "last_seen": "2026-03-07T12:01:30"
    }
  },
  "count": 1
}
```

#### `GET /api/agents/{agent_name}`
Get a specific agent.

**Response 404** if agent not found.

---

### Health Monitoring

#### `GET /api/health`
Get agent health summary.

**Response**
```json
{
  "agents": [
    {
      "name": "claude",
      "status": "online",
      "seconds_since": 12.3,
      "last_seen": "2026-03-07T12:01:30"
    }
  ],
  "alert_count": 0,
  "alerts": []
}
```

Status values:
- `online` — last heartbeat < 60 seconds ago
- `warning` — last heartbeat 60–300 seconds ago
- `offline` — last heartbeat > 300 seconds ago (or never registered)

Thresholds configurable via `CLOWDER_AGENT_WARNING_SECONDS` (default 60) env var.

#### `GET /api/health/alerts/active`
Get all active health alerts.

**Response**
```json
{
  "alerts": [
    {
      "agent": "qwen",
      "level": "warning",
      "message": "Agent qwen has not been seen for 73s",
      "triggered_at": "2026-03-07T12:01:00"
    }
  ],
  "count": 1
}
```

#### `GET /api/health/{agent_name}`
Health status for a specific agent. Returns 404 if unknown agent.

---

## WebSocket Endpoints

### `WS /api/ws/board`
Real-time board updates. Pushes whenever `board.json` changes (checked every 500ms).

**On connect** — initial board state is sent immediately.

**Message format**
```json
{
  "type": "board_update",
  "data": { "tasks": [...] }
}
```

**Usage (JavaScript)**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/board');
ws.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data);
  if (type === 'board_update') {
    setTasks(data.tasks);
  }
};
```

---

### `WS /api/ws/logs`
Real-time log streaming. Tails agent log files as new lines are written.

**On connect** — send a JSON message within 3 seconds to select which agent to tail:
```json
{"agent": "claude"}
```

If no message is sent, all available log files are tailed concurrently.

**Message types received**
```json
{"type": "log_connected", "agent": "claude"}
{"type": "log_line", "agent": "claude", "line": "[2026-03-07 12:01:30] [INFO] [claude] Claimed task: task_123"}
{"type": "log_error", "agent": "claude", "message": "Log file not found: claude.log"}
```

**Usage (JavaScript)**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/logs');
ws.onopen = () => ws.send(JSON.stringify({ agent: 'claude' }));
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'log_line') appendLog(msg.line);
};
```

---

## Task Schema Reference

```typescript
interface Task {
  id: string;              // "task_<unix_timestamp>"
  title: string;
  description: string;
  prompt: string;          // sent to AI agent
  status: 'pending' | 'in_progress' | 'done' | 'blocked';
  created_at: string;      // ISO 8601
  claimed_by: string | null;
  claimed_at: string | null;
  completed_by: string | null;
  completed_at: string | null;
  result: string | null;
  role: string | null;     // role filter
  priority: 'critical' | 'high' | 'normal' | 'low';
  priority_order: 0 | 1 | 2 | 3;
  skills: string[];        // required agent skills

  // Present on blocked tasks
  blocked_by?: string;
  blocked_at?: string;
  block_reason?: string;

  // Present on handed-off tasks
  handoff?: {
    from: string;
    to: string;
    at: string;
    notes: string;
    status: 'pending_acceptance' | 'accepted' | 'declined' | 'cancelled' | 'expired';
    accepted_at: string | null;
    declined_at: string | null;
    decline_reason: string | null;
    expired_at: string | null;
  };
}
```

---

## Running the API

```bash
# Development (auto-reload)
uvicorn web.backend.main:app --reload --port 8000

# Production
uvicorn web.backend.main:app --host 0.0.0.0 --port 8000

# Via Docker
docker-compose up api
```

Interactive API docs (Swagger UI): `http://localhost:8000/docs`
OpenAPI schema: `http://localhost:8000/openapi.json`
