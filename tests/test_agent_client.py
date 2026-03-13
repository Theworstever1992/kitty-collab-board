"""
tests/test_agent_client.py — Kitty Collab Board
Unit tests for AgentClient. No database, no network required.

The key behaviors under test:
  - Offline-only mode uses FileBackend throughout
  - Online probe failure falls back to FileBackend silently
  - get_context() always returns a list (never None), even offline
  - format_context_for_prompt() returns "" when list is empty
  - sync_pending_completions() handles the case where _pg_backend is None
"""

import json
import importlib
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def board_dir(monkeypatch, tmp_path):
    """Override CLOWDER_BOARD_DIR and reload affected modules."""
    monkeypatch.setenv("CLOWDER_BOARD_DIR", str(tmp_path))
    import agents.atomic, agents.channels, agents.context_manager, agents.file_backend, agents.agent_client
    for mod in [agents.atomic, agents.channels, agents.context_manager, agents.file_backend, agents.agent_client]:
        importlib.reload(mod)
    return tmp_path


def _make_client(board_dir, api_base=None):
    from agents.agent_client import AgentClient
    return AgentClient("test-agent", role="coder", api_base=api_base), board_dir


# ── Offline mode ──────────────────────────────────────────────────────────────

def test_offline_client_uses_file_backend(board_dir):
    client, tmp = _make_client(board_dir)
    from agents.file_backend import FileBackend
    assert isinstance(client._active_backend(), FileBackend)


def test_offline_get_tasks_empty(board_dir):
    client, tmp = _make_client(board_dir)
    assert client.get_tasks() == []


def test_offline_post_and_read_message(board_dir):
    client, tmp = _make_client(board_dir)
    client.post_message("general", "hello from test")
    msgs = client.read_messages("general")
    assert any(m.get("content") == "hello from test" for m in msgs)


def test_offline_claim_task(board_dir):
    tmp = board_dir
    (tmp / "board.json").write_text(
        json.dumps({"tasks": [{"id": "t1", "title": "T", "status": "pending"}]}),
        encoding="utf-8",
    )
    client, _ = _make_client(tmp)
    assert client.claim_task("t1") is True


def test_offline_complete_task(board_dir):
    tmp = board_dir
    (tmp / "board.json").write_text(
        json.dumps({"tasks": [{"id": "t1", "title": "T", "status": "claimed", "claimed_by": "test-agent"}]}),
        encoding="utf-8",
    )
    client, _ = _make_client(tmp)
    assert client.complete_task("t1", "All done") is True


# ── Fallback on failed probe ───────────────────────────────────────────────────

def test_failed_probe_falls_back_silently(board_dir):
    """When api_base is set but unreachable, FileBackend is used — no exception."""
    client, tmp = _make_client(board_dir, api_base="http://localhost:19999")
    # Force probe timeout to be instant in tests
    client._PROBE_TIMEOUT = 0.01  # type: ignore[attr-defined]
    from agents.file_backend import FileBackend
    backend = client._active_backend()
    assert isinstance(backend, FileBackend)


# ── get_context / format_context_for_prompt ───────────────────────────────────

def test_get_context_offline_returns_empty_list(board_dir):
    client, _ = _make_client(board_dir)
    result = client.get_context("what is the answer")
    assert result == []  # Never None


def test_format_context_empty(board_dir):
    client, _ = _make_client(board_dir)
    assert client.format_context_for_prompt([]) == ""


def test_format_context_with_items(board_dir):
    client, _ = _make_client(board_dir)
    items = [{"text": "Task 1 was about auth", "source": "tasks", "score": 0.9}]
    result = client.format_context_for_prompt(items)
    assert "Relevant past context" in result
    assert "Task 1 was about auth" in result


# ── Budget / Tokens ───────────────────────────────────────────────────────────

def test_check_budget_offline(board_dir):
    client, _ = _make_client(board_dir)
    result = client.check_budget()
    assert isinstance(result, dict)


# ── Sync ──────────────────────────────────────────────────────────────────────

def test_sync_returns_zero_when_no_pg_backend(board_dir):
    client, _ = _make_client(board_dir)
    result = client.sync_pending_completions()
    assert result == {"pushed": 0, "conflicts": 0}


def test_sync_pushes_done_tasks_online(board_dir):
    tmp = board_dir
    (tmp / "board.json").write_text(
        json.dumps({"tasks": [
            {"id": "t1", "title": "T", "status": "done", "claimed_by": "test-agent", "result": "great"},
            {"id": "t2", "title": "U", "status": "done", "claimed_by": "other-agent", "result": "meh"},
        ]}),
        encoding="utf-8",
    )
    client, _ = _make_client(tmp)
    mock_pg = MagicMock()
    mock_pg.get_task.return_value = None      # task unknown to API
    mock_pg.complete_task.return_value = True
    client._pg_backend = mock_pg

    result = client.sync_pending_completions()
    assert result["pushed"] == 1             # only test-agent's task
    assert result["conflicts"] == 0


def test_sync_logs_conflict_when_task_claimed_by_other(board_dir):
    tmp = board_dir
    (tmp / "board.json").write_text(
        json.dumps({"tasks": [
            {"id": "t1", "title": "T", "status": "done", "claimed_by": "test-agent", "result": "r"},
        ]}),
        encoding="utf-8",
    )
    client, _ = _make_client(tmp)
    mock_pg = MagicMock()
    mock_pg.get_task.return_value = {"id": "t1", "claimed_by": "rival-agent", "status": "done"}
    client._pg_backend = mock_pg

    result = client.sync_pending_completions()
    assert result["conflicts"] == 1
    conflicts = json.loads((tmp / "conflicts.json").read_text())
    assert conflicts[0]["task_id"] == "t1"
