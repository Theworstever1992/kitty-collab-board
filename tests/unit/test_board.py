"""
test_board.py — Unit tests for board operations.
"""

import json
import pytest
from pathlib import Path


class TestBoardOperations:
    """Test board.json read/write operations."""

    def test_board_file_created(self, temp_board_dir):
        """Test that board directory creates necessary files."""
        assert (temp_board_dir / "board.json").exists()
        assert (temp_board_dir / "agents.json").exists()

    def test_board_loads_empty_tasks(self, temp_board_dir):
        """Test loading an empty board."""
        board_file = temp_board_dir / "board.json"
        data = json.loads(board_file.read_text(encoding="utf-8"))
        assert "tasks" in data
        assert data["tasks"] == []

    def test_board_saves_tasks(self, temp_board_dir, sample_task):
        """Test saving tasks to board."""
        board_file = temp_board_dir / "board.json"
        data = {"tasks": [sample_task]}
        board_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        
        loaded = json.loads(board_file.read_text(encoding="utf-8"))
        assert len(loaded["tasks"]) == 1
        assert loaded["tasks"][0]["id"] == sample_task["id"]


class TestTaskLifecycle:
    """Test task status transitions."""

    def test_task_pending_status(self, sample_task_pending):
        """Test pending task has correct initial state."""
        assert sample_task_pending["status"] == "pending"
        assert sample_task_pending["claimed_by"] is None
        assert sample_task_pending["completed_by"] is None

    def test_task_in_progress_status(self, sample_task_in_progress):
        """Test in-progress task has claimant."""
        assert sample_task_in_progress["status"] == "in_progress"
        assert sample_task_in_progress["claimed_by"] is not None
        assert sample_task_in_progress["claimed_at"] is not None

    def test_task_done_status(self, sample_task_done):
        """Test completed task has result."""
        assert sample_task_done["status"] == "done"
        assert sample_task_done["completed_by"] is not None
        assert sample_task_done["result"] is not None

    def test_task_blocked_status(self, sample_task_blocked):
        """Test blocked task has reason."""
        assert sample_task_blocked["status"] == "blocked"
        assert sample_task_blocked["blocked_by"] is not None
        assert sample_task_blocked["block_reason"] is not None
