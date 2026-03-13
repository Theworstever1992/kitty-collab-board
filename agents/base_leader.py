"""
base_leader.py — Base class for Team Leader agents.

Team Leaders:
- Poll board/board.json for tasks assigned to their team (assigned_to_team == team_id)
- Maintain board/teams/<team_id>/board.json for their own agents
- Can spawn agents for their team
- Can send feedback to agents
- Report results back to PM via #war-room

Usage::

    from agents.base_leader import BaseLeader

    class MyCodingLeader(BaseLeader):
        def handle_task(self, task: dict) -> str:
            # implement team-specific logic here
            return "Done."

    leader = MyCodingLeader(name="coding-lead", team_id="coding")
    leader.run()
"""

import datetime
import time
import uuid
from pathlib import Path
from typing import Optional

from agents.atomic import atomic_read, atomic_write

POLL_INTERVAL = 5  # seconds


class BaseLeader:
    """
    Base class for Team Leader agents.

    Subclass and override ``handle_task()`` to implement team-specific logic.
    All board reads/writes go through ``atomic_read`` / ``atomic_write``.
    """

    def __init__(self, name: str, team_id: str, board_dir: Path = Path("board")):
        self.name = name
        self.team_id = team_id
        self.board_dir = board_dir
        self.team_board_dir = board_dir / "teams" / team_id
        self.team_board_dir.mkdir(parents=True, exist_ok=True)
        self.team_board_file = self.team_board_dir / "board.json"
        self.is_leader = True

        from agents.channels import get_or_create_channel
        self._get_or_create_channel = get_or_create_channel

    # ── Main board operations ──────────────────────────────────────────────────

    def get_assigned_tasks(self) -> list[dict]:
        """Return tasks from the main board assigned to this team with status 'pending'."""
        board = atomic_read(self.board_dir / "board.json", {"tasks": []})
        return [
            t for t in board.get("tasks", [])
            if t.get("assigned_to_team") == self.team_id
            and t.get("status") == "pending"
        ]

    def claim_task(self, task_id: str) -> bool:
        """
        Claim a pending task from the main board for this team.

        Uses atomic read-modify-write. Returns True only if the task was still
        'pending' at the time of the write (first-claim-wins semantics).
        """
        board_file = self.board_dir / "board.json"
        board = atomic_read(board_file, {"tasks": []})

        claimed = False
        for task in board.get("tasks", []):
            if task.get("id") == task_id and task.get("status") == "pending":
                task["status"] = "claimed"
                task["claimed_by"] = self.name
                task["claimed_at"] = datetime.datetime.utcnow().isoformat()
                claimed = True
                break

        if claimed:
            atomic_write(board_file, board)

        return claimed

    def complete_task(self, task_id: str, result: str) -> None:
        """Mark a task complete on the main board with the given result."""
        board_file = self.board_dir / "board.json"
        board = atomic_read(board_file, {"tasks": []})

        for task in board.get("tasks", []):
            if task.get("id") == task_id and task.get("claimed_by") == self.name:
                task["status"] = "done"
                task["result"] = result
                task["completed_at"] = datetime.datetime.utcnow().isoformat()
                break

        atomic_write(board_file, board)

    # ── Team board operations ──────────────────────────────────────────────────

    def spawn_agent(self, config: dict) -> str:
        """
        Register a new agent for this team by writing to board/teams/<team_id>/board.json.

        Args:
            config: Dict with keys: name, role, model, personality_seed (all optional
                    except name).

        Returns:
            The new agent's id string.
        """
        agent_id = uuid.uuid4().hex[:12]
        team_board = atomic_read(self.team_board_file, {"agents": []})

        agent_entry = {
            "id": agent_id,
            "name": config.get("name", agent_id),
            "role": config.get("role", "worker"),
            "model": config.get("model", "unknown"),
            "personality_seed": config.get("personality_seed", ""),
            "team_id": self.team_id,
            "spawned_by": self.name,
            "spawned_at": datetime.datetime.utcnow().isoformat(),
            "status": "idle",
        }

        team_board.setdefault("agents", []).append(agent_entry)
        atomic_write(self.team_board_file, team_board)

        return agent_id

    # ── Messaging ──────────────────────────────────────────────────────────────

    def send_feedback(self, agent_name: str, feedback_text: str) -> None:
        """Post feedback to the team channel, mentioning the target agent by name."""
        team_channel = f"team-{self.team_id}"
        try:
            ch = self._get_or_create_channel(team_channel, f"Team {self.team_id} channel")
            ch.post(
                f"@{agent_name} Feedback: {feedback_text}",
                sender=self.name,
                message_type="chat",
            )
        except Exception:
            pass

    def post_to_team(self, content: str, message_type: str = "chat") -> None:
        """Post a message to this team's channel."""
        team_channel = f"team-{self.team_id}"
        try:
            ch = self._get_or_create_channel(team_channel, f"Team {self.team_id} channel")
            ch.post(content, sender=self.name, message_type=message_type)
        except Exception:
            pass

    # ── Override in subclass ───────────────────────────────────────────────────

    def handle_task(self, task: dict) -> str:
        """
        Override in subclass to implement team-specific task handling.

        Args:
            task: Task dict from the main board.

        Returns:
            Result string that will be written back to the board.
        """
        return (
            f"Task {task['id']} acknowledged by {self.name}. "
            "Override handle_task() in subclass."
        )

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Main poll loop. Runs forever until interrupted."""
        print(f"[{self.name}] Team leader starting. Team: {self.team_id}")
        self.post_to_team(f"{self.name} (team leader) is online. Ready to receive tasks.")

        while True:
            try:
                tasks = self.get_assigned_tasks()
                for task in tasks:
                    if self.claim_task(task["id"]):
                        result = self.handle_task(task)
                        self.complete_task(task["id"], result)
                        self.post_to_team(
                            f"Task {task['id']} complete: {result[:100]}",
                            message_type="update",
                        )
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
            time.sleep(POLL_INTERVAL)
