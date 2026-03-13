"""
tests/test_phase1.py — Kitty Collab Board v2
Sprint 1 integration tests: schema validation + file-backend contract.

Test 1 (test_all_tables_exist) requires the postgres-test container on port 5433.
Tests 2-5 are file-only and run without any database.
"""

import datetime
import importlib
import json
import uuid
from pathlib import Path

import pytest


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_board(board_dir: Path, tasks: list[dict]) -> None:
    """Write a board.json with given tasks into board_dir."""
    board_dir.mkdir(parents=True, exist_ok=True)
    (board_dir / "board.json").write_text(
        json.dumps({"tasks": tasks}), encoding="utf-8"
    )


def _reload_file_modules(tmp_path: Path, monkeypatch) -> None:
    """Set CLOWDER_BOARD_DIR and reload all file-based modules that cache it at import time."""
    monkeypatch.setenv("CLOWDER_BOARD_DIR", str(tmp_path))
    import agents.atomic
    import agents.channels
    import agents.context_manager
    import agents.file_backend
    import agents.agent_client
    for mod in [
        agents.atomic,
        agents.channels,
        agents.context_manager,
        agents.file_backend,
        agents.agent_client,
    ]:
        importlib.reload(mod)


# ── Test 1: Schema validation (requires postgres-test on port 5433) ───────────

async def test_all_tables_exist(test_engine):
    """All v2 ORM tables must be present in the public schema after create_all."""
    from sqlalchemy import text

    expected_tables = [
        "tasks",
        "agents",
        "chat_messages",
        "token_usage",
        "teams",
        "task_history",
        "task_embeddings",
        "context_items",
        "message_reactions",
        "trending_discussions",
        "ideas",
        "idea_votes",
        "standards_violations",
        "agent_exports",
    ]

    async with test_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
        )
        actual = {row[0] for row in result}

    for table in expected_tables:
        assert table in actual, f"Missing table: {table}"


# ── Test 2: AgentClient falls back to FileBackend when API is unreachable ─────

def test_agent_client_falls_back_to_file_backend(tmp_path, monkeypatch):
    """When the v2 API is unreachable, AgentClient transparently uses FileBackend."""
    _reload_file_modules(tmp_path, monkeypatch)

    from agents.agent_client import AgentClient

    # Port 19999 — nothing is listening there
    client = AgentClient(
        "test-agent", role="tester", api_base="http://localhost:19999"
    )

    # Must not raise; result must be a list (possibly empty)
    tasks = client.get_tasks()
    assert isinstance(tasks, list)

    # AgentClient auto-registers on init → agents.json must have been written
    assert (tmp_path / "agents.json").exists()

    # Internal flag must remain False after a failed probe
    assert client._online is False


# ── Test 3: Task claim and complete via FileBackend ───────────────────────────

def test_file_backend_claim_and_complete(tmp_path, monkeypatch):
    """Agent can claim a pending task and mark it complete via FileBackend."""
    _reload_file_modules(tmp_path, monkeypatch)
    from agents.file_backend import FileBackend

    backend = FileBackend()
    task_id = str(uuid.uuid4())[:8]

    _make_board(
        tmp_path,
        [
            {
                "id": task_id,
                "title": "Test task",
                "status": "pending",
                "claimed_by": None,
                "result": None,
            }
        ],
    )

    # Signature: claim_task(task_id, agent_name, claimed_at)
    claimed_at = datetime.datetime.now().isoformat()
    assert backend.claim_task(task_id, "test-agent", claimed_at) is True

    # complete_task requires claimed_by == agent_name on the task record
    assert backend.complete_task(task_id, "test-agent", "Task done!") is True

    board = json.loads((tmp_path / "board.json").read_text())
    task = next(t for t in board["tasks"] if t["id"] == task_id)
    assert task["status"] == "done"
    assert task["result"] == "Task done!"


# ── Test 4: Conflict detection — second claim on an already-claimed task ──────

def test_conflict_logged_when_task_already_claimed(tmp_path, monkeypatch):
    """
    The first agent to claim a pending task wins.
    A second claim attempt must return False and must not transfer ownership.
    """
    _reload_file_modules(tmp_path, monkeypatch)
    from agents.file_backend import FileBackend

    task_id = str(uuid.uuid4())[:8]
    _make_board(
        tmp_path,
        [
            {
                "id": task_id,
                "title": "Contested task",
                "status": "pending",
                "claimed_by": None,
                "result": None,
            }
        ],
    )

    ts = datetime.datetime.now().isoformat()
    b1 = FileBackend()
    b2 = FileBackend()

    r1 = b1.claim_task(task_id, "agent-alpha", ts)
    r2 = b2.claim_task(task_id, "agent-beta", ts)

    # First claim wins
    assert r1 is True
    # Second claim must be rejected (task is no longer "pending")
    assert r2 is False

    board = json.loads((tmp_path / "board.json").read_text())
    task = next(t for t in board["tasks"] if t["id"] == task_id)
    assert task.get("claimed_by") == "agent-alpha"


# ── Test 5: Channel post and read ─────────────────────────────────────────────

def test_channel_post_and_read(tmp_path, monkeypatch):
    """Messages posted to a channel are readable back with correct fields."""
    _reload_file_modules(tmp_path, monkeypatch)

    # Import Channel *after* reload so the module-level CHANNELS_DIR resolves to tmp_path
    from agents.channels import Channel

    ch = Channel("test-channel")
    ch.create()  # creates the directory under CHANNELS_DIR

    msg_id = ch.post("Hello from test", sender="gemini", message_type="chat")
    assert msg_id is not None

    messages = ch.read(limit=10)
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello from test"
    assert messages[0]["sender"] == "gemini"


# ── Test 6: PM supervised mode ────────────────────────────────────────────────

def test_pm_supervised_mode(tmp_path, monkeypatch):
    """
    PmAgent.propose_plan() creates a pending-approval plan in .approvals.json
    but does NOT dispatch any in-progress tasks to board.json without approval.
    A message is also posted to #main-hall about the proposal.
    """
    _reload_file_modules(tmp_path, monkeypatch)

    # Reload war_room and pm_agent so their module-level BOARD_DIR / APPROVALS_FILE
    # and the global _war_room singleton are reset to use tmp_path.
    import agents.war_room
    import agents.pm_agent
    importlib.reload(agents.war_room)
    importlib.reload(agents.pm_agent)

    # Reset the global war room singleton so it re-creates against tmp_path
    agents.war_room._war_room = None

    from agents.pm_agent import PmAgent

    # ── 1. Create a task in board/pm_tasks.json ────────────────────────────
    pm_tasks_file = tmp_path / "pm_tasks.json"
    task = {
        "id": "test-pm-001",
        "title": "Build the widget",
        "description": "Implement the core widget module.",
        "status": "pending",
    }
    pm_tasks_file.write_text(
        json.dumps({"tasks": [task]}), encoding="utf-8"
    )

    # ── 2. Instantiate PmAgent with tmp_path as board_dir ─────────────────
    agent = PmAgent(name="pm-test", board_dir=tmp_path)

    # ── 3. Call propose_plan directly (avoid the infinite run() loop) ──────
    plan_id = agent.propose_plan(task)
    assert plan_id is not None and plan_id.startswith("plan_")

    # ── 4. Assert plan was created in .approvals.json ─────────────────────
    approvals_file = tmp_path / ".approvals.json"
    assert approvals_file.exists(), ".approvals.json was not created"
    approvals_data = json.loads(approvals_file.read_text(encoding="utf-8"))
    plans = approvals_data.get("plans", {})
    assert plan_id in plans, f"plan_id {plan_id!r} not found in .approvals.json"
    plan = plans[plan_id]
    assert plan["status"] == "pending_approval"

    # ── 5. Assert NO in-progress tasks were dispatched to board.json ───────
    board_file = tmp_path / "board.json"
    if board_file.exists():
        board_data = json.loads(board_file.read_text(encoding="utf-8"))
        in_progress = [
            t for t in board_data.get("tasks", [])
            if t.get("status") == "in-progress"
        ]
        assert in_progress == [], (
            f"PM dispatched tasks without approval: {in_progress}"
        )

    # ── 6. Assert a message was posted to #main-hall about the proposal ────
    main_hall_dir = tmp_path / "channels" / "main-hall"
    assert main_hall_dir.exists(), "#main-hall channel directory was not created"
    msg_files = sorted(main_hall_dir.glob("*.json"))
    assert len(msg_files) > 0, "No messages were posted to #main-hall"
    contents = [
        json.loads(f.read_text(encoding="utf-8")).get("content", "")
        for f in msg_files
    ]
    assert any(plan_id in c for c in contents), (
        f"plan_id {plan_id!r} not mentioned in any #main-hall message. "
        f"Messages: {contents}"
    )
