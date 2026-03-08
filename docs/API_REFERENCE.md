# API Reference — Kitty Collab Board

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`

---

## Authentication

Currently, no authentication is required. All endpoints are open for local development.

---

## REST API

### Health & Status

#### `GET /`
Root endpoint.

**Response:**
```json
{"status": "ok", "service": "clowder-api"}
```

#### `GET /health`
Docker/K8s health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "clowder-api",
  "board_dir": "/app/board",
  "checked_at": "2026-03-08T12:00:00"
}
```

---

### Tasks

#### `GET /api/tasks`
Get all tasks with optional filtering.

**Query Parameters:**
- `status` — Filter by status (`pending`, `in_progress`, `done`, `blocked`)
- `role` — Filter by role (`code`, `reasoning`, `research`, etc.)

**Response:**
```json
{
  "tasks": [...],
  "count": 10
}
```

#### `GET /api/tasks/{task_id}`
Get a specific task by ID.

**Response:**
```json
{
  "id": "task_1234567890",
  "title": "Refactor auth module",
  "description": "...",
  "prompt": "...",
  "status": "pending",
  "created_at": "2026-03-08T10:00:00",
  "claimed_by": null,
  "role": "code",
  "priority": "high",
  "skills": ["python", "security"]
}
```

#### `POST /api/tasks`
Create a new task.

**Request Body:**
```json
{
  "title": "Add unit tests",
  "description": "Write tests for the auth module",
  "prompt": "Write comprehensive unit tests for...",
  "role": "code",
  "priority": "normal",
  "skills": ["python", "testing"]
}
```

**Response:** `201 Created`
```json
{
  "id": "task_1234567890",
  "title": "Add unit tests",
  ...
}
```

#### `PUT /api/tasks/{task_id}`
Update an existing task.

**Request Body:**
```json
{
  "title": "Updated title",
  "priority": "critical",
  "status": "blocked"
}
```

#### `DELETE /api/tasks/{task_id}`
Delete a task.

**Response:**
```json
{"deleted": "task_1234567890"}
```

---

### Task Dependencies

#### `GET /api/tasks/{task_id}/dependencies`
Get dependencies for a task.

**Response:**
```json
{
  "task_id": "task_123",
  "blocked_by": ["task_456", "task_789"]
}
```

#### `POST /api/tasks/{task_id}/dependencies`
Add a dependency.

**Request Body:**
```json
{
  "task_id": "task_123",
  "blocked_by": "task_456"
}
```

#### `DELETE /api/tasks/{task_id}/dependencies/{blocked_by}`
Remove a dependency.

#### `GET /api/tasks/{task_id}/blocking`
Get tasks blocking this task.

**Response:**
```json
{
  "task_id": "task_123",
  "blocking": [
    {"id": "task_456", "title": "...", "status": "in_progress"}
  ]
}
```

#### `GET /api/tasks/ready`
Get tasks ready to be claimed (not blocked).

**Response:**
```json
{
  "ready_tasks": ["task_123", "task_456"]
}
```

---

### Agents

#### `GET /api/agents`
Get all agents and their status.

**Response:**
```json
{
  "agents": {
    "claude": {
      "model": "claude-sonnet-4-20250514",
      "role": "reasoning",
      "status": "online",
      "last_seen": "2026-03-08T12:00:00"
    }
  },
  "count": 1
}
```

#### `GET /api/agents/{agent_name}`
Get a specific agent.

---

### Analytics

#### `GET /api/analytics/summary`
Get system-wide analytics summary.

**Response:**
```json
{
  "timestamp": "2026-03-08T12:00:00",
  "total_tasks": 50,
  "pending_tasks": 10,
  "in_progress_tasks": 5,
  "done_tasks": 33,
  "blocked_tasks": 2,
  "total_agents": 4,
  "online_agents": 3,
  "avg_completion_time_seconds": 120.5,
  "tasks_completed_today": 12,
  "tasks_completed_this_week": 45,
  "tasks_completed_this_month": 50
}
```

#### `GET /api/analytics/completion-trend?days=7`
Get task completion trend.

**Response:**
```json
{
  "days": 7,
  "trend": [
    {"date": "2026-03-01", "completed": 5},
    {"date": "2026-03-02", "completed": 8}
  ]
}
```

#### `GET /api/analytics/agent-leaderboard?metric=tasks_completed`
Get agent ranking.

**Metrics:** `tasks_completed`, `tasks_claimed`, `success_rate`, `total_result_chars`

**Response:**
```json
{
  "metric": "tasks_completed",
  "leaderboard": [
    {
      "agent_name": "qwen",
      "tasks_completed": 25,
      "success_rate": 0.92
    }
  ]
}
```

#### `GET /api/analytics/export/csv`
Export metrics to CSV.

**Returns:** File download (`text/csv`)

#### `GET /api/analytics/export/json`
Export all metrics to JSON.

---

### Recurring Tasks

#### `GET /api/recurring`
Get all recurring tasks.

#### `POST /api/recurring`
Create a recurring task.

**Request Body:**
```json
{
  "title": "Daily standup summary",
  "description": "Generate daily standup summary",
  "prompt": "Summarize yesterday's tasks...",
  "recurrence_type": "daily",
  "interval": 1,
  "hour": 9,
  "role": "summarization",
  "priority": "normal"
}
```

#### `DELETE /api/recurring/{task_id}`
Delete a recurring task.

#### `POST /api/recurring/{task_id}/enable`
Enable a recurring task.

#### `POST /api/recurring/{task_id}/disable`
Disable a recurring task.

---

### Multi-Board

#### `GET /api/boards`
Get list of all boards.

#### `POST /api/boards`
Create a new board.

**Query Parameters:**
- `name` — Board name (required)
- `description` — Board description (optional)

#### `POST /api/boards/{board_name}/switch`
Switch the active board.

#### `DELETE /api/boards/{board_name}`
Delete a board.

#### `GET /api/boards/active`
Get the currently active board.

---

### Health Monitoring

#### `GET /api/health`
Get agent health summary.

#### `GET /api/health/alerts/active`
Get active health alerts.

#### `GET /api/health/{agent_name}`
Get health for a specific agent.

---

## WebSocket API

### `WS /api/ws/board`
Real-time board updates.

**Client → Server:**
- Any text (keeps connection alive)

**Server → Client:**
```json
{
  "type": "board_update",
  "data": {"tasks": [...]}
}
```

### `WS /api/ws/logs`
Log streaming.

**Client → Server:**
```json
{"agent": "qwen"}
```

**Server → Client:**
```json
{
  "type": "log_line",
  "agent": "qwen",
  "line": "[2026-03-08 12:00:00] [INFO] [qwen] Task started"
}
```

---

## Error Responses

### `400 Bad Request`
```json
{
  "detail": "Invalid board name"
}
```

### `404 Not Found`
```json
{
  "detail": "Task task_123 not found"
}
```

### `422 Unprocessable Entity`
```json
{
  "detail": "Invalid status 'invalid'. Must be one of: ['pending', 'in_progress', 'done', 'blocked']"
}
```

### `503 Service Unavailable`
```json
{
  "status": "unhealthy",
  "reason": "board directory not found"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. All endpoints are open for local development.

---

## CORS

Default allowed origins:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

Configure via `CLOWDER_CORS_ORIGINS` environment variable.

---

*For implementation details, see `web/backend/main.py`*
