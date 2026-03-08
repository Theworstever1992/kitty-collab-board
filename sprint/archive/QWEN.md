# QWEN.md — Instructions for Qwen on Kitty Collab Board

This file provides guidance to the Qwen agent (claude.ai/code equivalent for Qwen)
when working in this repository.

## Overview

**Kitty Collab Board** (codename: **Clowder**) is a multi-agent AI collaboration system.
Multiple AI agents (Claude, Qwen, Gemini, Llama, etc.) run as independent processes,
poll a shared JSON task board, claim and complete tasks, and report results.
A human operator manages the board via `meow.py` (CLI) or `mission_control.py` (TUI).

**Your role:** Code generation, analysis, and backend implementation.
**Model:** `qwen-plus` via DashScope OpenAI-compatible API.

---

## Architecture Summary

```
kitty-collab-board/
├── meow.py                    # Main CLI entry point
├── wake_up.py                 # Initialize board, print shell aliases
├── mission_control.py         # TUI dashboard (curses on Unix, simple on Windows)
├── config.py                  # Centralized configuration with env validation
├── agents.yaml                # Agent team configuration (name, model, provider, role)
│
├── agents/                    # Agent implementations
│   ├── base_agent.py          # BaseAgent class — all agents inherit from this
│   ├── generic_agent.py       # Config-driven agent (uses any provider)
│   ├── claude_agent.py        # Legacy Claude agent (Anthropic)
│   ├── qwen_agent.py          # Legacy Qwen agent (DashScope)
│   ├── config.py              # YAML config loader + provider builder
│   ├── prompts.py             # Role-based system prompts
│   ├── audit.py               # Board audit logging
│   ├── retry.py               # API retry with exponential backoff
│   ├── health_monitor.py      # Agent health tracking + alerts
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
├── web/                       # Web GUI (FastAPI backend + React frontend)
├── tests/                     # pytest test suite
└── sprint/                    # Sprint planning and task tracking
```

### Shared State (`board/`)

- **`board.json`** — Task list with statuses: `pending` → `in_progress` → `done` | `blocked`
- **`agents.json`** — Agent registry with `status`, `last_seen`, `role`, `skills`

Task fields: `id`, `title`, `description`, `prompt`, `status`, `created_at`,
`claimed_by`, `claimed_at`, `completed_by`, `completed_at`, `result`,
`role`, `priority`, `priority_order`, `skills`, `blocked_by`, `block_reason`,
`handoff` (for agent handoff protocol)

### Agent Pattern

All agents inherit from `agents/base_agent.py:BaseAgent`. The base class handles:
- Registration/deregistration in `agents.json`
- Board polling with file locking (`filelock`)
- Task claiming/completing with optimistic locking
- Structured logging to `logs/<agent_name>.log`
- Handoff protocol (initiate, accept, decline, cancel)
- Health monitoring integration

Subclasses only override `handle_task(task: dict) -> str`.

### Provider Architecture

All providers implement `agents/providers/base.py:BaseProvider`:

```python
class BaseProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, system: str = "", config: dict = None) -> str
    @abstractmethod
    def is_available(self) -> bool
```

Available providers: `anthropic`, `openai_compat`, `ollama`, `gemini`

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and fill in API keys
cp .env.example .env
# Edit .env with your keys (DASHSCOPE_API_KEY required for Qwen)

# 3. Initialize board and print aliases
python wake_up.py
```

### Environment Variables

| Variable | Required For | Description |
|----------|--------------|-------------|
| `DASHSCOPE_API_KEY` | Qwen | Alibaba DashScope API key |
| `ANTHROPIC_API_KEY` | Claude | Anthropic API key |
| `CLOWDER_BOARD_DIR` | Docker | Path to board directory |
| `CLOWDER_LOG_DIR` | Docker | Path to logs directory |

---

## Common Commands

### CLI (via `meow.py`)

```bash
python meow.py                    # Show board status
python meow.py mc                 # Open Mission Control TUI
python meow.py wake               # Re-initialize board + print aliases
python meow.py add                # Add a task interactively
python meow.py task "do thing"    # Quick-add a task
python meow.py task "fix bug" --role code --priority high
python meow.py spawn              # Spawn all agents
python meow.py spawn --agent qwen # Spawn specific agent
python meow.py spawn --list       # List configured agents
python meow.py template list      # List saved task templates
python meow.py help               # Show help
```

### Running Individual Agents

```bash
# Legacy agents
python agents/qwen_agent.py
python agents/claude_agent.py

# Generic agent (uses agents.yaml config)
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

### Testing

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_board.py
pytest tests/test_agent.py
pytest tests/test_providers.py
```

---

## Your Tasks (Current Work Plan)

See `sprint/SPRINT_6.md` for the current sprint board.

### Phase 9: Production Readiness (Your Track)

| ID | Task | Status |
|----|------|--------|
| 6001 | Environment configuration system | ✅ done |
| 6002 | Logging infrastructure upgrade | ⬜ todo |
| 6003 | Performance profiling + optimization | ⬜ todo |
| 6004 | Memory usage optimization | ⬜ todo |
| 6005 | Startup time optimization | ⬜ todo |

### Phase 10: Advanced Features (Your Track)

| ID | Task | Status |
|----|------|--------|
| 6022 | Task dependencies (blocked-by) | ⬜ todo |
| 6024 | Recurring tasks | ⬜ todo |
| 6025 | Multi-board support | ⬜ todo |
| 6031 | Task completion metrics | ⬜ todo |
| 6032 | Agent performance tracking | ⬜ todo |
| 6033 | Dashboard with charts | ⬜ todo |
| 6034 | Export reports (CSV/PDF) | ⬜ todo |

### Phase 11: Native GUI (Shared Track)

| ID | Task | Status |
|----|------|--------|
| 6055 | Offline-first architecture | ⬜ todo |

**Note:** Check `sprint/SPRINT_6.md` for the latest task status before claiming work.

---

## Coding Conventions

- **Python 3.10+** with type hints
- **PEP 8** compliance
- **Docstrings** for all public methods (Google style)
- **Minimal dependencies** — update `requirements.txt` if you add packages
- **Graceful degradation** — check dependencies with `try/ImportError`

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

### Board Access Pattern

All board reads/writes go through `base_agent.py` methods — don't touch `board.json` directly:

```python
# Correct
tasks = self.get_tasks()
self.claim_task(task_id)
self.complete_task(task_id, result)

# Wrong — don't do this
board = json.load(open("board/board.json"))
```

### Logging

Use structured logging via `self.log(msg, level)`:

```python
self.log("Task started", "INFO")
self.log("API error occurred", "ERROR")
self.log("Debug details", "DEBUG")
```

Logs are written to both console and `logs/<agent_name>.log`.

---

## Key Design Decisions

### File Locking
- Uses `filelock` library for cross-platform locking
- Lock files: `board.json.lock`, `agents.json.lock`
- Fallback to `_NoOpLock` if library not available

### Task Routing
- **Role-based:** Tasks can specify `role` (code, reasoning, research, etc.)
- **Skills-based:** Tasks can specify required `skills` list
- **Priority:** Tasks sorted by `priority_order` (critical=0, high=1, normal=2, low=3)

### Handoff Protocol
- Agents can transfer tasks to other agents with context notes
- Handoff states: `pending_acceptance`, `accepted`, `declined`, `cancelled`, `expired`
- Timeout: 10 minutes (configurable)

### Health Monitoring
- Warning threshold: 60 seconds since last heartbeat
- Offline threshold: 300 seconds (5 minutes)
- Alerts via console, log file, and optional webhooks (Discord/Slack)

---

## Testing Practices

- **Unit tests** in `tests/unit/` — test individual functions/classes
- **Integration tests** in `tests/integration/` — test agent interactions
- **Fixtures** in `tests/conftest.py` — reusable test setup
- **Mock providers** for API-free testing

Run tests before committing changes:
```bash
pytest
```

---

## Debugging

### Check Board State
```bash
python -c "import json; print(json.dumps(json.load(open('board/board.json')), indent=2))"
```

### Check Agent Registry
```bash
python -c "import json; print(json.dumps(json.load(open('board/agents.json')), indent=2))"
```

### View Agent Logs
```bash
tail -f logs/qwen.log
```

### Debug Configuration
```bash
python config.py  # Validate configuration loading
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `README.md` | User-facing quick start |
| `CLAUDE.md` | Claude Code context |
| `AGENTS.md` | Comprehensive project documentation |
| `STANDING_ORDERS.md` | Agent protocol rules |
| `IMPROVEMENT_PLAN.md` | 8-phase roadmap |
| `sprint/SPRINT_6.md` | Current sprint board |
| `sprint/QWEN_PROGRESS_REPORT_2.md` | Your latest progress report |

---

## Quick Reference

### Adding a Task Programmatically
```python
from mission_control import add_task
task_id = add_task("Task title", description="...", prompt="...", role="code", priority="high")
```

### Claiming and Completing Tasks
```python
tasks = self.get_tasks()
if tasks:
    task = tasks[0]
    if self.claim_task(task["id"]):
        result = self.handle_task(task)
        self.complete_task(task["id"], result)
```

### Handoff Example
```python
# Initiate handoff
success = self.handoff_task(task_id, "claude", "Need reasoning help with...")

# Accept handoff (in receiving agent)
if self.accept_handoff(task_id):
    result = self.handle_task(task)
    self.complete_task(task_id, result)
```

---

*Last updated: 2026-03-08 | Sprint 6 in progress*
