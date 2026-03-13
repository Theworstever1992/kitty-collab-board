"""
agent_client.py — Kitty Collab Board
AgentClient: composes FileBackend + PostgresBackend, routes transparently.

Usage (offline, no v2 API):
    client = AgentClient("my-agent", role="coder")
    client.get_tasks()         # reads board/board.json
    client.post_message(...)   # writes to board/channels/

Usage (online, v2 API running):
    client = AgentClient("my-agent", role="coder", api_base="http://localhost:9000")
    client.get_tasks()         # hits PostgresBackend via REST
    # Falls back to FileBackend silently if API goes down
"""

import datetime
import time
from typing import TYPE_CHECKING

from agents.file_backend import FileBackend

if TYPE_CHECKING:
    from backend.postgres_backend import PostgresBackend

# Seconds between API health probes (avoids hammering on every call)
_PROBE_INTERVAL = 30
# Seconds before giving up on the health probe
_PROBE_TIMEOUT = 2


class AgentClient:
    """
    Transparent routing layer between FileBackend (offline) and PostgresBackend (online).

    Callers never need to know which backend is active — identical API surface either way.
    """

    def __init__(
        self,
        agent_name: str,
        role: str = "general",
        api_base: str | None = None,
        team_id: str | None = None,
        model: str = "unknown",
    ):
        self.agent_name = agent_name
        self.role = role
        self.api_base = api_base
        self.team_id = team_id
        self.model = model

        self._file_backend = FileBackend()
        self._pg_backend: "PostgresBackend | None" = None
        self._online = False
        self._last_probe_time: float = 0.0

        # Auto-register on creation
        self._file_backend.register_agent(agent_name, role, team_id, model)

    # ── Backend routing ────────────────────────────────────────────────────────

    def _probe_api(self) -> bool:
        """
        Check whether the v2 API is reachable. Cached for _PROBE_INTERVAL seconds.
        Returns True if online.
        """
        if not self.api_base:
            return False

        now = time.monotonic()
        if now - self._last_probe_time < _PROBE_INTERVAL:
            return self._online
        self._last_probe_time = now

        try:
            import urllib.request
            req = urllib.request.urlopen(
                f"{self.api_base}/api/health",
                timeout=_PROBE_TIMEOUT,
            )
            was_online = self._online
            self._online = req.status == 200
            # Transition: offline → online → trigger sync
            if not was_online and self._online:
                self._on_reconnect()
            return self._online
        except Exception:
            self._online = False
            return False

    def _get_pg_backend(self) -> "PostgresBackend":
        """Lazy-load PostgresBackend on first successful probe."""
        if self._pg_backend is None:
            from backend.postgres_backend import PostgresBackend
            self._pg_backend = PostgresBackend(api_base=self.api_base)
        return self._pg_backend

    def _active_backend(self) -> FileBackend:
        """Return the appropriate backend. Falls back to FileBackend silently."""
        if self._probe_api():
            try:
                return self._get_pg_backend()
            except Exception:
                self._online = False
        return self._file_backend

    def _on_reconnect(self) -> None:
        """Called when transitioning from offline → online. Sync pending completions."""
        try:
            # Ensure pg_backend is initialized for sync
            if self.api_base and self._pg_backend is None:
                self._get_pg_backend()
            self.sync_pending_completions()
        except Exception:
            pass  # Never let sync errors break normal operation

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def get_tasks(self) -> list[dict]:
        return self._active_backend().get_tasks(team_id=self.team_id)

    def claim_task(self, task_id: str) -> bool:
        claimed_at = datetime.datetime.now().isoformat()
        return self._active_backend().claim_task(task_id, self.agent_name, claimed_at)

    def complete_task(self, task_id: str, result: str) -> bool:
        return self._active_backend().complete_task(task_id, self.agent_name, result)

    def get_task(self, task_id: str) -> dict | None:
        return self._active_backend().get_task(task_id)

    # ── Messages ──────────────────────────────────────────────────────────────

    def post_message(
        self,
        channel: str,
        content: str,
        message_type: str = "chat",
        thread_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        return self._active_backend().post_message(
            channel, content, self.agent_name, message_type, thread_id, metadata
        )

    def read_messages(
        self,
        channel: str,
        limit: int = 20,
        message_type: str | None = None,
    ) -> list[dict]:
        return self._active_backend().read_messages(channel, limit, message_type)

    # ── Agents ────────────────────────────────────────────────────────────────

    def heartbeat(self) -> None:
        """Update last_seen for this agent. Call periodically from agent loops."""
        self._active_backend().update_heartbeat(self.agent_name)

    # ── Tokens / Budget ───────────────────────────────────────────────────────

    def log_tokens(self, input_tokens: int, output_tokens: int) -> dict:
        return self._active_backend().log_tokens(
            self.agent_name, input_tokens, output_tokens, self.model
        )

    def check_budget(self) -> dict:
        return self._active_backend().check_budget(self.agent_name)

    # ── RAG / Context ─────────────────────────────────────────────────────────

    def get_context(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Semantic search over past context (RAG).
        Returns empty list offline — always safe to iterate.
        """
        result = self._active_backend().search_context(query, top_k)
        return result or []

    def format_context_for_prompt(self, items: list[dict]) -> str:
        """
        Format RAG context items into a prompt-injectable string.
        Returns empty string if no items (offline or no relevant context found).
        """
        if not items:
            return ""
        lines = ["### Relevant past context:"]
        for item in items:
            score = item.get("score", "")
            text = item.get("text") or item.get("content", "")
            source = item.get("source", "")
            prefix = f"[{source}] " if source else ""
            score_str = f" (similarity: {score:.2f})" if isinstance(score, float) else ""
            lines.append(f"- {prefix}{text}{score_str}")
        return "\n".join(lines)

    # ── Sync on reconnect ─────────────────────────────────────────────────────

    def sync_pending_completions(self) -> dict:
        """
        Push locally-completed tasks to the v2 API after reconnecting.
        Logs conflicts to board/conflicts.json when the API disagrees.

        Returns: {"pushed": N, "conflicts": M}
        """
        if not self._pg_backend:
            return {"pushed": 0, "conflicts": 0}

        local_tasks = self._file_backend.get_tasks()
        done_mine = [
            t for t in local_tasks
            if t.get("status") == "done" and t.get("claimed_by") == self.agent_name
        ]

        pushed = 0
        conflicts = 0

        for task in done_mine:
            task_id = task["id"]
            try:
                remote = self._pg_backend.get_task(task_id)
                if remote is None:
                    # Task unknown to API — push it
                    self._pg_backend.complete_task(task_id, self.agent_name, task.get("result", ""))
                    pushed += 1
                elif remote.get("claimed_by") not in (None, self.agent_name):
                    # Conflict: someone else claimed it on the API side
                    self._file_backend.log_conflict({
                        "task_id": task_id,
                        "local_agent": self.agent_name,
                        "remote_agent": remote.get("claimed_by"),
                        "local_result": task.get("result", ""),
                        "remote_status": remote.get("status"),
                    })
                    conflicts += 1
            except Exception:
                pass  # Network hiccup — leave for next sync

        return {"pushed": pushed, "conflicts": conflicts}
