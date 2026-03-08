"""
recurring.py — Kitty Collab Board
Recurring task management system.

Supports recurring tasks with configurable schedules (daily, weekly, monthly, custom).
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False


BOARD_DIR = Path(os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board"))
RECURRING_FILE = BOARD_DIR / "recurring.json"


class _NoOpLock:
    """Fallback context manager when filelock is not installed."""
    def __enter__(self): return self
    def __exit__(self, *_): pass


def _lock(file_path: Path):
    """Return a FileLock for the given path, or a no-op context if unavailable."""
    if FILELOCK_AVAILABLE:
        return FileLock(str(file_path) + ".lock", timeout=10)
    return _NoOpLock()


class RecurrenceType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class RecurrenceRule:
    """Defines when a recurring task should be created."""
    recurrence_type: RecurrenceType
    interval: int = 1  # Every N days/weeks/months
    hour: int = 9  # Hour of day (for daily/weekly)
    day_of_week: int = 0  # 0=Monday (for weekly)
    day_of_month: int = 1  # (for monthly)
    custom_cron: Optional[str] = None  # For custom schedules


@dataclass
class RecurringTask:
    """A recurring task definition."""
    id: str
    title: str
    description: str
    prompt: str
    recurrence: RecurrenceRule
    role: Optional[str] = None
    priority: str = "normal"
    skills: List[str] = field(default_factory=list)
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_created: Optional[str] = None
    last_task_id: Optional[str] = None
    total_created: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class RecurringTaskManager:
    """
    Manages recurring task definitions and creates new instances on schedule.
    """

    def __init__(self, board_dir: Optional[Path] = None):
        self.board_dir = Path(board_dir) if board_dir else BOARD_DIR
        self.recurring_file = self.board_dir / "recurring.json"
        self.board_dir.mkdir(parents=True, exist_ok=True)

    def _load_data(self) -> Dict:
        """Load recurring tasks data."""
        if not self.recurring_file.exists():
            return {"tasks": {}}
        try:
            with _lock(self.recurring_file):
                content = self.recurring_file.read_text(encoding="utf-8")
                if not content.strip():
                    return {"tasks": {}}
                return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return {"tasks": {}}

    def _save_data(self, data: Dict):
        """Save recurring tasks data atomically."""
        with _lock(self.recurring_file):
            self.recurring_file.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8"
            )

    def add_recurring_task(
        self,
        title: str,
        description: str,
        prompt: str,
        recurrence_type: str,
        interval: int = 1,
        hour: int = 9,
        day_of_week: int = 0,
        day_of_month: int = 1,
        role: Optional[str] = None,
        priority: str = "normal",
        skills: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Add a new recurring task.

        Returns:
            The recurring task ID
        """
        data = self._load_data()
        task_id = f"recurring_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        recurrence = RecurrenceRule(
            recurrence_type=RecurrenceType(recurrence_type),
            interval=interval,
            hour=hour,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
        )

        task = RecurringTask(
            id=task_id,
            title=title,
            description=description,
            prompt=prompt,
            recurrence=recurrence,
            role=role,
            priority=priority,
            skills=skills or [],
            enabled=True,
            metadata=metadata or {},
        )

        data["tasks"][task_id] = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "prompt": task.prompt,
            "recurrence": asdict_safe(task.recurrence),
            "role": task.role,
            "priority": task.priority,
            "skills": task.skills,
            "enabled": task.enabled,
            "created_at": task.created_at,
            "last_created": task.last_created,
            "last_task_id": task.last_task_id,
            "total_created": task.total_created,
            "metadata": task.metadata,
        }

        self._save_data(data)
        return task_id

    def get_recurring_task(self, task_id: str) -> Optional[RecurringTask]:
        """Get a recurring task by ID."""
        data = self._load_data()
        task_data = data["tasks"].get(task_id)
        if not task_data:
            return None

        recurrence = RecurrenceRule(**task_data["recurrence"])
        return RecurringTask(
            id=task_data["id"],
            title=task_data["title"],
            description=task_data["description"],
            prompt=task_data["prompt"],
            recurrence=recurrence,
            role=task_data.get("role"),
            priority=task_data.get("priority", "normal"),
            skills=task_data.get("skills", []),
            enabled=task_data.get("enabled", True),
            created_at=task_data.get("created_at"),
            last_created=task_data.get("last_created"),
            last_task_id=task_data.get("last_task_id"),
            total_created=task_data.get("total_created", 0),
            metadata=task_data.get("metadata", {}),
        )

    def list_recurring_tasks(self, enabled_only: bool = True) -> List[RecurringTask]:
        """List all recurring tasks."""
        data = self._load_data()
        tasks = []

        for task_data in data["tasks"].values():
            if enabled_only and not task_data.get("enabled", True):
                continue

            recurrence = RecurrenceRule(**task_data["recurrence"])
            tasks.append(RecurringTask(
                id=task_data["id"],
                title=task_data["title"],
                description=task_data["description"],
                prompt=task_data["prompt"],
                recurrence=recurrence,
                role=task_data.get("role"),
                priority=task_data.get("priority", "normal"),
                skills=task_data.get("skills", []),
                enabled=task_data.get("enabled", True),
                created_at=task_data.get("created_at"),
                last_created=task_data.get("last_created"),
                last_task_id=task_data.get("last_task_id"),
                total_created=task_data.get("total_created", 0),
                metadata=task_data.get("metadata", {}),
            ))

        return tasks

    def enable_recurring_task(self, task_id: str):
        """Enable a recurring task."""
        data = self._load_data()
        if task_id in data["tasks"]:
            data["tasks"][task_id]["enabled"] = True
            self._save_data(data)

    def disable_recurring_task(self, task_id: str):
        """Disable a recurring task."""
        data = self._load_data()
        if task_id in data["tasks"]:
            data["tasks"][task_id]["enabled"] = False
            self._save_data(data)

    def delete_recurring_task(self, task_id: str):
        """Delete a recurring task."""
        data = self._load_data()
        if task_id in data["tasks"]:
            del data["tasks"][task_id]
            self._save_data(data)

    def check_and_create_tasks(self, create_task_func) -> List[str]:
        """
        Check for recurring tasks that should be created and create them.

        Args:
            create_task_func: Function to call to create actual task
                Signature: create_task_func(title, description, prompt, role, priority, skills) -> task_id

        Returns:
            List of newly created task IDs
        """
        data = self._load_data()
        created_ids = []
        now = datetime.now()

        for task_id, task_data in data["tasks"].items():
            if not task_data.get("enabled", True):
                continue

            recurrence = task_data["recurrence"]
            should_create = self._should_create_task(recurrence, now, task_data.get("last_created"))

            if should_create:
                # Create the task
                new_task_id = create_task_func(
                    title=task_data["title"],
                    description=task_data["description"],
                    prompt=task_data["prompt"],
                    role=task_data.get("role"),
                    priority=task_data.get("priority", "normal"),
                    skills=task_data.get("skills", []),
                )

                # Update recurring task record
                task_data["last_created"] = now.isoformat()
                task_data["last_task_id"] = new_task_id
                task_data["total_created"] = task_data.get("total_created", 0) + 1

                created_ids.append(new_task_id)

        self._save_data(data)
        return created_ids

    def _should_create_task(self, recurrence: Dict, now: datetime, last_created: Optional[str]) -> bool:
        """Determine if a task should be created based on recurrence rule."""
        rec_type = recurrence.get("recurrence_type")
        interval = recurrence.get("interval", 1)

        # Parse last created time
        last = None
        if last_created:
            try:
                last = datetime.fromisoformat(last_created)
            except Exception:
                last = None

        if rec_type == RecurrenceType.DAILY.value:
            if last is None:
                return True  # Never created, create now

            # Check if enough days have passed
            days_since = (now - last).days
            return days_since >= interval and now.hour >= recurrence.get("hour", 9)

        elif rec_type == RecurrenceType.WEEKLY.value:
            if last is None:
                return True

            # Check if enough weeks have passed and it's the right day
            weeks_since = (now - last).days // 7
            target_day = recurrence.get("day_of_week", 0)
            is_right_day = now.weekday() == target_day
            is_right_hour = now.hour >= recurrence.get("hour", 9)

            return weeks_since >= interval and is_right_day and is_right_hour

        elif rec_type == RecurrenceType.MONTHLY.value:
            if last is None:
                return True

            # Check if enough months have passed
            months_since = (now.year - last.year) * 12 + (now.month - last.month)
            target_day = recurrence.get("day_of_month", 1)
            is_right_day = now.day == target_day
            is_right_hour = now.hour >= recurrence.get("hour", 9)

            return months_since >= interval and is_right_day and is_right_hour

        elif rec_type == RecurrenceType.CUSTOM.value:
            # Custom cron-like schedules - for now, just check interval
            if last is None:
                return True
            hours_since = (now - last).total_seconds() / 3600
            return hours_since >= interval

        return False

    def get_next_run_times(self) -> Dict[str, datetime]:
        """Get estimated next run time for each recurring task."""
        data = self._load_data()
        next_times = {}
        now = datetime.now()

        for task_id, task_data in data["tasks"].items():
            if not task_data.get("enabled", True):
                continue

            recurrence = task_data["recurrence"]
            last = None
            if task_data.get("last_created"):
                try:
                    last = datetime.fromisoformat(task_data["last_created"])
                except Exception:
                    last = None

            next_time = self._estimate_next_run(recurrence, now, last)
            next_times[task_id] = next_time

        return next_times


def asdict_safe(obj):
    """Convert dataclass to dict, handling nested dataclasses."""
    result = {}
    for key, value in obj.__dict__.items():
        if hasattr(value, '__dict__'):
            result[key] = asdict_safe(value)
        elif isinstance(value, Enum):
            result[key] = value.value
        else:
            result[key] = value
    return result


# Global manager instance
_manager: Optional[RecurringTaskManager] = None


def get_recurring_manager() -> RecurringTaskManager:
    """Get the global recurring task manager instance."""
    global _manager
    if _manager is None:
        _manager = RecurringTaskManager()
    return _manager


# Convenience functions
def add_recurring_task(title: str, description: str, prompt: str, recurrence_type: str, **kwargs) -> str:
    return get_recurring_manager().add_recurring_task(title, description, prompt, recurrence_type, **kwargs)


def list_recurring_tasks(enabled_only: bool = True) -> List[RecurringTask]:
    return get_recurring_manager().list_recurring_tasks(enabled_only)


def check_and_create_recurring_tasks(create_task_func) -> List[str]:
    return get_recurring_manager().check_and_create_tasks(create_task_func)
