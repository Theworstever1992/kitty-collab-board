"""
postgres_backend.py — Kitty Collab Board v2
PostgresBackend: REST client wrapping the v2 FastAPI + PostgreSQL API.

Raises BackendUnavailableError on any connection failure.
AgentClient catches this and falls back to FileBackend silently.

Note: This is a REST client (not SQLAlchemy direct) so it works both when the
backend is in-process and when it's a remote service. Phase 2 can switch to
SQLAlchemy sessions for in-process use if needed.
"""

import datetime
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class BackendUnavailableError(Exception):
    """Raised when the v2 API is unreachable or returns an unexpected error."""
    pass


def _request(method: str, url: str, body: Any = None, timeout: int = 5) -> Any:
    """
    Minimal HTTP helper. Raises BackendUnavailableError on network or HTTP errors.
    Returns parsed JSON response body.
    """
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise BackendUnavailableError(f"HTTP {e.code}: {e.reason}") from e
    except Exception as e:
        raise BackendUnavailableError(str(e)) from e


class PostgresBackend:
    """
    Online backend — REST client for the v2 FastAPI service.
    Field names mirror board.json for meow.py compatibility.
    """

    def __init__(self, api_base: str):
        self.api_base = api_base.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.api_base}{path}"

    # ── Tasks ─────────────────────────────────────────────────────────────────

    def get_tasks(self, team_id: str | None = None) -> list[dict]:
        params = f"?team_id={urllib.parse.quote(team_id)}" if team_id else ""
        return _request("GET", self._url(f"/api/tasks{params}"))

    def claim_task(self, task_id: str, agent_name: str, claimed_at: str) -> bool:
        """
        First-claim-wins via atomic UPDATE on the server side.
        Returns True if this agent won the claim.
        """
        result = _request("POST", self._url(f"/api/tasks/{task_id}/claim"), {
            "agent_name": agent_name,
            "claimed_at": claimed_at,
        })
        return result.get("claimed", False)

    def complete_task(self, task_id: str, agent_name: str, result: str) -> bool:
        resp = _request("POST", self._url(f"/api/tasks/{task_id}/complete"), {
            "agent_name": agent_name,
            "result": result,
            "completed_at": datetime.datetime.now().isoformat(),
        })
        return resp.get("ok", False)

    def get_task(self, task_id: str) -> dict | None:
        try:
            return _request("GET", self._url(f"/api/tasks/{task_id}"))
        except BackendUnavailableError:
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
        resp = _request("POST", self._url(f"/api/channels/{channel}/messages"), {
            "content": content,
            "sender": sender,
            "type": message_type,
            "thread_id": thread_id,
            "metadata": metadata,
        })
        return resp.get("id", "")

    def read_messages(
        self,
        channel: str,
        limit: int = 20,
        message_type: str | None = None,
    ) -> list[dict]:
        params = f"?limit={limit}"
        if message_type:
            params += f"&type={urllib.parse.quote(message_type)}"
        return _request("GET", self._url(f"/api/channels/{channel}/messages{params}"))

    # ── Agents ────────────────────────────────────────────────────────────────

    def register_agent(
        self,
        name: str,
        role: str,
        team: str | None = None,
        model: str = "unknown",
    ) -> None:
        _request("POST", self._url("/api/agents/register"), {
            "name": name,
            "role": role,
            "team": team,
            "model": model,
        })

    def update_heartbeat(self, name: str) -> None:
        _request("POST", self._url(f"/api/agents/{name}/heartbeat"))

    # ── Tokens / Budget ───────────────────────────────────────────────────────

    def log_tokens(
        self,
        agent: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> dict:
        return _request("POST", self._url("/api/tokens/log"), {
            "agent": agent,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": model,
        })

    def check_budget(self, agent: str) -> dict:
        return _request("GET", self._url(f"/api/tokens/{agent}/budget"))

    # ── Conflicts / Sync ──────────────────────────────────────────────────────

    def log_conflict(self, conflict: dict) -> None:
        _request("POST", self._url("/api/conflicts"), conflict)

    # ── RAG / Profiles (available online only) ────────────────────────────────

    def search_context(self, query: str, top_k: int = 5) -> list[dict] | None:
        """Semantic search. Phase 2: returns real results. Phase 1: returns []."""
        try:
            return _request("POST", self._url("/api/rag/search"), {
                "query": query,
                "top_k": top_k,
            })
        except BackendUnavailableError:
            return None

    def get_agent_profile(self, agent_name: str) -> dict | None:
        try:
            return _request("GET", self._url(f"/api/agents/{agent_name}/profile"))
        except BackendUnavailableError:
            return None
