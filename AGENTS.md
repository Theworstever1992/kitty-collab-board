# AGENTS.md — Kitty Collab Board (Clowder)

**Language:** English  
**Project:** Multi-agent AI collaboration system  
**Last Updated:** 2026-03-07

---

## Project Overview

**Kitty Collab Board** (codename: **Clowder**) is a multi-agent AI collaboration system where multiple AI agents (Claude, Qwen, Gemini, Llama, etc.) run as independent processes, share a JSON-based task board, and collaborate to complete work assigned by a human operator.

### Core Concept
- Agents poll a shared `board/board.json` file for pending tasks
- Agents claim tasks, execute them using their configured AI provider, and write results back
- Human operators manage the board via CLI (`meow.py`) or TUI (`mission_control.py`)
- Agents communicate only through the board — no direct agent-to-agent calls

### Architecture Highlights
- **File-based shared state:** JSON files in `board/` act as the central coordination point
- **Provider abstraction:** New AI models can be added via YAML configuration (no code changes)
- **File locking:** Uses `filelock` library for atomic board writes (prevents race conditions)
- **Cross-platform:** Works on Windows (PowerShell), Linux, and macOS

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.10+ |
| **AI SDKs** | `anthropic`, `openai`, `google-genai` |
| **Config** | YAML (`pyyaml`) |
| **Concurrency** | `filelock` for cross-platform file locking |
| **TUI** | `curses` (Unix) / simple print mode (Windows) |
| **Web UI** | FastAPI + WebSocket (planned), React + TypeScript (planned) |
| **Container** | Docker, docker-compose |
| **CI/CD** | GitHub Actions (publishes to GHCR) |

---

## Project Structure

```
kitty-collab-board/
├── meow.py                    # Main CLI entry point
├── wake_up.py                 # Initialize board, print shell aliases
├── mission_control.py         # TUI dashboard (curses on Unix, simple on Windows)
├── agents.yaml                # Agent team configuration (name, model, provider, role)
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Container orchestration
├── Dockerfile                 # Container image
│
├── agents/                    # Agent implementation
│   ├── base_agent.py          # BaseAgent class — all agents inherit from this
│   ├── generic_agent.py       # Config-driven agent (uses any provider)
│   ├── config.py              # YAML config loader + provider builder
│   ├── prompts.py             # Role-based system prompts
│   ├── claude_agent.py        # Legacy Claude agent (Anthropic)
│   ├── qwen_agent.py          # Legacy Qwen agent (DashScope)
│   └── providers/             # AI provider implementations
│       ├── base.py            # BaseProvider abstract class
│       ├── anthropic_provider.py
│       ├── openai_compat.py   # OpenAI-compatible (Qwen, Together, Groq, etc.)
│       ├── ollama.py          # Local models via Ollama
│       └── gemini.py          # Google Gemini
│
├── board/                     # Shared state (auto-generated)
│   ├── board.json             # Task list — agents poll, claim, complete here
│   └── agents.json            # Agent registry — agents register on startup
│
├── logs/                      # Per-agent log files (auto-generated)
│   └── {agent_name}.log
│
├── windows/                   # Windows-specific scripts
│   └── spawn_agents.ps1       # PowerShell agent launcher
│
├── sprint/                    # Sprint planning and task tracking
│   ├── SPRINT_1.md            # Completed: Universal Agent System
│   ├── SPRINT_2.md            # Active: Smart Routing, Testing, TUI
│   ├── SPRINT_3.md            # Active: Web GUI, Native GUI Planning
│   ├── tasks/                 # Individual task files
│   └── reviews/               # Peer review files
│
└── .github/
    ├── copilot-instructions.md
    └── workflows/docker-publish.yml
```

---

## Build and Run Commands

### Setup (First Time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and fill in API keys
cp .env.example .env
# Edit .env with your keys

# 3. Initialize board and print aliases
python wake_up.py
```

### Daily Commands (via `meow.py`)

```bash
python meow.py                  # Show board status
python meow.py mc               # Open Mission Control TUI
python meow.py wake             # Re-initialize board + aliases
python meow.py add              # Add a task interactively
python meow.py task "do thing"  # Quick-add a task
python meow.py spawn            # Spawn all agents
python meow.py spawn --list     # List configured agents
python meow.py spawn --agent qwen   # Spawn specific agent
python meow.py help             # Show help
```

### Running Individual Agents

```bash
# Legacy agents
python agents/claude_agent.py
python agents/qwen_agent.py

# Generic agent (uses agents.yaml)
python agents/generic_agent.py
python agents/generic_agent.py --agent qwen
```

### Docker Deployment

```bash
# Start all agents in containers
docker-compose up -d

# Monitor from host
python mission_control.py

# Pull pre-built image
docker pull ghcr.io/theworstever1992/kitty-collab-board:main
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required For | Description |
|----------|--------------|-------------|
| `ANTHROPIC_API_KEY` | Claude | Anthropic API key |
| `DASHSCOPE_API_KEY` | Qwen | Alibaba DashScope API key |
| `OPENAI_API_KEY` | OpenAI | Optional OpenAI API key |
| `CLOWDER_BOARD_DIR` | Docker | Path to board directory |
| `CLOWDER_LOG_DIR` | Docker | Path to logs directory |

---

## Code Organization

### Agent Architecture

All agents inherit from `BaseAgent` (`agents/base_agent.py`):

```python
class BaseAgent:
    def __init__(self, name: str, model: str, role: str = "general")
    def register()          # Announce presence in agents.json
    def deregister()        # Mark as offline
    def get_tasks()         # Read pending tasks from board.json
    def claim_task(id)      # Lock a task (uses filelock)
    def complete_task(id, result)   # Mark done with result
    def log(msg, level)     # Write to console + log file
    def run()               # Main loop: poll → claim → handle → complete
    def handle_task(task)   # OVERRIDE THIS in subclasses
```

### Provider Architecture

All providers implement `BaseProvider` (`agents/providers/base.py`):

```python
class BaseProvider(ABC):
    @abstractmethod
    def complete(prompt: str, system: str = "", config: dict = None) -> str
    @abstractmethod
    def is_available() -> bool
```

Available providers: `anthropic`, `openai_compat`, `ollama`, `gemini`

### Agent Configuration (`agents.yaml`)

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
    api_key_env: DASHSCOPE_API_KEY
```

**Roles:** `reasoning`, `code`, `research`, `summarization`, `general`

---

## Code Style Guidelines

- **Python 3.10+** with type hints
- **PEP 8** compliance
- **Docstrings** for all public methods (Google style)
- **Minimal dependencies** — only add to `requirements.txt` if necessary
- **Graceful degradation** — check dependencies with try/ImportError

### File Organization Pattern

```python
"""
module.py — Kitty Collab Board
One-line description.
"""

# Imports: stdlib first, third-party, then local
import json
import os

from agents.base_agent import BaseAgent

# Constants
BOARD_DIR = Path(...)

# Classes
class MyClass:
    """Class docstring."""
    pass

# Main entry point
if __name__ == "__main__":
    pass
```

---

## Testing

**Current Status:** No test suite yet. Task 601 (pytest setup) is in progress.

### Planned Test Structure

```
tests/
├── conftest.py           # pytest fixtures
├── test_board.py         # Board operations
├── test_agent.py         # Agent lifecycle
└── test_providers.py     # Provider mocks
```

### Running Tests (Future)

```bash
pytest
pytest -v
pytest tests/test_board.py
```

---

## Task Board Schema

Tasks in `board/board.json` have these fields:

```json
{
  "id": "task_<timestamp>",
  "title": "Task title",
  "description": "Task description",
  "prompt": "Prompt sent to agent",
  "status": "pending|in_progress|done|blocked",
  "created_at": "2026-03-07T00:00:00",
  "claimed_by": "agent_name",
  "claimed_at": "2026-03-07T00:01:00",
  "completed_by": "agent_name",
  "completed_at": "2026-03-07T00:05:00",
  "result": "Task result text",
  "role": "code|reasoning|research|...",
  "priority": "critical|high|normal|low",
  "priority_order": 2,
  "blocked_by": "agent_name",
  "blocked_at": "2026-03-07T00:02:00",
  "block_reason": "Error message"
}
```

### Task Status Flow

```
pending → in_progress → done
   ↓           ↓
blocked ←─────┘
```

---

## Sprint Workflow

The project uses sprint-based development documented in `sprint/`:

### Active Sprints

| Sprint | Goal | Status |
|--------|------|--------|
| Sprint 1 | Universal Agent System | ✅ Complete |
| Sprint 2 | Smart Routing, Testing, TUI | 🔄 Active |
| Sprint 3 | Web GUI, Native GUI Planning | 🔄 Active |

### Claiming a Task

1. Check `sprint/SPRINT_X.md` for available tasks
2. Update task status: `🔄 in_progress`
3. Create/edit task file in `sprint/tasks/TASK_XXX_name.md`
4. Implement the task
5. Update task file with completion notes
6. Mark as `✅ done` in sprint board

### Task File Template

```markdown
# Task XXX — Task Name

**Status:** 🔄 in_progress
**Assigned to:** YourName
**Started:** 2026-03-07

## Goal
What needs to be done.

## Implementation Notes
- Key decisions
- Gotchas

## Review
Reviewed by: Name
Comments: ...

---
**Status:** ✅ done
**Completed:** 2026-03-07
```

---

## Security Considerations

- **API keys** stored in `.env` (never commit to git)
- **File permissions:** Board and log directories created with default permissions
- **No input validation** on task prompts (agents receive raw text)
- **No sandboxing** — agents run with full Python capabilities
- **Docker:** Containers run with shared volume mounts for board/logs

### Sensitive Files

```
.env              # API keys — must be in .gitignore
board/board.json  # May contain sensitive task data
logs/*.log        # May contain sensitive output
```

---

## Common Issues

### File Locking
- Uses `filelock` library for cross-platform locking
- Fallback to `_NoOpLock` if library not available
- Lock files: `board.json.lock`, `agents.json.lock`

### Race Conditions
- Task claiming is optimistic (check-then-act)
- File locking prevents corrupted writes, not duplicate claims
- Heavy load may cause occasional duplicate claims

### Windows vs Linux
- Windows: Uses `windows/spawn_agents.ps1` (PowerShell jobs)
- Linux/Mac: Uses `spawn_agents.sh` (background processes)
- TUI: curses on Unix, simple print mode on Windows

---

## Key Documents Reference

| Document | Purpose |
|----------|---------|
| `README.md` | User-facing quick start |
| `CLAUDE.md` | Claude Code context |
| `QWEN.md` | Qwen agent context |
| `KIMI_HANDOFF.md` | Kimi agent onboarding |
| `STANDING_ORDERS.md` | Agent protocol rules |
| `IMPROVEMENT_PLAN.md` | 8-phase roadmap |
| `SPRINT_1.md` | Completed sprint |
| `SPRINT_2.md` | Active sprint |
| `SPRINT_3.md` | Active sprint |

---

## Quick Reference

### Adding a New Agent

1. Add entry to `agents.yaml`
2. Ensure provider is implemented in `agents/providers/`
3. Run `python meow.py spawn --agent <name>`

### Adding a New Provider

1. Create `agents/providers/my_provider.py`
2. Inherit from `BaseProvider`
3. Implement `complete()` and `is_available()`
4. Add to `build_provider()` in `agents/config.py`

### Debugging an Agent

```bash
# Check agent logs
cat logs/{agent_name}.log

# Check board state
python -c "import json; print(json.dumps(json.load(open('board/board.json')), indent=2))"

# Check agent registry
python -c "import json; print(json.dumps(json.load(open('board/agents.json')), indent=2))"
```

---

*For the human operator: This file helps AI agents understand the project quickly. Keep it updated when architecture changes.*
