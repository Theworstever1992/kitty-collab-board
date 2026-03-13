# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Kitty Collab Board** (codename: **Clowder**) is a multi-agent AI collaboration system. Multiple AI agents (Claude, Qwen, etc.) run in parallel, poll a shared JSON task board, claim and complete tasks, and report results. A human operator manages the board via `meow.py` / `mission_control.py`.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # fill in API keys
python wake_up.py         # create board/ and logs/ dirs, print PowerShell aliases
```

### Required environment variables

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude agent |
| `DASHSCOPE_API_KEY` | Qwen agent (Alibaba DashScope) |
| `OPENAI_API_KEY` | Optional; not used by built-in agents |
| `CLOWDER_BOARD_DIR` | Override `board/` path (Docker / CI) |
| `CLOWDER_LOG_DIR` | Override `logs/` path (Docker / CI) |

## Common Commands

```bash
python meow.py                  # show board status (banner + dashboard)
python meow.py mc               # open Mission Control TUI (curses on Linux, simple on Windows)
python meow.py task "do thing"  # quick-add a task from the command line
python meow.py add              # add a task interactively
python meow.py wake             # re-initialize board + print PowerShell aliases
python meow.py spawn            # spawn agents via PowerShell (Windows only)
python meow.py help             # show all commands
python wake_up.py               # same as meow wake
```

Run a single agent directly:

```bash
python agents/claude_agent.py
python agents/qwen_agent.py
```

Stop all background agent jobs (PowerShell only):

```powershell
Get-Job | Stop-Job; Get-Job | Remove-Job
```

### Docker

```bash
docker compose up               # launch claude + qwen agents
docker compose up claude        # launch only the claude agent
docker compose down             # stop all containers
```

`board/` and `logs/` are mounted as volumes, so the host can read/write the board while agents run in containers.

## Architecture

### Directory Layout

```
kitty-collab-board/
├── agents/
│   ├── __init__.py          # empty package marker
│   ├── base_agent.py        # BaseAgent base class
│   ├── claude_agent.py      # Anthropic/Claude agent
│   └── qwen_agent.py        # Alibaba/Qwen agent
├── windows/
│   └── spawn_agents.ps1     # PowerShell agent launcher
├── board/                   # runtime only — created by wake_up.py
│   ├── board.json           # shared task list
│   └── agents.json          # agent registry
├── logs/                    # runtime only — one file per agent
├── meow.py                  # main CLI entry point
├── mission_control.py       # TUI dashboard + add_task()
├── wake_up.py               # board initializer
├── STANDING_ORDERS.md       # agent conduct rules
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

### Shared State (`board/`)

Both files use plain JSON with read-modify-write (no file locking).

#### `board/board.json`

```json
{
  "tasks": [
    {
      "id": "task_1700000000",
      "title": "Short title",
      "description": "Human-readable description",
      "prompt": "Text sent to the agent's LLM",
      "status": "pending",
      "created_at": "2026-01-01T00:00:00",
      "claimed_by": null,
      "claimed_at": null,
      "completed_by": null,
      "completed_at": null,
      "result": null
    }
  ]
}
```

Task status flow: `pending` → `in_progress` → `done` | `blocked`

#### `board/agents.json`

```json
{
  "claude": {
    "model": "claude-3-5-sonnet-20241022",
    "role": "reasoning",
    "status": "online",
    "started_at": "2026-01-01T00:00:00",
    "last_seen": "2026-01-01T00:05:00"
  }
}
```

Agent status values: `online`, `offline`, `idle`

### Agent Pattern

All agents inherit from `agents/base_agent.py:BaseAgent`.

**Base class responsibilities:**

| Method | Description |
|---|---|
| `register()` | Write entry to `agents.json` on startup |
| `deregister()` | Mark agent `offline` on shutdown |
| `get_tasks()` | Return list of `pending` tasks from `board.json` |
| `claim_task(id)` | Set task to `in_progress`, record `claimed_by`; returns `bool` |
| `complete_task(id, result)` | Set task to `done`, store result string |
| `log(msg, level)` | Print timestamped entry and append to `logs/<name>.log` |
| `_heartbeat()` | Update `last_seen` in `agents.json` |
| `run()` | Main loop: heartbeat → get tasks → claim first → `handle_task()` → complete; polls every **5 seconds** |

**Subclasses override only `handle_task(task: dict) -> str`.**

`task` keys available in `handle_task`: `id`, `title`, `description`, `prompt`, `status`, `claimed_by`, `created_at`.

> **Race condition note:** `claim_task` is not atomically locked. Under heavy concurrent load two agents may claim the same task. This is acceptable for low-throughput use; add file locking if needed.

### Agent Implementations

| File | Agent name | Model | Role | SDK |
|---|---|---|---|---|
| `agents/claude_agent.py` | `claude` | `claude-3-5-sonnet-20241022` | `reasoning` | `anthropic` |
| `agents/qwen_agent.py` | `qwen` | `qwen-plus` | `code` | `openai` (DashScope-compatible) |

`qwen_agent.py` points the OpenAI client at `https://dashscope.aliyuncs.com/compatible-mode/v1`.

Both agents use `max_tokens=2048` and send only the `task["prompt"]` field to their respective LLMs.

### Creating a New Agent

1. Create `agents/<name>_agent.py`.
2. Subclass `BaseAgent`; set `self.name`, `self.model`, `self.role` in `__init__`.
3. Implement `handle_task(self, task: dict) -> str`.
4. Add an entry to `windows/spawn_agents.ps1` for Windows spawning.
5. Add a service to `docker-compose.yml` for Docker deployment.

Minimal skeleton:

```python
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="myagent", model="my-model", role="general")

    def handle_task(self, task: dict) -> str:
        # call your LLM here
        return "result string"

if __name__ == "__main__":
    MyAgent().run()
```

### Operator Tools

| File | Purpose |
|---|---|
| `meow.py` | Thin CLI dispatcher; delegates to other modules |
| `mission_control.py` | `add_task()` function; curses TUI (Unix); simple print loop (Windows/fallback) |
| `wake_up.py` | Creates `board/` and `logs/` dirs; seeds empty JSON files; prints PowerShell alias commands |

`mission_control.py` can be imported directly to call `add_task(title, description, prompt)` without launching the TUI.

### Agent Protocol (`STANDING_ORDERS.md`)

All agents must:

1. Register on startup — write to `agents.json`.
2. Read the board before acting — never act on stale state.
3. Not duplicate claimed tasks — skip tasks already `in_progress`.
4. Log all significant actions via `self.log()`.
5. Flag blockers immediately — set task status to `blocked`.
6. Complete or hand off — never silently abandon a task.

### Deployment (Docker)

Each service in `docker-compose.yml` runs one agent, mounts `./board` and `./logs` as volumes, and restarts unless explicitly stopped. The `CLOWDER_BOARD_DIR` and `CLOWDER_LOG_DIR` environment variables point agents at the mounted paths.

## Security Notice

`meow.py` contains obfuscated code at lines 105–113 that base64-decodes, decompresses, and `exec()`s a compiled payload at import time. This code runs whenever `meow.py` is imported or executed. **Do not run or import `meow.py` on a production or sensitive machine until the obfuscated block has been reviewed and removed.** The rest of the codebase (agents, mission_control, wake_up) does not contain obfuscated code.

## Dependencies

```
anthropic>=0.20.0
openai>=1.0.0
rich>=13.0.0
python-dotenv>=1.0.0
```

`rich` is available but not actively used in the current codebase — it was likely added for future formatted output.
