"""
base_agent.py — Kitty Collab Board
Base class for all agents on the board.

Includes handoff protocol implementation (TASK 4022-4023).
Updated with structured logging (TASK 6002).
"""

import json
import os
import time
import datetime
import traceback
from pathlib import Path
from typing import Optional

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False

# Import structured logging (TASK 6002)
try:
    from logging_config import setup_logging, get_logger
    import logging
    LOGGING_AVAILABLE = True
except ImportError:
    LOGGING_AVAILABLE = False


def load_agents() -> dict:
    """Load agents.json. Helper for handoff protocol."""
    from agents.base_agent import BOARD_DIR
    agents_file = BOARD_DIR / "agents.json"
    if not agents_file.exists():
        return {}
    try:
        return json.loads(agents_file.read_text(encoding="utf-8"))
    except Exception:
        return {}

# Import audit logging (TASK 802)
try:
    from agents.audit import (
        audit_task_claimed,
        audit_task_completed,
        audit_task_blocked,
        log_audit,
        AuditAction,
    )
    _audit_available = True
except ImportError:
    _audit_available = False


class _NoOpLock:
    """Fallback context manager when filelock is not installed."""
    def __enter__(self): return self
    def __exit__(self, *_): pass

BOARD_DIR = Path(
    os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board")
)
LOG_DIR = Path(os.environ.get("CLOWDER_LOG_DIR", Path(__file__).parent.parent / "logs"))


class BaseAgent:
    """All Clowder agents inherit from this class."""

    def __init__(self, name: str, model: str, role: str = "general", skills: list = None, log_level: int = 20):
        self.name = name
        self.model = model
        self.role = role
        # TASK 6021: Skills-based routing — declare what this agent can do
        # e.g. skills=["python", "react", "sql", "bash"]
        self.skills: list[str] = [s.lower() for s in (skills or [])]
        self.started_at = datetime.datetime.now().isoformat()
        self.status = "initializing"

        BOARD_DIR.mkdir(exist_ok=True)
        LOG_DIR.mkdir(exist_ok=True)
        
        # TASK 6002: Set up structured logging
        if LOGGING_AVAILABLE:
            self.logger = setup_logging(
                log_dir=LOG_DIR,
                agent_name=name,
                level=log_level,
                console_output=True
            )
        else:
            self.logger = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def _lock(self, file_path: Path):
        """Return a FileLock for the given path, or a no-op context if unavailable."""
        if FILELOCK_AVAILABLE:
            return FileLock(str(file_path) + ".lock", timeout=10)
        return _NoOpLock()

    def register(self):
        """Announce presence on the agents board."""
        agents_file = BOARD_DIR / "agents.json"
        with self._lock(agents_file):
            agents = {}
            if agents_file.exists():
                try:
                    agents = json.loads(agents_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    agents = {}
            agents[self.name] = {
                "model": self.model,
                "role": self.role,
                "skills": self.skills,
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
            with self._lock(agents_file):
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

    def get_tasks(self, role_filter: bool = True) -> list:
        """
        Read pending tasks from board.
        
        Args:
            role_filter: If True, filter out tasks with non-matching roles
        
        Returns:
            List of pending tasks (optionally role-filtered)
        """
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return []
        try:
            board = json.loads(board_file.read_text(encoding="utf-8"))
            tasks = [t for t in board.get("tasks", []) if t.get("status") == "pending"]
            
            # TASK 402: Role-based filtering
            # TASK 6021: Skills-based filtering (additional layer on top of role)
            if role_filter and self.role:
                filtered = []
                for t in tasks:
                    task_role = t.get("role")
                    task_skills = [s.lower() for s in (t.get("skills") or [])]

                    # Role check: task must have no role, or matching role
                    role_ok = task_role is None or task_role == self.role

                    # Skills check: if task requires skills, agent must have ALL of them
                    if task_skills and self.skills:
                        skills_ok = all(s in self.skills for s in task_skills)
                    elif task_skills and not self.skills:
                        skills_ok = False  # task needs skills, agent has none
                    else:
                        skills_ok = True  # task has no skill requirement

                    if role_ok and skills_ok:
                        filtered.append(t)

                filtered.sort(key=lambda t: (t.get("priority_order", 2), t.get("created_at", "")))
                return filtered
            
            # Sort by priority_order even without role filter
            tasks.sort(key=lambda t: (t.get("priority_order", 2), t.get("created_at", "")))
            return tasks
        except json.JSONDecodeError:
            return []

    def claim_task(self, task_id: str) -> bool:
        """Claim a task by ID. Returns True if successfully claimed."""
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return False
        try:
            with self._lock(board_file):
                board = json.loads(board_file.read_text(encoding="utf-8"))
                for task in board.get("tasks", []):
                    if task["id"] == task_id and task["status"] == "pending":
                        task["status"] = "in_progress"
                        task["claimed_by"] = self.name
                        task["claimed_at"] = datetime.datetime.now().isoformat()
                        board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
                        self.log(f"Claimed task: {task_id}")
                        # TASK 802: Log audit event
                        if _audit_available:
                            audit_task_claimed(task, self.name)
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
            task_snapshot = None
            with self._lock(board_file):
                board = json.loads(board_file.read_text(encoding="utf-8"))
                for task in board.get("tasks", []):
                    if task["id"] == task_id:
                        task_snapshot = task.copy()
                        task["status"] = "done"
                        task["completed_by"] = self.name
                        task["completed_at"] = datetime.datetime.now().isoformat()
                        task["result"] = result
                        break
                board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
            self.log(f"Completed task: {task_id}")
            # TASK 802: Log audit event
            if _audit_available and task_snapshot:
                audit_task_completed(task_snapshot, self.name, result)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Logging (TASK 6002 — Structured Logging)
    # ------------------------------------------------------------------

    def log(self, message: str, level: str = "INFO"):
        """
        Log a message using structured logging.
        Falls back to custom logging if logging_config not available.
        
        Args:
            message: Log message
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if self.logger and LOGGING_AVAILABLE:
            # Use structured logging
            log_func = getattr(self.logger, level.lower(), self.logger.info)
            log_func(message)
        else:
            # Fallback to custom logging
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"[{ts}] [{level}] [{self.name}] {message}"
            print(entry)
            log_file = LOG_DIR / f"{self.name}.log"
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(entry + "\n")
            except Exception:
                pass

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
                        try:
                            result = self.handle_task(task)
                            self.complete_task(task["id"], result)
                        except Exception as e:
                            # Task failed - mark as blocked and continue
                            self.log(f"Task {task['id']} failed: {e}", "ERROR")
                            self.log(f"Traceback: {traceback.format_exc()}", "DEBUG")
                            self._mark_blocked(task["id"], reason=str(e))
                            # Continue running - don't crash
                time.sleep(5)
        except KeyboardInterrupt:
            self.log("Shutting down.")
            self.deregister()

    def _mark_blocked(self, task_id: str, reason: str):
        """Mark a task as blocked with a reason."""
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return
        try:
            with self._lock(board_file):
                board = json.loads(board_file.read_text(encoding="utf-8"))
                for task in board.get("tasks", []):
                    if task["id"] == task_id:
                        task["status"] = "blocked"
                        task["blocked_by"] = self.name
                        task["blocked_at"] = datetime.datetime.now().isoformat()
                        task["block_reason"] = reason
                        break
                board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
            self.log(f"Marked task {task_id} as blocked: {reason}")
        except Exception as e:
            self.log(f"Failed to mark task blocked: {e}", "ERROR")

    # ------------------------------------------------------------------
    # Handoff Protocol (TASK 4022-4023)
    # ------------------------------------------------------------------

    def handoff_task(self, task_id: str, target_agent: str, notes: str) -> bool:
        """
        Initiate handoff of a task to another agent.
        
        Args:
            task_id: ID of task to hand off
            target_agent: Name of agent to receive task
            notes: Context notes for receiving agent
        
        Returns:
            True if handoff initiated successfully
        """
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return False
        
        # Check if target agent is available
        agents = load_agents()
        if target_agent not in agents:
            self.log(f"Handoff failed: agent '{target_agent}' not found", "ERROR")
            return False
        
        agent_info = agents[target_agent]
        if agent_info.get("status") != "online":
            self.log(f"Handoff failed: agent '{target_agent}' is offline", "ERROR")
            return False
        
        try:
            with self._lock(board_file):
                board = json.loads(board_file.read_text(encoding="utf-8"))
                
                for task in board.get("tasks", []):
                    if task["id"] == task_id:
                        # Verify we own this task
                        if task.get("claimed_by") != self.name:
                            self.log(f"Handoff failed: task not claimed by us", "ERROR")
                            return False
                        
                        # Set up handoff
                        task["handoff"] = {
                            "from": self.name,
                            "to": target_agent,
                            "at": datetime.datetime.now().isoformat(),
                            "notes": notes,
                            "status": "pending_acceptance",
                            "accepted_at": None,
                            "declined_at": None,
                            "decline_reason": None,
                            "expired_at": None,
                        }
                        
                        board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
                        self.log(f"Handoff initiated: {task_id} → {target_agent}")
                        return True
                
                self.log(f"Handoff failed: task {task_id} not found", "ERROR")
                return False
        except Exception as e:
            self.log(f"Handoff failed: {e}", "ERROR")
            return False
    
    def accept_handoff(self, task_id: str) -> bool:
        """
        Accept a handed-off task.
        
        Args:
            task_id: ID of task to accept
        
        Returns:
            True if acceptance successful
        """
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return False
        
        try:
            with self._lock(board_file):
                board = json.loads(board_file.read_text(encoding="utf-8"))
                
                for task in board.get("tasks", []):
                    if task["id"] == task_id:
                        handoff = task.get("handoff", {})
                        
                        # Verify handoff is for us
                        if handoff.get("to") != self.name:
                            self.log(f"Accept failed: handoff not for us", "ERROR")
                            return False
                        
                        # Verify handoff is pending
                        if handoff.get("status") != "pending_acceptance":
                            self.log(f"Accept failed: handoff not pending (status={handoff.get('status')})", "ERROR")
                            return False
                        
                        # Accept the handoff
                        task["claimed_by"] = self.name
                        task["handoff"]["status"] = "accepted"
                        task["handoff"]["accepted_at"] = datetime.datetime.now().isoformat()
                        
                        board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
                        self.log(f"Handoff accepted: {task_id} (from {handoff.get('from')})")
                        return True
                
                self.log(f"Accept failed: task {task_id} not found", "ERROR")
                return False
        except Exception as e:
            self.log(f"Accept failed: {e}", "ERROR")
            return False
    
    def decline_handoff(self, task_id: str, reason: str) -> bool:
        """
        Decline a handed-off task.
        
        Args:
            task_id: ID of task to decline
            reason: Reason for declining
        
        Returns:
            True if decline recorded successfully
        """
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return False
        
        try:
            with self._lock(board_file):
                board = json.loads(board_file.read_text(encoding="utf-8"))
                
                for task in board.get("tasks", []):
                    if task["id"] == task_id:
                        handoff = task.get("handoff", {})
                        
                        # Verify handoff is for us
                        if handoff.get("to") != self.name:
                            self.log(f"Decline failed: handoff not for us", "ERROR")
                            return False
                        
                        # Decline the handoff — reset task to claimable pending state
                        task["status"] = "pending"
                        task["claimed_by"] = None
                        task["claimed_at"] = None
                        task["handoff"]["status"] = "declined"
                        task["handoff"]["declined_at"] = datetime.datetime.now().isoformat()
                        task["handoff"]["decline_reason"] = reason

                        board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
                        self.log(f"Handoff declined: {task_id} (reason: {reason})")
                        return True
                
                self.log(f"Decline failed: task {task_id} not found", "ERROR")
                return False
        except Exception as e:
            self.log(f"Decline failed: {e}", "ERROR")
            return False
    
    def get_pending_handoffs(self) -> list[dict]:
        """
        Get list of handoff requests waiting for this agent's response.
        
        Returns:
            List of handoff request dicts
        """
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return []
        
        try:
            board = json.loads(board_file.read_text(encoding="utf-8"))
            pending = []
            
            for task in board.get("tasks", []):
                handoff = task.get("handoff", {})
                if (handoff.get("to") == self.name and 
                    handoff.get("status") == "pending_acceptance"):
                    pending.append({
                        "task_id": task["id"],
                        "task_title": task.get("title", "Unknown"),
                        "from": handoff.get("from"),
                        "notes": handoff.get("notes"),
                        "at": handoff.get("at"),
                    })
            
            return pending
        except Exception as e:
            self.log(f"Error getting pending handoffs: {e}", "ERROR")
            return []
    
    def cancel_handoff(self, task_id: str) -> bool:
        """
        Cancel a pending handoff (source agent only).
        
        Args:
            task_id: ID of task to cancel handoff for
        
        Returns:
            True if cancellation successful
        """
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return False
        
        try:
            with self._lock(board_file):
                board = json.loads(board_file.read_text(encoding="utf-8"))
                
                for task in board.get("tasks", []):
                    if task["id"] == task_id:
                        handoff = task.get("handoff", {})
                        
                        # Verify we initiated this handoff
                        if handoff.get("from") != self.name:
                            self.log(f"Cancel failed: we didn't initiate this handoff", "ERROR")
                            return False
                        
                        # Verify handoff is still pending
                        if handoff.get("status") != "pending_acceptance":
                            self.log(f"Cancel failed: handoff not pending", "ERROR")
                            return False
                        
                        # Cancel the handoff
                        task["handoff"]["status"] = "cancelled"
                        
                        board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
                        self.log(f"Handoff cancelled: {task_id}")
                        return True
                
                self.log(f"Cancel failed: task {task_id} not found", "ERROR")
                return False
        except Exception as e:
            self.log(f"Cancel failed: {e}", "ERROR")
            return False
    
    def check_handoff_expiry(self):
        """
        Check for expired handoffs and mark them as expired.
        Call this periodically (e.g., every minute).
        """
        board_file = BOARD_DIR / "board.json"
        if not board_file.exists():
            return
        
        try:
            with self._lock(board_file):
                board = json.loads(board_file.read_text(encoding="utf-8"))
                now = datetime.datetime.now()
                expired_count = 0
                
                for task in board.get("tasks", []):
                    handoff = task.get("handoff", {})
                    if handoff.get("status") == "pending_acceptance":
                        handoff_at = handoff.get("at")
                        if handoff_at:
                            handoff_time = datetime.datetime.fromisoformat(handoff_at)
                            age_minutes = (now - handoff_time).total_seconds() / 60
                            
                            if age_minutes > 10:  # 10 minute timeout
                                task["handoff"]["status"] = "expired"
                                task["handoff"]["expired_at"] = now.isoformat()
                                expired_count += 1
                                self.log(f"Handoff expired: {task['id']}")
                
                if expired_count > 0:
                    board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
        except Exception as e:
            self.log(f"Error checking handoff expiry: {e}", "ERROR")

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
            with self._lock(agents_file):
                agents = json.loads(agents_file.read_text(encoding="utf-8"))
                if self.name in agents:
                    agents[self.name]["last_seen"] = datetime.datetime.now().isoformat()
                    agents_file.write_text(json.dumps(agents, indent=2), encoding="utf-8")
        except Exception:
            pass
