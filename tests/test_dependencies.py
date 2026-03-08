"""
test_dependencies.py — Tests for task dependencies (TASK 6022)

Tests blocked_by field and dependency resolution.
"""

import json
import pytest
from pathlib import Path
from agents.base_agent import BaseAgent


class TestDependencies:
    """Tests for task dependencies."""

    def test_claim_task_with_unmet_dependency(self, tmp_path):
        """Task with unmet blocked_by should not be claimed."""
        board_dir = tmp_path / "board"
        board_dir.mkdir()

        # Create board with dependent tasks
        board = {
            "tasks": [
                {"id": "task_1", "title": "First", "status": "pending"},
                {
                    "id": "task_2",
                    "title": "Second (depends on task_1)",
                    "status": "pending",
                    "blocked_by": ["task_1"],
                },
            ]
        }
        board_file = board_dir / "board.json"
        board_file.write_text(json.dumps(board))

        # Try to claim task_2 when task_1 not done
        agent = BaseAgent("test_agent", "test", role="general")
        result = agent.claim_task("task_2")

        assert not result, "Should not claim task with unmet dependencies"

    def test_claim_task_with_met_dependency(self, tmp_path):
        """Task with met blocked_by should be claimed."""
        board_dir = tmp_path / "board"
        board_dir.mkdir()

        # Create board with dependent tasks, task_1 already done
        board = {
            "tasks": [
                {"id": "task_1", "title": "First", "status": "done"},
                {
                    "id": "task_2",
                    "title": "Second (depends on task_1)",
                    "status": "pending",
                    "blocked_by": ["task_1"],
                },
            ]
        }
        board_file = board_dir / "board.json"
        board_file.write_text(json.dumps(board))

        # Try to claim task_2 when task_1 is done
        agent = BaseAgent("test_agent", "test", role="general")
        result = agent.claim_task("task_2")

        assert result, "Should claim task when dependencies are met"

        # Verify task_2 is claimed
        board = json.loads(board_file.read_text())
        task_2 = next((t for t in board["tasks"] if t["id"] == "task_2"), None)
        assert task_2["status"] == "in_progress"
        assert task_2["claimed_by"] == "test_agent"

    def test_claim_task_with_multiple_dependencies(self, tmp_path):
        """Task with multiple blocked_by should require all to be done."""
        board_dir = tmp_path / "board"
        board_dir.mkdir()

        board = {
            "tasks": [
                {"id": "task_1", "title": "First", "status": "done"},
                {"id": "task_2", "title": "Second", "status": "pending"},
                {
                    "id": "task_3",
                    "title": "Third (depends on 1 and 2)",
                    "status": "pending",
                    "blocked_by": ["task_1", "task_2"],
                },
            ]
        }
        board_file = board_dir / "board.json"
        board_file.write_text(json.dumps(board))

        agent = BaseAgent("test_agent", "test", role="general")

        # Should fail (task_2 not done yet)
        assert not agent.claim_task("task_3")

        # Complete task_2
        board["tasks"][1]["status"] = "done"
        board_file.write_text(json.dumps(board))

        # Should succeed now (both dependencies done)
        assert agent.claim_task("task_3")

    def test_claim_task_without_dependencies(self, tmp_path):
        """Task without blocked_by should be claimed normally."""
        board_dir = tmp_path / "board"
        board_dir.mkdir()

        board = {
            "tasks": [
                {"id": "task_1", "title": "First", "status": "pending"},
            ]
        }
        board_file = board_dir / "board.json"
        board_file.write_text(json.dumps(board))

        agent = BaseAgent("test_agent", "test", role="general")
        result = agent.claim_task("task_1")

        assert result, "Should claim task without dependencies"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
