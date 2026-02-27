# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Kitty Collab Board** (codename: **Clowder**) is a multi-agent AI collaboration system. Multiple AI agents (Claude, Qwen, etc.) run in parallel, poll a shared JSON task board, claim and complete tasks, and report results. A human operator manages the board via `meow.py` / `mission_control.py`.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # fill in API keys
python wake_up.py     # create board/ and logs/ dirs, print PowerShell aliases
```

Required env vars: `ANTHROPIC_API_KEY`, `DASHSCOPE_API_KEY`

## Common Commands

```bash
python meow.py                  # show board status
python meow.py mc               # open Mission Control TUI (curses on Linux, simple on Windows)
python meow.py task "do thing"  # quick-add a task
python meow.py add              # add a task interactively
python meow.py spawn            # spawn agents via PowerShell (Windows only)
python wake_up.py               # re-initialize board + print aliases
```

To run a single agent directly:
```bash
python agents/claude_agent.py
python agents/qwen_agent.py
```

To stop all background agent jobs (PowerShell):
```powershell
Get-Job | Stop-Job; Get-Job | Remove-Job
```

## Architecture

### Shared State (board/)
- `board/board.json` — the task list; agents poll this, claim tasks by setting `status: "in_progress"` and `claimed_by`, then write results and set `status: "done"`
- `board/agents.json` — agent registry; each agent writes its entry on startup and updates `last_seen` every heartbeat

Task statuses: `pending` → `in_progress` → `done` | `blocked`

### Agent Pattern
All agents inherit from `agents/base_agent.py:BaseAgent`. The base class handles:
- `register()` / `deregister()` — read-modify-write `agents.json`
- `get_tasks()` — returns `pending` tasks from `board.json`
- `claim_task(id)` — atomic-ish claim (no true locking; race conditions possible under heavy load)
- `complete_task(id, result)` — writes result and marks done
- `log(msg)` — prints and appends to `logs/<agent_name>.log`
- `run()` — main loop: heartbeat → get tasks → claim first → `handle_task()` → complete; polls every 5 seconds

Subclasses override only `handle_task(task: dict) -> str`. The `task` dict includes `title`, `description`, `prompt` fields.

### Agent Implementations
- `claude_agent.py` — uses `anthropic` SDK; sends `prompt` field to `claude-3-5-sonnet-20241022`
- `qwen_agent.py` — uses `openai` SDK pointed at DashScope's OpenAI-compatible endpoint; model `qwen-plus`

New agents: subclass `BaseAgent`, set `name`/`model`/`role` in `__init__`, implement `handle_task`, add to `spawn_agents.ps1`.

### Operator Tools
- `meow.py` — thin CLI dispatcher; imports from `mission_control.py` for task adding
- `mission_control.py` — provides `add_task()`, a curses TUI (Unix), and a simple print loop (Windows/fallback)
- `wake_up.py` — creates `board/` and `logs/` dirs and prints PowerShell alias commands

### Agent Protocol (STANDING_ORDERS.md)
Agents must: register on startup, read the board before acting, not duplicate claimed tasks, log all actions, flag blockers, and hand off rather than abandon tasks.
