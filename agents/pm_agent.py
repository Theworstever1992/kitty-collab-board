"""
pm_agent.py — Project Manager Agent (supervised mode)

Polls board/pm_tasks.json for user-assigned tasks.
Decomposes tasks and posts proposals to #war-room instead of dispatching directly.
Human approves via: python3 meow.py war-room approve <plan_id>

Supervised mode: NEVER dispatches tasks autonomously — all plans require human approval.
"""

import json
import time
import datetime
import uuid
from pathlib import Path

from agents.atomic import atomic_read, atomic_write

BOARD_DIR = Path("board")
PM_TASKS_FILE = BOARD_DIR / "pm_tasks.json"
POLL_INTERVAL = 5  # seconds


class PmAgent:
    """
    Project Manager Agent — supervised mode.

    Reads from board/pm_tasks.json and creates approval plans in #war-room.
    Tasks in pm_tasks.json must have at minimum: {id, title, description, status}.
    """

    def __init__(self, name: str = "pm", board_dir: Path = BOARD_DIR):
        self.name = name
        self.board_dir = board_dir
        self.pm_tasks_file = board_dir / "pm_tasks.json"

        # War room for supervised proposal flow
        from agents.war_room import get_war_room
        self.war_room = get_war_room()

        # Channel manager for status updates
        from agents.channels import get_or_create_channel
        self._get_or_create_channel = get_or_create_channel

    def get_pending_tasks(self) -> list[dict]:
        """Read pm_tasks.json and return tasks with status == 'pending'."""
        data = atomic_read(self.pm_tasks_file, {"tasks": []})
        return [
            t for t in data.get("tasks", [])
            if t.get("status") == "pending"
        ]

    def mark_task_processing(self, task_id: str) -> None:
        """Mark a PM task as 'processing' so it is not re-picked on the next poll."""
        data = atomic_read(self.pm_tasks_file, {"tasks": []})
        for task in data.get("tasks", []):
            if task.get("id") == task_id:
                task["status"] = "processing"
                task["processing_started_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                break
        atomic_write(self.pm_tasks_file, data)

    def propose_plan(self, task: dict) -> str:
        """
        Decompose a task into subtasks and post to #war-room for human approval.

        Returns the plan_id.
        In supervised mode: NEVER dispatches without approval.
        """
        title = task.get("title", "Untitled task")
        description = task.get("description", "No description provided.")
        task_id = task.get("id", "unknown")

        # Generic 3-subtask decomposition based on task title
        subtasks = [
            {
                "title": f"[{title}] — Analysis & Planning",
                "description": (
                    f"Analyze requirements for task '{title}'. "
                    "Identify dependencies, risks, and acceptance criteria."
                ),
                "assignee": "general",
                "priority": "high",
            },
            {
                "title": f"[{title}] — Implementation",
                "description": (
                    f"Implement the core work for task '{title}'. "
                    "Follow the plan from the analysis phase."
                ),
                "assignee": "general",
                "priority": "high",
            },
            {
                "title": f"[{title}] — Review & Verification",
                "description": (
                    f"Review and verify the implementation for task '{title}'. "
                    "Confirm acceptance criteria are met and report results."
                ),
                "assignee": "general",
                "priority": "normal",
            },
        ]

        plan_result = self.war_room.create_approval_plan(
            title=f"PM Plan: {title}",
            description=(
                f"Automatically decomposed from PM task `{task_id}`.\n\n"
                f"**Original description:** {description}"
            ),
            tasks=subtasks,
            coordinator=self.name,
        )

        plan_id = plan_result["plan_id"]

        # Post status update to #main-hall
        self._post_to_channel(
            "main-hall",
            f"PM received task `{task_id}` ({title}). "
            f"Proposal `{plan_id}` posted to #war-room — awaiting human approval.",
        )

        # Mark the original PM task as proposed
        data = atomic_read(self.pm_tasks_file, {"tasks": []})
        for t in data.get("tasks", []):
            if t.get("id") == task_id:
                t["status"] = "proposed"
                t["plan_id"] = plan_id
                t["proposed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                break
        atomic_write(self.pm_tasks_file, data)

        return plan_id

    def run(self) -> None:
        """Main poll loop. Runs forever until interrupted."""
        print(f"[PM Agent] Starting in supervised mode. Polling {self.pm_tasks_file}")
        self._post_to_channel(
            "main-hall",
            "PM Agent online. Supervised mode — all plans require human approval via #war-room.",
        )

        while True:
            try:
                tasks = self.get_pending_tasks()
                for task in tasks:
                    self.mark_task_processing(task["id"])
                    plan_id = self.propose_plan(task)
                    print(f"[PM Agent] Proposed plan {plan_id} for task {task['id']}")
            except Exception as e:
                print(f"[PM Agent] Error: {e}")
            time.sleep(POLL_INTERVAL)

    def _post_to_channel(self, channel: str, content: str) -> None:
        """Post a message to a channel, silently ignoring failures."""
        try:
            ch = self._get_or_create_channel(channel, "")
            ch.post(content, sender=self.name, message_type="chat")
        except Exception:
            pass


def main():
    agent = PmAgent()
    agent.run()


if __name__ == "__main__":
    main()
