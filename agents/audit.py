"""
audit.py — Kitty Collab Board
Audit logging for all board state changes.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, Dict
from contextlib import contextmanager

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False


BOARD_DIR = Path(os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board"))
AUDIT_FILE = BOARD_DIR / "audit.json"


class _NoOpLock:
    """Fallback context manager when filelock is not installed."""
    def __enter__(self): return self
    def __exit__(self, *_): pass


def _lock(file_path: Path):
    """Return a FileLock for the given path, or a no-op context if unavailable."""
    if FILELOCK_AVAILABLE:
        return FileLock(str(file_path) + ".lock", timeout=10)
    return _NoOpLock()


class AuditAction:
    """Constants for audit action types."""
    TASK_CREATED = "task_created"
    TASK_CLAIMED = "task_claimed"
    TASK_COMPLETED = "task_completed"
    TASK_BLOCKED = "task_blocked"
    TASK_RESET = "task_reset"  # Stale task reset
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    AGENT_REGISTERED = "agent_registered"
    AGENT_DEREGISTERED = "agent_deregistered"
    BOARD_RESET = "board_reset"


class AuditLogger:
    """
    Logger for board state changes.
    
    All mutations to the board are logged as append-only entries
    for debugging, replay, and accountability.
    """
    
    def __init__(self, board_dir: Optional[Path] = None):
        self.board_dir = Path(board_dir) if board_dir else BOARD_DIR
        self.audit_file = self.board_dir / "audit.json"
        self.board_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_entries(self) -> list:
        """Load existing audit entries."""
        if not self.audit_file.exists():
            return []
        try:
            with _lock(self.audit_file):
                content = self.audit_file.read_text(encoding="utf-8")
                if not content.strip():
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return []
    
    def _save_entries(self, entries: list):
        """Save audit entries atomically."""
        with _lock(self.audit_file):
            self.audit_file.write_text(
                json.dumps(entries, indent=2, default=str),
                encoding="utf-8"
            )
    
    def log(
        self,
        action: str,
        task_id: Optional[str] = None,
        agent: Optional[str] = None,
        old_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Log an audit event.
        
        Args:
            action: Type of action (use AuditAction constants)
            task_id: Optional task ID affected
            agent: Optional agent name who performed the action
            old_state: Optional state before the change
            new_state: Optional state after the change
            metadata: Optional additional data
            
        Returns:
            The audit entry that was logged
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "task_id": task_id,
            "agent": agent,
            "old_state": old_state,
            "new_state": new_state,
            "metadata": metadata or {},
        }
        
        # Remove None values for cleaner output
        entry = {k: v for k, v in entry.items() if v is not None}
        
        entries = self._load_entries()
        entries.append(entry)
        self._save_entries(entries)
        
        return entry
    
    def get_entries(
        self,
        action: Optional[str] = None,
        task_id: Optional[str] = None,
        agent: Optional[str] = None,
        limit: int = 100,
        since: Optional[str] = None,
    ) -> list:
        """
        Query audit entries with optional filtering.
        
        Args:
            action: Filter by action type
            task_id: Filter by task ID
            agent: Filter by agent name
            limit: Maximum entries to return (default 100)
            since: ISO timestamp to get entries after
            
        Returns:
            List of matching audit entries, newest first
        """
        entries = self._load_entries()
        
        # Apply filters
        if action:
            entries = [e for e in entries if e.get("action") == action]
        if task_id:
            entries = [e for e in entries if e.get("task_id") == task_id]
        if agent:
            entries = [e for e in entries if e.get("agent") == agent]
        if since:
            entries = [e for e in entries if e.get("timestamp", "") > since]
        
        # Return newest first, limited
        return list(reversed(entries))[:limit]
    
    def get_task_history(self, task_id: str) -> list:
        """Get complete audit history for a specific task."""
        return self.get_entries(task_id=task_id, limit=1000)
    
    def get_agent_actions(self, agent: str, limit: int = 100) -> list:
        """Get recent actions performed by a specific agent."""
        return self.get_entries(agent=agent, limit=limit)
    
    def rotate(self, max_entries: int = 10000, archive_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Rotate audit log if it gets too large.
        
        Args:
            max_entries: Maximum entries before rotation
            archive_dir: Directory to save rotated logs (default: board_dir/archives)
            
        Returns:
            Path to archive file if rotated, None otherwise
        """
        entries = self._load_entries()
        
        if len(entries) <= max_entries:
            return None
        
        # Create archive
        archive_dir = archive_dir or (self.board_dir / "archives")
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = archive_dir / f"audit_{timestamp}.json"
        
        # Split entries
        to_archive = entries[:-max_entries]
        to_keep = entries[-max_entries:]
        
        # Save archive
        archive_file.write_text(
            json.dumps(to_archive, indent=2, default=str),
            encoding="utf-8"
        )
        
        # Save truncated log
        self._save_entries(to_keep)
        
        return archive_file
    
    def clear(self):
        """Clear all audit entries. Use with caution!"""
        if self.audit_file.exists():
            self.audit_file.unlink()


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_audit(
    action: str,
    task_id: Optional[str] = None,
    agent: Optional[str] = None,
    old_state: Optional[Dict] = None,
    new_state: Optional[Dict] = None,
    metadata: Optional[Dict] = None,
) -> Dict:
    """
    Convenience function to log an audit event.
    
    Example:
        log_audit(
            action=AuditAction.TASK_CLAIMED,
            task_id="task_123",
            agent="claude",
            new_state={"status": "in_progress", "claimed_by": "claude"}
        )
    """
    return get_audit_logger().log(
        action=action,
        task_id=task_id,
        agent=agent,
        old_state=old_state,
        new_state=new_state,
        metadata=metadata,
    )


# Integration helpers for base_agent.py

def audit_task_claimed(task: Dict, agent_name: str):
    """Log when a task is claimed."""
    return log_audit(
        action=AuditAction.TASK_CLAIMED,
        task_id=task.get("id"),
        agent=agent_name,
        old_state={"status": "pending"},
        new_state={
            "status": "in_progress",
            "claimed_by": agent_name,
            "claimed_at": datetime.now().isoformat(),
        },
    )


def audit_task_completed(task: Dict, agent_name: str, result: str = ""):
    """Log when a task is completed."""
    return log_audit(
        action=AuditAction.TASK_COMPLETED,
        task_id=task.get("id"),
        agent=agent_name,
        old_state={"status": "in_progress", "claimed_by": agent_name},
        new_state={
            "status": "done",
            "completed_by": agent_name,
            "completed_at": datetime.now().isoformat(),
            "result_preview": result[:200] if result else None,
        },
    )


def audit_task_blocked(task: Dict, agent_name: str, reason: str):
    """Log when a task is blocked."""
    return log_audit(
        action=AuditAction.TASK_BLOCKED,
        task_id=task.get("id"),
        agent=agent_name,
        old_state={"status": "in_progress"},
        new_state={
            "status": "blocked",
            "blocked_by": agent_name,
            "blocked_at": datetime.now().isoformat(),
            "block_reason": reason,
        },
    )


def audit_task_reset(task: Dict, reason: str = "Stale task"):
    """Log when a stale task is reset."""
    return log_audit(
        action=AuditAction.TASK_RESET,
        task_id=task.get("id"),
        agent="system",
        old_state={
            "status": "in_progress",
            "claimed_by": task.get("claimed_by"),
        },
        new_state={
            "status": "pending",
            "reset_at": datetime.now().isoformat(),
            "reset_reason": reason,
        },
    )
