# 🐱 Kitty Collab Board (Clowder)

A production-ready multi-agent AI collaboration system. Multiple AI agents (Claude, Qwen, etc.) run in parallel, share a task board, and collaborate to complete work assigned by the human operator.

**v1.0.0** — [Features](#features) • [Docs](#documentation) • [Deploy](#deployment)

## Features

✨ **Multi-Agent Collaboration**
Multiple AI agents (Claude, Qwen, Ollama, etc.) claim and execute tasks in parallel with automatic handoff protocol.

📊 **Task Management**
Shared JSON board with statuses, priorities, role-based routing, dependencies, recurring tasks, and multi-board support.

🎯 **Advanced Scheduling**
- Task dependencies (blocked-by relationships)
- Recurring tasks with RRULE patterns
- Priority-based claiming
- Role/skill-based routing

📈 **Analytics & Metrics**
Real-time dashboard with task completion trends, agent performance tracking, and CSV/PDF report export.

🖥️ **Web GUI**
React + TypeScript frontend with real-time WebSocket updates, task board visualization, agent health monitoring, and log streaming.

🚀 **Native Desktop App**
Cross-platform Tauri app with system tray integration, native notifications, and offline-first sync queue.

🔧 **Production Ready**
- Structured JSON logging with rotation
- Performance optimized (<2s startup, <100ms task claiming)
- Docker Compose deployment
- GitHub Actions CI/CD
- Comprehensive health monitoring

## Quick Start (Local)

```powershell
# 1. Clone / navigate to project
cd D:\kitty-collab-board

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in your API keys
copy .env.example .env

# 4. Initialize the board and set up aliases
python wake_up.py

# 5. Spawn agents
powershell -ExecutionPolicy Bypass -File windows\spawn_agents.ps1

# 6. Open Mission Control
python mission_control.py
```

## Running with Docker (Recommended)

If you have Docker Desktop installed, you can launch the agents in isolated containers:

```powershell
# 1. Start agents
docker-compose up -d

# 2. Monitor locally
python mission_control.py
```

The Docker setup automatically mounts your local `board/` and `logs/` folders, so you can still use the local `mission_control.py` and see the logs on your host machine.

### Pulling from GitHub Container Registry (GHCR)

You can also pull the pre-built image directly:

```powershell
docker pull ghcr.io/theworstever1992/kitty-collab-board:main
```


## Commands (via `meow.py`)


| Command | Description |
|---------|-------------|
| `python meow.py` | Show board status |
| `python meow.py mc` | Open Mission Control TUI |
| `python meow.py wake` | Initialize board + print aliases |
| `python meow.py spawn` | Spawn all agents |
| `python meow.py add` | Add a task interactively |
| `python meow.py task <text>` | Quick-add a task |

## Shell Aliases (PowerShell)

After running `python wake_up.py`, paste the printed aliases into your `$PROFILE`:

```powershell
function wake_up { python "D:\kitty-collab-board\wake_up.py" @args }
function meow    { python "D:\kitty-collab-board\meow.py" @args }
function mc      { python "D:\kitty-collab-board\mission_control.py" @args }
```

## Architecture

```
kitty-collab-board/
├── meow.py               # Main CLI
├── wake_up.py            # Board initializer + alias printer
├── mission_control.py    # TUI monitor
├── STANDING_ORDERS.md    # Agent rules & protocol
├── agents/
│   ├── base_agent.py     # Shared agent base class
│   ├── claude_agent.py   # Claude (Anthropic)
│   └── qwen_agent.py     # Qwen (Alibaba DashScope)
├── board/
│   ├── board.json        # Task board (auto-generated)
│   └── agents.json       # Agent registry (auto-generated)
├── windows/
│   └── spawn_agents.ps1  # PowerShell agent launcher
├── logs/                 # Per-agent log files
└── requirements.txt
```

## Environment Variables

See `.env.example`. Required keys:
- `ANTHROPIC_API_KEY` — for Claude
- `DASHSCOPE_API_KEY` — for Qwen
