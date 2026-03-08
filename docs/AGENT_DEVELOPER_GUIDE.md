# Kitty Collab Board — Agent Developer Guide

This guide explains how to create a new agent for the Clowder system.

---

## The Agent Pattern

All agents inherit from `BaseAgent` in `agents/base_agent.py`. The base class handles:

- Registration and heartbeat on `agents.json`
- Polling `board.json` for pending tasks
- Claiming tasks (with file locking)
- Completing or blocking tasks
- Role-based and skills-based task filtering
- Handoff protocol (send/receive/decline/expire)
- Logging to stdout and `logs/<name>.log`

Your subclass only needs to implement one method: `handle_task(task: dict) -> str`.

---

## Minimal Agent

```python
# agents/my_agent.py
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="my-agent",
            model="my-model-v1",
            role="code",                          # or: reasoning, research, summarization, general
            skills=["python", "bash", "testing"], # optional; lowercase strings
        )

    def handle_task(self, task: dict) -> str:
        prompt = task.get("prompt", task.get("description", ""))
        # ... call your AI API here ...
        return "Result text written back to board"


if __name__ == "__main__":
    agent = MyAgent()
    agent.run()
```

Run it: `python agents/my_agent.py`

---

## BaseAgent Reference

### `__init__(name, model, role, skills)`

| Param | Type | Description |
|-------|------|-------------|
| `name` | str | Unique agent identifier (used in `agents.json`, log filename) |
| `model` | str | Model name (stored in registry, informational) |
| `role` | str | Task role filter: `reasoning`, `code`, `research`, `summarization`, `general` |
| `skills` | list[str] | Capabilities declared by this agent, e.g. `["python", "react"]` |

Skills are lowercased automatically. Tasks that declare `skills` require an agent to have ALL listed skills.

### `handle_task(task: dict) -> str`

Called by the main loop when a task is successfully claimed. Return the result string — this is written to `task["result"]` and the task is marked `done`.

Raise any exception to mark the task `blocked` with the exception message as `block_reason`. The agent will continue running.

```python
def handle_task(self, task: dict) -> str:
    prompt = task.get("prompt") or task.get("description", "")
    if not prompt:
        raise ValueError("Task has no prompt or description")
    # ... process ...
    return result_text
```

### `run()`

Main loop. Calls in order every 5 seconds:
1. `_heartbeat()` — updates `last_seen` in `agents.json`
2. `get_tasks()` — reads pending tasks (role + skills filtered)
3. `claim_task(id)` — locks board file, sets status to `in_progress`
4. `handle_task(task)` — your implementation
5. `complete_task(id, result)` — sets status to `done`, writes result

On `KeyboardInterrupt`, calls `deregister()` and exits.

### `log(message, level="INFO")`

Prints to stdout and appends to `logs/<name>.log`:
```
[2026-03-07 12:00:00] [INFO] [my-agent] Claimed task: task_123
```

### `get_tasks(role_filter=True) -> list`

Returns pending tasks matching this agent's role and skills, sorted by priority then creation time.

### `claim_task(task_id) -> bool`

Atomically claims a task. Returns `False` if the task was already claimed by another agent (race condition). Always check the return value.

### `complete_task(task_id, result)`

Marks task done, writes result string. Fires audit log if `agents/audit.py` is available.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLOWDER_BOARD_DIR` | `<project_root>/board` | Board directory path |
| `CLOWDER_LOG_DIR` | `<project_root>/logs` | Log directory path |

These are resolved at import time by `BaseAgent`. Docker containers should set both explicitly.

---

## Role and Skills Design

### When to use `role`

Roles are coarse-grained routing. Use them when you have specialized agents (e.g., one agent for code review, another for research). Tasks without a role are claimable by any agent.

```python
super().__init__(name="researcher", model="...", role="research")
```

### When to use `skills`

Skills are fine-grained routing within a role. A `code` agent might have `skills=["python"]` and another might have `skills=["python", "react"]`. A task requiring `["python", "react"]` would only go to the second.

```python
# Task requires both skills
python meow.py task "Build UI component" --role code --skills python,react

# Agent must have both to claim it
super().__init__(name="fullstack", model="...", role="code", skills=["python", "react", "typescript"])
```

Skills are always AND — not OR. An agent with `["python"]` cannot claim a task requiring `["python", "react"]`.

---

## File Locking

`BaseAgent` uses `filelock.FileLock` (from `pip install filelock`) on all board writes. If `filelock` is not installed, a no-op fallback is used. Install it for production deployments — without it, concurrent agents can corrupt `board.json`.

```bash
pip install filelock
```

---

## Handoff Protocol

Use handoffs when you cannot complete a task and another agent would be better suited.

```python
def handle_task(self, task: dict) -> str:
    if "react" in task.get("skills", []) and "react" not in self.skills:
        success = self.handoff_task(
            task_id=task["id"],
            target_agent="frontend-agent",
            notes="This task requires React knowledge I don't have."
        )
        if success:
            return "Handed off to frontend-agent"
    # ... normal handling ...
```

### Handoff lifecycle

```
handoff.status: pending_acceptance → accepted
                                   → declined   (task returns to pending)
                                   → cancelled  (source cancels)
                                   → expired    (10 min timeout)
```

### Available handoff methods

```python
# Initiate handoff (source agent)
self.handoff_task(task_id, target_agent, notes) -> bool

# Accept handoff (target agent — called in your run loop or handle_task)
self.accept_handoff(task_id) -> bool

# Decline handoff (target agent)
self.decline_handoff(task_id, reason) -> bool

# Cancel handoff (source agent, before acceptance)
self.cancel_handoff(task_id) -> bool

# Get handoffs waiting for this agent
self.get_pending_handoffs() -> list[dict]

# Expire stale handoffs (call periodically)
self.check_handoff_expiry()
```

To check for incoming handoffs in your main loop, override `run()` or check in `handle_task`:

```python
def run(self):
    self.register()
    while True:
        self._heartbeat()
        self.check_handoff_expiry()

        # Check incoming handoffs first
        for ho in self.get_pending_handoffs():
            self.accept_handoff(ho["task_id"])

        tasks = self.get_tasks()
        if tasks:
            task = tasks[0]
            if self.claim_task(task["id"]):
                try:
                    result = self.handle_task(task)
                    self.complete_task(task["id"], result)
                except Exception as e:
                    self._mark_blocked(task["id"], str(e))
        time.sleep(5)
```

---

## Registering with Docker

Add a service entry to `docker-compose.yml`:

```yaml
services:
  my-agent:
    build:
      context: .
      dockerfile: Dockerfile
    command: python agents/my_agent.py
    volumes:
      - ./board:/app/board
      - ./logs:/app/logs
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - CLOWDER_BOARD_DIR=/app/board
      - CLOWDER_LOG_DIR=/app/logs
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
```

---

## Using Existing Providers

The `agents/providers/` directory contains reusable API client wrappers. Check `agents/providers/` for available providers rather than calling SDKs directly.

```python
from agents.providers.anthropic_provider import AnthropicProvider
from agents.providers.openai_compat_provider import OpenAICompatProvider
```

---

## Audit Logging

If `agents/audit.py` is present, `BaseAgent` automatically fires audit events:
- `audit_task_claimed(task, agent_name)` — on successful claim
- `audit_task_completed(task, agent_name, result)` — on completion

Audit entries are written to `board/audit.log`. No action needed in subclasses.

---

## Testing Your Agent

```bash
# Initialize test board
CLOWDER_BOARD_DIR=/tmp/test-board python wake_up.py

# Add a test task
CLOWDER_BOARD_DIR=/tmp/test-board python meow.py task "Test task" --role code

# Run your agent against the test board
CLOWDER_BOARD_DIR=/tmp/test-board python agents/my_agent.py
```

For unit tests, mock `board.json` reads/writes using `tmp_path` (pytest) or `tempfile.TemporaryDirectory`.

---

## Conventions

- Agent names: lowercase, hyphen-separated (`my-agent`, `code-reviewer`)
- Log entries include `[agent_name]` for easy grepping
- Never write to `board.json` without using `_lock()` — race conditions corrupt the file
- Always return a string from `handle_task` — even if empty
- Raise exceptions for genuine failures; return `"nothing to do"` for gracefully skipped tasks
