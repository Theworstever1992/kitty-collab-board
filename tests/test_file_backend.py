"""
tests/test_file_backend.py — Kitty Collab Board
Unit tests for FileBackend. No database required.
"""

import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest


@pytest.fixture()
def board_dir(monkeypatch, tmp_path):
    """Override CLOWDER_BOARD_DIR to a temp directory for each test."""
    monkeypatch.setenv("CLOWDER_BOARD_DIR", str(tmp_path))
    # Reload modules that cache BOARD_DIR at import time
    import importlib
    import agents.atomic
    import agents.channels
    import agents.file_backend
    import agents.context_manager
    importlib.reload(agents.atomic)
    importlib.reload(agents.channels)
    importlib.reload(agents.context_manager)
    importlib.reload(agents.file_backend)
    from agents.file_backend import FileBackend
    return tmp_path, FileBackend()


def _make_board(board_dir: Path, tasks: list[dict]) -> None:
    """Write a board.json with given tasks."""
    board_dir.mkdir(parents=True, exist_ok=True)
    (board_dir / "board.json").write_text(
        json.dumps({"tasks": tasks}), encoding="utf-8"
    )


# ── Tasks ─────────────────────────────────────────────────────────────────────

def test_get_tasks_empty(board_dir):
    tmp, fb = board_dir
    assert fb.get_tasks() == []


def test_get_tasks_returns_all(board_dir):
    tmp, fb = board_dir
    tasks = [
        {"id": "t1", "title": "First", "status": "pending"},
        {"id": "t2", "title": "Second", "status": "done"},
    ]
    _make_board(tmp, tasks)
    result = fb.get_tasks()
    assert len(result) == 2


def test_get_tasks_team_filter(board_dir):
    tmp, fb = board_dir
    tasks = [
        {"id": "t1", "title": "Team A task", "status": "pending", "team_id": "alpha"},
        {"id": "t2", "title": "Team B task", "status": "pending", "team_id": "beta"},
    ]
    _make_board(tmp, tasks)
    result = fb.get_tasks(team_id="alpha")
    assert len(result) == 1
    assert result[0]["id"] == "t1"


def test_claim_task_success(board_dir):
    tmp, fb = board_dir
    _make_board(tmp, [{"id": "t1", "title": "Work", "status": "pending"}])
    assert fb.claim_task("t1", "agent-a", "2026-03-08T10:00:00") is True
    board = json.loads((tmp / "board.json").read_text())
    task = board["tasks"][0]
    assert task["status"] == "claimed"
    assert task["claimed_by"] == "agent-a"


def test_claim_task_already_claimed(board_dir):
    tmp, fb = board_dir
    _make_board(tmp, [{"id": "t1", "title": "Work", "status": "claimed", "claimed_by": "agent-b"}])
    assert fb.claim_task("t1", "agent-a", "2026-03-08T10:00:00") is False


def test_complete_task(board_dir):
    tmp, fb = board_dir
    _make_board(tmp, [{"id": "t1", "title": "Work", "status": "claimed", "claimed_by": "agent-a"}])
    assert fb.complete_task("t1", "agent-a", "Done!") is True
    board = json.loads((tmp / "board.json").read_text())
    task = board["tasks"][0]
    assert task["status"] == "done"
    assert task["result"] == "Done!"


def test_get_task_found(board_dir):
    tmp, fb = board_dir
    _make_board(tmp, [{"id": "t42", "title": "Find me", "status": "pending"}])
    task = fb.get_task("t42")
    assert task is not None
    assert task["title"] == "Find me"


def test_get_task_not_found(board_dir):
    tmp, fb = board_dir
    _make_board(tmp, [])
    assert fb.get_task("nonexistent") is None


# ── Messages ──────────────────────────────────────────────────────────────────

def test_post_and_read_message(board_dir):
    tmp, fb = board_dir
    msg_id = fb.post_message("general", "Hello, board!", "test-agent")
    assert isinstance(msg_id, str)
    messages = fb.read_messages("general")
    assert any(m.get("content") == "Hello, board!" for m in messages)


def test_read_messages_empty_channel(board_dir):
    tmp, fb = board_dir
    result = fb.read_messages("nonexistent-channel")
    assert result == []


# ── Agents ────────────────────────────────────────────────────────────────────

def test_register_agent(board_dir):
    tmp, fb = board_dir
    fb.register_agent("claude", "coder", team="alpha", model="claude-sonnet-4-6")
    agents = json.loads((tmp / "agents.json").read_text())
    assert "claude" in agents
    assert agents["claude"]["role"] == "coder"
    assert agents["claude"]["model"] == "claude-sonnet-4-6"


def test_update_heartbeat(board_dir):
    tmp, fb = board_dir
    fb.register_agent("claude", "coder")
    first_seen = json.loads((tmp / "agents.json").read_text())["claude"]["last_seen"]
    import time; time.sleep(0.01)
    fb.update_heartbeat("claude")
    second_seen = json.loads((tmp / "agents.json").read_text())["claude"]["last_seen"]
    assert second_seen >= first_seen


# ── Conflicts ─────────────────────────────────────────────────────────────────

def test_log_conflict(board_dir):
    tmp, fb = board_dir
    fb.log_conflict({"task_id": "t1", "local_agent": "me", "remote_agent": "other"})
    conflicts = json.loads((tmp / "conflicts.json").read_text())
    assert len(conflicts) == 1
    assert conflicts[0]["task_id"] == "t1"


# ── RAG / Profile stubs ───────────────────────────────────────────────────────

def test_search_context_returns_none_offline(board_dir):
    tmp, fb = board_dir
    assert fb.search_context("anything") is None


def test_get_agent_profile_returns_none_offline(board_dir):
    tmp, fb = board_dir
    assert fb.get_agent_profile("claude") is None


# ── Protocol compliance ───────────────────────────────────────────────────────

def test_file_backend_satisfies_protocol(board_dir):
    """FileBackend must be recognized as BoardBackend at runtime."""
    from agents.backend_protocol import BoardBackend
    _, fb = board_dir
    assert isinstance(fb, BoardBackend)
