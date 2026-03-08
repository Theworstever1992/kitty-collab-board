"""
test_recurring.py — Tests for recurring tasks (TASK 6024)

Tests recurring task creation and scheduling.
"""

import pytest
from datetime import datetime
from agents.recurring import RecurringTaskManager, RecurrenceType


class TestRecurringTasks:
    """Tests for recurring task functionality."""

    def test_add_recurring_task(self, tmp_path):
        """Test adding a recurring task."""
        manager = RecurringTaskManager(tmp_path)

        task_id = manager.add_recurring_task(
            title="Daily standup",
            description="Team sync",
            prompt="Run standup meeting",
            recurrence_type="daily",
            hour=9,
            priority="high",
        )

        assert task_id.startswith("recurring_")
        task = manager.get_recurring_task(task_id)
        assert task.title == "Daily standup"
        assert task.enabled is True

    def test_recurring_task_scheduling(self, tmp_path):
        """Test that recurring tasks are scheduled correctly."""
        manager = RecurringTaskManager(tmp_path)

        # Add a weekly task
        task_id = manager.add_recurring_task(
            title="Weekly review",
            description="Sprint review",
            prompt="Review sprint progress",
            recurrence_type="weekly",
            day_of_week=4,  # Friday
            hour=15,
        )

        # Check if it should be created (first time always true)
        should_create = manager._should_create_task(
            manager.get_recurring_task(task_id).recurrence.__dict__,
            datetime.now(),
            None
        )
        assert should_create, "Should create recurring task on first run"

    def test_enable_disable_recurring_task(self, tmp_path):
        """Test enabling and disabling recurring tasks."""
        manager = RecurringTaskManager(tmp_path)

        task_id = manager.add_recurring_task(
            title="Test task",
            description="Test",
            prompt="Test",
            recurrence_type="daily",
        )

        # Disable
        manager.disable_recurring_task(task_id)
        task = manager.get_recurring_task(task_id)
        assert task.enabled is False

        # Enable
        manager.enable_recurring_task(task_id)
        task = manager.get_recurring_task(task_id)
        assert task.enabled is True

    def test_list_recurring_tasks(self, tmp_path):
        """Test listing recurring tasks."""
        manager = RecurringTaskManager(tmp_path)

        # Add multiple tasks
        task1 = manager.add_recurring_task(
            title="Daily",
            description="D",
            prompt="d",
            recurrence_type="daily",
        )
        task2 = manager.add_recurring_task(
            title="Weekly",
            description="W",
            prompt="w",
            recurrence_type="weekly",
        )

        # Disable one
        manager.disable_recurring_task(task2)

        # List only enabled
        enabled = manager.list_recurring_tasks(enabled_only=True)
        assert len(enabled) == 1
        assert enabled[0].id == task1

        # List all
        all_tasks = manager.list_recurring_tasks(enabled_only=False)
        assert len(all_tasks) == 2

    def test_delete_recurring_task(self, tmp_path):
        """Test deleting a recurring task."""
        manager = RecurringTaskManager(tmp_path)

        task_id = manager.add_recurring_task(
            title="To delete",
            description="Delete me",
            prompt="Delete",
            recurrence_type="monthly",
        )

        # Verify it exists
        task = manager.get_recurring_task(task_id)
        assert task is not None

        # Delete it
        manager.delete_recurring_task(task_id)

        # Verify it's gone
        task = manager.get_recurring_task(task_id)
        assert task is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
