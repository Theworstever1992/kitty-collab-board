# Copilot Instructions for Kitty Collab Board

## 1. Build, Test, and Lint

- **Dependencies**: `pip install -r requirements.txt`
- **Run TUI**: `python mission_control.py` (or alias `mc`)
- **Run CLI**: `python meow.py` (or alias `meow`)
- **Initialize Board**: `python wake_up.py` (or alias `wake`)
- **Spawn Agents**: `powershell -ExecutionPolicy Bypass -File windows/spawn_agents.ps1`
- **Tests**: No test suite currently configured.
- **Linting**: No linting configuration found. Follow PEP 8 guidelines.

## 2. High-Level Architecture

This is a multi-agent collaboration system where agents run as independent processes and coordinate via shared JSON files in `board/`.

- **Shared State (`board/`)**:
  - `board.json`: List of tasks with status (`pending`, `in_progress`, `done`, `blocked`).
  - `agents.json`: Registry of active agents and their status (`online`, `offline`, `idle`).
- **Agents (`agents/`)**:
  - Inherit from `BaseAgent` (`agents/base_agent.py`).
  - Poll `board.json` for tasks.
  - Claim tasks by updating the JSON file.
  - Write logs to `logs/`.
- **Mission Control (`mission_control.py`)**: A TUI that monitors the JSON files and allows manual task addition.
- **CLI (`meow.py`)**: A command-line interface for managing the board.

## 3. Key Conventions

- **Agent Lifecycle**:
  - **Startup**: Must call `self.register()` to announce presence in `agents.json`.
  - **Shutdown**: Must call `self.deregister()` to mark status as `offline`.
  - **Loop**: Implement `run()` to poll for tasks and `handle_task(task)` to execute work.
- **Task Handling**:
  - Use `self.claim_task(task_id)` to lock a task before working on it to prevent race conditions.
  - Use `self.complete_task(task_id, result)` to finalize work.
  - Always update the board state to reflect progress.
- **Communication**:
  - Agents do not communicate directly; they use the board as a shared memory.
  - Use `self.log()` for all significant actions (writes to console and file).
- **Environment**:
  - Requires `.env` file with API keys (e.g., `ANTHROPIC_API_KEY`, `DASHSCOPE_API_KEY`).
  - PowerShell aliases (`wake_up`, `meow`, `mc`) are recommended for workflow efficiency.
