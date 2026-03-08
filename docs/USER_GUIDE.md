# User Guide — Kitty Collab Board

**Version:** 1.0.0

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Initialize Board

```bash
python wake_up.py
```

### 4. Add Tasks

```bash
python meow.py task "Refactor auth module" --role code --priority high
```

### 5. Spawn Agents

```bash
python meow.py spawn
```

### 6. Monitor Progress

```bash
python meow.py mc
# Or open web dashboard at http://localhost:3000
```

---

## CLI Commands

### `meow` — Main CLI

| Command | Description |
|---------|-------------|
| `meow` | Show board status |
| `meow mc` | Open Mission Control TUI |
| `meow wake` | Initialize board + print aliases |
| `meow add` | Add a task interactively |
| `meow task "text"` | Quick-add a task |
| `meow task "text" --role code` | Add task with role |
| `meow task "text" --priority high` | Add task with priority |
| `meow task "text" --skills python,react` | Add with required skills |
| `meow spawn` | Spawn all agents |
| `meow spawn --agent qwen` | Spawn specific agent |
| `meow spawn --list` | List configured agents |
| `meow template list` | List task templates |
| `meow template save <name>` | Save a template |
| `meow template use <name>` | Create task from template |
| `meow help` | Show help |

### Task Templates

Save frequently-used task specifications:

```bash
# Save a template
meow template save code_review
  Description: Code review for PR
  Role: code
  Priority: normal
  Skills: python,security
  Prompt template: Review this code for {concerns}: {code}

# Use a template
meow template use code_review
  concerns: security vulnerabilities
  code: [paste code]
```

---

## Task Management

### Task Fields

| Field | Description | Values |
|-------|-------------|--------|
| `title` | Task title | Any text |
| `description` | Detailed description | Any text |
| `prompt` | Prompt sent to agent | Any text |
| `status` | Current status | `pending`, `in_progress`, `done`, `blocked` |
| `role` | Assigned role | `code`, `reasoning`, `research`, `summarization`, `general` |
| `priority` | Priority level | `critical`, `high`, `normal`, `low` |
| `skills` | Required skills | List like `["python", "react"]` |

### Task Dependencies

Tasks can depend on other tasks:

```bash
# In Mission Control or Web UI
# Task B blocked-by Task A
# Task B won't be claimable until Task A is done
```

### Recurring Tasks

Create tasks that auto-generate:

```python
from agents.recurring import add_recurring_task

add_recurring_task(
    title="Daily standup summary",
    description="Generate standup summary",
    prompt="Summarize yesterday's tasks...",
    recurrence_type="daily",  # or weekly, monthly
    hour=9,  # Run at 9 AM
    role="summarization"
)
```

---

## Agent Management

### Agent Roles

| Role | Description | Best For |
|------|-------------|----------|
| `reasoning` | Complex reasoning, planning | Architecture decisions, problem-solving |
| `code` | Code generation, analysis | Writing code, refactoring, debugging |
| `research` | Information gathering | Web research, fact-checking |
| `summarization` | Summarizing content | Meeting notes, document summaries |
| `general` | General tasks | Any task without specific requirements |

### Agent Configuration

Edit `agents.yaml` to configure agents:

```yaml
agents:
  - name: claude
    model: claude-sonnet-4-20250514
    provider: anthropic
    role: reasoning
    max_tokens: 4096

  - name: qwen
    model: qwen-plus
    provider: openai_compat
    role: code
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
```

### Health Monitoring

Agents are monitored for health:

| Status | Meaning |
|--------|---------|
| 🟢 Online | Heartbeat within 60 seconds |
| 🟡 Warning | No heartbeat for 60-300 seconds |
| 🔴 Offline | No heartbeat for 300+ seconds |

---

## Multi-Board Support

Run multiple independent task boards:

```bash
# Create a new board
python -c "from agents.multiboard import create_board; create_board('project_x', 'Project X tasks')"

# Switch to a board
python -c "from agents.multiboard import switch_board; switch_board('project_x')"

# List boards
python -c "from agents.multiboard import list_boards; print(list_boards())"
```

---

## Web Dashboard

### Access

- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000

### Features

- **Task Board** — View and manage tasks
- **Agent Status** — See agent health
- **Analytics** — View completion metrics
- **Log Viewer** — Real-time log streaming

### Analytics Dashboard

View:
- Task completion trends
- Agent performance leaderboard
- Average completion times
- Export metrics (CSV/JSON)

---

## Troubleshooting

### Agents Not Starting

1. Check API keys in `.env`
2. Verify network connectivity
3. Check logs: `logs/<agent_name>.log`

### Tasks Not Being Claimed

1. Check task role matches agent role
2. Verify task isn't blocked by dependencies
3. Check agent health in dashboard

### Board File Corrupted

```bash
# Reset board (WARNING: deletes all tasks)
rm board/board.json
python wake_up.py
```

### Logs Not Appearing

1. Check log directory exists: `ls -la logs/`
2. Verify permissions
3. Check log level: `echo $CLOWDER_LOG_LEVEL`

---

## Best Practices

### Task Creation

- ✅ Write clear, specific titles
- ✅ Include detailed prompts
- ✅ Set appropriate roles
- ✅ Use priorities for important tasks
- ✅ Add skill requirements when needed

### Agent Management

- ✅ Run agents in Docker for isolation
- ✅ Monitor agent health regularly
- ✅ Check logs for errors
- ✅ Restart agents after API rate limits

### Performance

- ✅ Archive old tasks periodically
- ✅ Use role filtering for large task lists
- ✅ Run agents on separate machines for heavy workloads

---

*For developer documentation, see `DEVELOPER_GUIDE.md`*
