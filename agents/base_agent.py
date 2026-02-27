"""
base_agent.py — Kitty Collab Board
Base class for all agents on the board.
"""

import json
import os
import time
import datetime
from pathlib import Path

BOARD_DIR = Path(__file__).parent.parent / "board"
LOG_DIR = Path(__file__).parent.parent / "logs"


class BaseAgent:
    """All Clowder agents inherit from this class."""

    def __init__(self, name: str, model: str, role: str = "general"):
        self.name = name
        self.model = model
        self.role = role
        self.started_at = datetime.datetime.now().isoformat()
        self.status = "initializing"

        BOARD_DIR.mkdir(exist_ok=True)
        LOG_DIR.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self):
        """Announce presence on the agents board."""
        agents_file = BOARD_DIR / "agents.json"
        agents = {}
        if agents_file.exists():
            try:
                agents = json.loads(agents_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                agents = {}

        agents[self.name] = {
            "model": self.model,
            "role": self.role,
            "status": "online",
            "started_at": self.started_at,
            "last_seen": datetime.datetime.now().isoformat(),
        }
        agents_file.write_text(json.dumps(agents, indent=2), encoding="utf-8")
        self.log(f"Registered on board as '{self.name}'")

    def deregister(self):
        """Mark agent as offline."""
        agents_file = BOARD_DIR / "agents.json"
        if not agents_file.exists():
            return
        try:
            agents = json.loads(agents_file.read_text(encoding="utf-8"))
            if self.name in agents:
                agents[self.name]["status"] = "offline"
                agents[self.name]["last_seen"] = datetime.datetime.now().isoformat()
                agents_file.write_text(json.dumps(agents, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Board interaction
    # ------------------------------------------------------------------

    def get_tasks(self) -> list:
        """Read pending tasks from board."""
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return []
        try:
            board = json.loads(board_file.read_text(encoding="utf-8"))
            return [t for t in board.get("tasks", []) if t.get("status") == "pending"]
        except json.JSONDecodeError:
            return []

    def claim_task(self, task_id: str) -> bool:
        """Claim a task by ID. Returns True if successfully claimed."""
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return False
        try:
            board = json.loads(board_file.read_text(encoding="utf-8"))
            for task in board.get("tasks", []):
                if task["id"] == task_id and task["status"] == "pending":
                    task["status"] = "in_progress"
                    task["claimed_by"] = self.name
                    task["claimed_at"] = datetime.datetime.now().isoformat()
                    board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
                    self.log(f"Claimed task: {task_id}")
                    return True
        except Exception:
            pass
        return False

    def complete_task(self, task_id: str, result: str = ""):
        """Mark a task as done."""
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return
        try:
            board = json.loads(board_file.read_text(encoding="utf-8"))
            for task in board.get("tasks", []):
                if task["id"] == task_id:
                    task["status"] = "done"
                    task["completed_by"] = self.name
                    task["completed_at"] = datetime.datetime.now().isoformat()
                    task["result"] = result
                    break
            board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
            self.log(f"Completed task: {task_id}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log(self, message: str, level: str = "INFO"):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{ts}] [{level}] [{self.name}] {message}"
        print(entry)
        log_file = LOG_DIR / f"{self.name}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    # ------------------------------------------------------------------
    # Main loop — override in subclasses
    # ------------------------------------------------------------------

    def run(self):
        """Main agent loop. Override in subclasses."""
        self.register()
        self.log("Awake and standing by.")
        self.status = "idle"
        try:
            while True:
                self._heartbeat()
                tasks = self.get_tasks()
                if tasks:
                    task = tasks[0]
                    if self.claim_task(task["id"]):
                        result = self.handle_task(task)
                        self.complete_task(task["id"], result)
                time.sleep(5)
        except KeyboardInterrupt:
            self.log("Shutting down.")
            self.deregister()

    def handle_task(self, task: dict) -> str:
        """Override this in agent subclasses."""
        self.log(f"Received task: {task.get('title', 'unknown')}")
        return "Task received but no handler implemented."

    def _heartbeat(self):
        """Update last_seen timestamp."""
        agents_file = BOARD_DIR / "agents.json"
        if not agents_file.exists():
            return
        try:
            agents = json.loads(agents_file.read_text(encoding="utf-8"))
            if self.name in agents:
                agents[self.name]["last_seen"] = datetime.datetime.now().isoformat()
                agents_file.write_text(json.dumps(agents, indent=2), encoding="utf-8")
        except Exception:
            pass
