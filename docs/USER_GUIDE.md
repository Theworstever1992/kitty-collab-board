# Kitty Collab Board — User Guide

Kitty Collab Board (codename **Clowder**) is a multi-agent AI collaboration system. Multiple AI agents run as independent processes, poll a shared task board, claim and complete tasks, and report results. You manage everything through `meow.py`.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and fill in your API keys
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and DASHSCOPE_API_KEY

# 3. Initialize the board
python wake_up.py

# 4. Add your first task
python meow.py task "Summarize the README file"

# 5. Start an agent
python agents/claude_agent.py
```

The agent will pick up the task, run it, and write the result back to the board.

---

## The `meow` Command

All operator actions go through `meow.py`:

```bash
python meow.py                       # show board status
python meow.py mc                    # open Mission Control (TUI)
python meow.py wake                  # re-initialize board
python meow.py add                   # add task interactively
python meow.py task "do something"   # quick-add a task
python meow.py spawn                 # spawn all agents (Linux/Mac)
python meow.py help                  # show all commands
```

### Quick-Add a Task

```bash
# Basic
python meow.py task "Write unit tests for board.py"

# With role filter (only agents with this role will claim it)
python meow.py task "Fix SQL injection" --role code

# With priority
python meow.py task "Deploy hotfix" --priority critical

# With required skills
python meow.py task "Build React component" --role code --skills python,react
```

### Interactive Add

`python meow.py add` prompts you for all task fields (title, description, prompt, role, priority, skills).

---

## Mission Control (TUI)

`python meow.py mc` opens Mission Control — a terminal dashboard showing tasks and agents.

### Navigation

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate task list |
| `Enter` | View full task result |
| `r` | Refresh |
| `a` | Add a new task |
| `h` | Initiate a handoff |
| `A` | Archive done tasks |
| `q` | Quit |

### Status View

`python meow.py` (no arguments) prints a quick status summary: task counts by status and agent heartbeat times.

---

## Task Lifecycle

```
pending → in_progress → done
                     ↘ blocked
```

- **pending** — task is on the board, waiting to be claimed
- **in_progress** — an agent has claimed it and is working
- **done** — agent completed it; `result` field contains the output
- **blocked** — agent hit an error; `block_reason` explains why

---

## Task Priorities

Tasks are sorted by priority before agents claim them:

| Priority | Typical use |
|----------|-------------|
| `critical` | Production incidents, urgent fixes |
| `high` | Important features, blocking bugs |
| `normal` | Standard work (default) |
| `low` | Nice-to-have, background work |

```bash
python meow.py task "Fix login crash" --priority critical
```

---

## Role-Based Routing

Agents have roles and only claim tasks matching their role. Tasks without a role can be claimed by any agent.

Available roles:
- `reasoning` — analysis, planning, decision-making
- `code` — writing and reviewing code
- `research` — web research, information gathering
- `summarization` — condensing documents or results
- `general` — catch-all (unclaimed tasks default here)

```bash
# Only the 'code' role agent will pick this up
python meow.py task "Implement OAuth flow" --role code
```

---

## Skills-Based Routing

For finer-grained routing, tasks can declare required skills. An agent must have **all** listed skills to claim a task.

```bash
# Only an agent with both 'python' and 'react' skills can claim this
python meow.py task "Build dashboard widget" --skills python,react
```

Skills are lowercase strings — whatever you and your agents agree on.

---

## Task Templates

Save common task patterns as templates to reuse them quickly.

```bash
# Save a template
python meow.py template save bug-fix
#   Description: Fix a bug in the codebase
#   Role: code
#   Priority: high
#   Skills: python
#   Prompt template: Fix the bug in {file}: {description}

# List templates
python meow.py template list

# Create a task from a template (will prompt for placeholders)
python meow.py template use bug-fix
#   file: auth.py
#   description: null pointer when user has no email
#   Task title: Fix null email bug

# Delete a template
python meow.py template delete bug-fix
```

Templates are stored in `board/templates.json`.

---

## Handoff Protocol

An agent can hand off a task to another agent when it's stuck or the other agent is better suited.

From Mission Control (`meow mc`), press `h` to initiate a handoff. You specify:
- Target agent name
- Notes for the receiving agent

The target agent will see a pending handoff on its next poll and can accept or decline. Handoffs expire after 10 minutes if not responded to.

---

## Archiving Done Tasks

Done tasks accumulate over time. Archive them to keep the board clean:

```bash
# Archive all done tasks (from CLI)
python mission_control.py archive

# Or press 'A' in Mission Control TUI
```

Archived tasks move to `board/archive.json` with an `archived_at` timestamp.

---

## Web UI

Start the API and frontend for a browser-based view:

```bash
# Start API
uvicorn web.backend.main:app --reload

# Start frontend (in a separate terminal)
cd web/frontend && npm run dev
```

Open `http://localhost:3000` to see the board, agent health, and live logs.

---

## Viewing Agent Logs

Logs are written to `logs/<agent_name>.log`. View them directly:

```bash
tail -f logs/claude.log
tail -f logs/qwen.log
```

Or use the web UI's log streaming panel (connects via WebSocket).

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | required | Anthropic API key for Claude agents |
| `DASHSCOPE_API_KEY` | required | DashScope key for Qwen agents |
| `CLOWDER_BOARD_DIR` | `./board` | Path to board directory |
| `CLOWDER_LOG_DIR` | `./logs` | Path to log directory |
| `CLOWDER_AGENT_WARNING_SECONDS` | `60` | Seconds before agent is marked "warning" |

---

## Docker

Run everything in containers:

```bash
docker-compose up -d          # start API + all agents
docker-compose logs -f        # stream all logs
docker-compose down           # stop everything
```

The `board/` and `logs/` directories are mounted from your host, so you can still run `meow.py` locally while agents run in containers.

---

## Troubleshooting

**Agent not picking up tasks**
- Check that the agent is running: `python meow.py` shows last-seen times
- Check that the task's role matches the agent's role
- Check that the agent has the required skills

**Board file corrupted**
```bash
python -c "import json; json.load(open('board/board.json'))"
```
If this fails, restore from `board/archive.json` or re-initialize with `python wake_up.py`.

**API won't start**
- Check port 8000 is free: `lsof -i :8000`
- Check `board/` exists: `python wake_up.py`

**Handoff not working**
- Target agent must be online (last_seen < 5 minutes)
- Handoffs expire after 10 minutes if not accepted
