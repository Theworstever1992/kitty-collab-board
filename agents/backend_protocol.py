"""
backend_protocol.py — Kitty Collab Board
BoardBackend Protocol: the interface both FileBackend and PostgresBackend implement.

Neither backend inherits from this class — structural subtyping (duck typing) only.
@runtime_checkable lets you use isinstance() checks if needed.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class BoardBackend(Protocol):
    # ── Tasks ─────────────────────────────────────────────────────────────────
    def get_tasks(self, team_id: str | None = None) -> list[dict]:
        """Return all tasks, optionally filtered by team."""
        ...

    def claim_task(self, task_id: str, agent_name: str, claimed_at: str) -> bool:
        """Atomically claim a task. Returns True if this agent won the claim."""
        ...

    def complete_task(self, task_id: str, agent_name: str, result: str) -> bool:
        """Mark a task done with a result. Returns True on success."""
        ...

    def get_task(self, task_id: str) -> dict | None:
        """Fetch a single task by ID, or None if not found."""
        ...

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
        """Post a message to a channel. Returns the message ID."""
        ...

    def read_messages(
        self,
        channel: str,
        limit: int = 20,
        message_type: str | None = None,
    ) -> list[dict]:
        """Read recent messages from a channel."""
        ...

    # ── Agents ────────────────────────────────────────────────────────────────
    def register_agent(
        self,
        name: str,
        role: str,
        team: str | None = None,
        model: str = "unknown",
    ) -> None:
        """Register or update an agent entry."""
        ...

    def update_heartbeat(self, name: str) -> None:
        """Stamp an agent's last_seen to now."""
        ...

    # ── Tokens / Budget ───────────────────────────────────────────────────────
    def log_tokens(
        self,
        agent: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> dict:
        """Log token usage and return updated metrics dict."""
        ...

    def check_budget(self, agent: str) -> dict:
        """Return budget status for an agent (used, limit, remaining, ok)."""
        ...

    # ── Conflicts / Sync ──────────────────────────────────────────────────────
    def log_conflict(self, conflict: dict) -> None:
        """Append a conflict record to board/conflicts.json."""
        ...

    # ── RAG / Profiles (None when offline) ────────────────────────────────────
    def search_context(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict] | None:
        """Semantic search over past context. Returns None if unavailable offline."""
        ...

    def get_agent_profile(self, agent_name: str) -> dict | None:
        """Return agent profile (avatar, bio, skills). None if unavailable offline."""
        ...
