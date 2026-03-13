"""
file_backend.py — Kitty Collab Board
FileBackend: thin wrapper over the existing v1 modules.

Implements BoardBackend via structural subtyping (no inheritance).
Zero new logic — pure delegation to channels.py, atomic.py, context_manager.py.
"""

import datetime
import os
from pathlib import Path

from agents.atomic import atomic_read, atomic_write
from agents.channels import get_or_create_channel
from agents.context_manager import get_context_manager

BOARD_DIR = Path(os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board"))


class FileBackend:
    """
    Offline backend — delegates entirely to v1 file-based modules.
    Always available. Never raises connection errors.
    """

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def get_tasks(self, team_id: str | None = None) -> list[dict]:
        board = atomic_read(BOARD_DIR / "board.json", {"tasks": []})
        tasks = board.get("tasks", [])
        if team_id is not None:
            tasks = [t for t in tasks if t.get("team_id") == team_id]
        return tasks

    def claim_task(self, task_id: str, agent_name: str, claimed_at: str) -> bool:
        board_file = BOARD_DIR / "board.json"
        board = atomic_read(board_file, {"tasks": []})
        for task in board.get("tasks", []):
            if task["id"] == task_id and task.get("status") == "pending":
                task["status"] = "claimed"
                task["claimed_by"] = agent_name
                task["claimed_at"] = claimed_at
                atomic_write(board_file, board)
                return True
        return False

    def complete_task(self, task_id: str, agent_name: str, result: str) -> bool:
        board_file = BOARD_DIR / "board.json"
        board = atomic_read(board_file, {"tasks": []})
        for task in board.get("tasks", []):
            if task["id"] == task_id and task.get("claimed_by") == agent_name:
                task["status"] = "done"
                task["result"] = result
                task["completed_at"] = datetime.datetime.now().isoformat()
                atomic_write(board_file, board)
                return True
        return False

    def get_task(self, task_id: str) -> dict | None:
        board = atomic_read(BOARD_DIR / "board.json", {"tasks": []})
        for task in board.get("tasks", []):
            if task["id"] == task_id:
                return task
        return None

    # ── Messages ──────────────────────────────────────────────────────────────

    def post_message(
        self,
        channel: str,
        content: str,
        sender: str,
        message_type: str = "chat",
        thread_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        ch = get_or_create_channel(channel)
        return ch.post(content, sender, message_type, thread_id, metadata)

    def read_messages(
        self,
        channel: str,
        limit: int = 20,
        message_type: str | None = None,
    ) -> list[dict]:
        ch = get_or_create_channel(channel)
        messages = ch.read(limit=limit)
        if message_type is not None:
            messages = [m for m in messages if m.get("type") == message_type]
        return messages

    # ── Agents ────────────────────────────────────────────────────────────────

    def register_agent(
        self,
        name: str,
        role: str,
        team: str | None = None,
        model: str = "unknown",
    ) -> None:
        agents_file = BOARD_DIR / "agents.json"
        agents = atomic_read(agents_file, {})
        agents[name] = {
            **agents.get(name, {}),
            "role": role,
            "model": model,
            "team": team,
            "status": "online",
            "last_seen": datetime.datetime.now().isoformat(),
        }
        atomic_write(agents_file, agents)

    def update_heartbeat(self, name: str) -> None:
        agents_file = BOARD_DIR / "agents.json"
        agents = atomic_read(agents_file, {})
        if name in agents:
            agents[name]["last_seen"] = datetime.datetime.now().isoformat()
            atomic_write(agents_file, agents)

    # ── Tokens / Budget ───────────────────────────────────────────────────────

    def log_tokens(
        self,
        agent: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> dict:
        return get_context_manager().log_token_usage(agent, input_tokens, output_tokens, model)

    def check_budget(self, agent: str) -> dict:
        return get_context_manager().check_budget(agent)

    # ── Conflicts / Sync ──────────────────────────────────────────────────────

    def log_conflict(self, conflict: dict) -> None:
        conflicts_file = BOARD_DIR / "conflicts.json"
        conflicts = atomic_read(conflicts_file, [])
        conflicts.append({
            **conflict,
            "logged_at": datetime.datetime.now().isoformat(),
        })
        atomic_write(conflicts_file, conflicts)

    # ── RAG / Profiles (not available offline) ────────────────────────────────

    def search_context(self, query: str, top_k: int = 5) -> None:
        return None

    def get_agent_profile(self, agent_name: str) -> None:
        return None
