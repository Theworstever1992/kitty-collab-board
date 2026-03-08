"""
dependencies.py — Kitty Collab Board
Task dependency management system.

Supports blocked-by relationships between tasks.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Set
from collections import defaultdict

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False


BOARD_DIR = Path(os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board"))
DEPENDENCIES_FILE = BOARD_DIR / "dependencies.json"


class _NoOpLock:
    """Fallback context manager when filelock is not installed."""
    def __enter__(self): return self
    def __exit__(self, *_): pass


def _lock(file_path: Path):
    """Return a FileLock for the given path, or a no-op context if unavailable."""
    if FILELOCK_AVAILABLE:
        return FileLock(str(file_path) + ".lock", timeout=10)
    return _NoOpLock()


class DependencyManager:
    """
    Manages task dependencies (blocked-by relationships).

    A task can depend on other tasks - it cannot be claimed until
    all its dependencies are completed.
    """

    def __init__(self, board_dir: Optional[Path] = None):
        self.board_dir = Path(board_dir) if board_dir else BOARD_DIR
        self.deps_file = self.board_dir / "dependencies.json"
        self.board_dir.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> Dict:
        """Load dependencies data."""
        if not self.deps_file.exists():
            return {"dependencies": {}, "blocks": {}}
        try:
            with _lock(self.deps_file):
                content = self.deps_file.read_text(encoding="utf-8")
                if not content.strip():
                    return {"dependencies": {}, "blocks": {}}
                return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return {"dependencies": {}, "blocks": {}}

    def _save_data(self, data: Dict):
        """Save dependencies data atomically."""
        with _lock(self.deps_file):
            self.deps_file.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8"
            )

    def add_dependency(self, task_id: str, blocked_by: str):
        """
        Add a dependency: task_id is blocked by blocked_by.

        Args:
            task_id: The task that is blocked
            blocked_by: The task that must complete first
        """
        data = self._load_data()

        # Add to dependencies (what this task depends on)
        if task_id not in data["dependencies"]:
            data["dependencies"][task_id] = []
        if blocked_by not in data["dependencies"][task_id]:
            data["dependencies"][task_id].append(blocked_by)

        # Add to blocks (what this task blocks)
        if blocked_by not in data["blocks"]:
            data["blocks"][blocked_by] = []
        if task_id not in data["blocks"][blocked_by]:
            data["blocks"][blocked_by].append(task_id)

        self._save_data(data)

    def remove_dependency(self, task_id: str, blocked_by: str):
        """Remove a dependency relationship."""
        data = self._load_data()

        if task_id in data["dependencies"]:
            if blocked_by in data["dependencies"][task_id]:
                data["dependencies"][task_id].remove(blocked_by)
            if not data["dependencies"][task_id]:
                del data["dependencies"][task_id]

        if blocked_by in data["blocks"]:
            if task_id in data["blocks"][blocked_by]:
                data["blocks"][blocked_by].remove(task_id)
            if not data["blocks"][blocked_by]:
                del data["blocks"][blocked_by]

        self._save_data(data)

    def get_dependencies(self, task_id: str) -> List[str]:
        """Get list of tasks that this task depends on (blocked by)."""
        data = self._load_data()
        return data["dependencies"].get(task_id, [])

    def get_blocked_tasks(self, blocking_task: str) -> List[str]:
        """Get list of tasks that are blocked by this task."""
        data = self._load_data()
        return data["blocks"].get(blocking_task, [])

    def get_all_dependencies(self, task_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """
        Get all transitive dependencies (recursive).

        Returns all tasks that must complete before this task can start.
        """
        if visited is None:
            visited = set()

        if task_id in visited:
            return visited

        visited.add(task_id)
        direct_deps = self.get_dependencies(task_id)

        for dep in direct_deps:
            self.get_all_dependencies(dep, visited)

        return visited

    def is_blocked(self, task_id: str, board_tasks: List[Dict]) -> bool:
        """
        Check if a task is blocked by incomplete dependencies.

        Args:
            task_id: Task to check
            board_tasks: List of all tasks from board.json

        Returns:
            True if task is blocked, False if it can be claimed
        """
        deps = self.get_dependencies(task_id)
        if not deps:
            return False

        # Build task status map
        task_status = {t["id"]: t.get("status", "pending") for t in board_tasks}

        # Check if all dependencies are done
        for dep in deps:
            if task_status.get(dep) != "done":
                return True

        return False

    def get_blocking_tasks(self, task_id: str, board_tasks: List[Dict]) -> List[Dict]:
        """
        Get list of incomplete tasks that are blocking this task.

        Returns:
            List of task dicts that must complete first
        """
        deps = self.get_dependencies(task_id)
        if not deps:
            return []

        # Build task map
        task_map = {t["id"]: t for t in board_tasks}
        blocking = []

        for dep in deps:
            task = task_map.get(dep)
            if task and task.get("status") != "done":
                blocking.append(task)

        return blocking

    def get_ready_tasks(self, board_tasks: List[Dict]) -> List[str]:
        """
        Get list of tasks that are ready to be claimed (not blocked).

        Args:
            board_tasks: List of all tasks from board.json

        Returns:
            List of task IDs that have all dependencies satisfied
        """
        ready = []

        for task in board_tasks:
            if task.get("status") != "pending":
                continue

            task_id = task["id"]
            if not self.is_blocked(task_id, board_tasks):
                ready.append(task_id)

        return ready

    def on_task_completed(self, task_id: str) -> List[str]:
        """
        Call when a task is completed to get newly unblocked tasks.

        Args:
            task_id: The task that was just completed

        Returns:
            List of task IDs that are now unblocked
        """
        blocked_tasks = self.get_blocked_tasks(task_id)
        data = self._load_data()

        # Build current task status (we don't have full board here, caller should verify)
        # This returns tasks that were blocked by this task - caller should check if they're now ready

        return blocked_tasks

    def clear_dependencies(self, task_id: str):
        """Clear all dependencies for a task (when deleting)."""
        data = self._load_data()

        # Remove from dependencies
        if task_id in data["dependencies"]:
            # Remove each blocking relationship
            for blocked_by in data["dependencies"][task_id]:
                if blocked_by in data["blocks"]:
                    if task_id in data["blocks"][blocked_by]:
                        data["blocks"][blocked_by].remove(task_id)
                    if not data["blocks"][blocked_by]:
                        del data["blocks"][blocked_by]
            del data["dependencies"][task_id]

        # Remove from blocks (task was blocking others)
        if task_id in data["blocks"]:
            for blocked_task in data["blocks"][task_id]:
                if blocked_task in data["dependencies"]:
                    if task_id in data["dependencies"][blocked_task]:
                        data["dependencies"][blocked_task].remove(task_id)
                    if not data["dependencies"][blocked_task]:
                        del data["dependencies"][blocked_task]
            del data["blocks"][task_id]

        self._save_data(data)

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get full dependency graph for visualization."""
        data = self._load_data()
        return data["dependencies"].copy()

    def has_circular_dependency(self) -> bool:
        """Check for circular dependencies using DFS."""
        data = self._load_data()
        visited = set()
        rec_stack = set()

        def dfs(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            for dep in data["dependencies"].get(task_id, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        for task_id in data["dependencies"]:
            if task_id not in visited:
                if dfs(task_id):
                    return True

        return False


# Global manager instance
_manager: Optional[DependencyManager] = None


def get_dependency_manager() -> DependencyManager:
    """Get the global dependency manager instance."""
    global _manager
    if _manager is None:
        _manager = DependencyManager()
    return _manager


# Convenience functions
def add_dependency(task_id: str, blocked_by: str):
    return get_dependency_manager().add_dependency(task_id, blocked_by)


def remove_dependency(task_id: str, blocked_by: str):
    return get_dependency_manager().remove_dependency(task_id, blocked_by)


def get_dependencies(task_id: str) -> List[str]:
    return get_dependency_manager().get_dependencies(task_id)


def is_task_blocked(task_id: str, board_tasks: List[Dict]) -> bool:
    return get_dependency_manager().is_blocked(task_id, board_tasks)


def get_blocking_tasks(task_id: str, board_tasks: List[Dict]) -> List[Dict]:
    return get_dependency_manager().get_blocking_tasks(task_id, board_tasks)


def get_ready_tasks(board_tasks: List[Dict]) -> List[str]:
    return get_dependency_manager().get_ready_tasks(board_tasks)


def clear_dependencies(task_id: str):
    return get_dependency_manager().clear_dependencies(task_id)
