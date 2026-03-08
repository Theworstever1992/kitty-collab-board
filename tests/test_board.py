"""
test_board.py — Kitty Collab Board
Tests for board operations: claim, complete, release tasks.
"""

import json
import time
from pathlib import Path

from agents.base_agent import BaseAgent


class TestAgent(BaseAgent):
    """Test agent for board operation tests."""
    def __init__(self, name="test_agent", role="general"):
        super().__init__(name=name, model="test-model", role=role)


class TestClaimTask:
    """Tests for claim_task() method."""
    
    def test_claim_pending_task(self, temp_board_dir, sample_task):
        """Test claiming a pending task succeeds."""
        # Add task to board
        board_file = temp_board_dir / "board.json"
        board = json.loads(board_file.read_text())
        board["tasks"].append(sample_task)
        board_file.write_text(json.dumps(board, indent=2))
        
        # Claim the task
        agent = TestAgent()
        result = agent.claim_task(sample_task["id"])
        
        assert result is True
        # Verify task was claimed
        board = json.loads(board_file.read_text())
        claimed_task = board["tasks"][0]
        assert claimed_task["status"] == "in_progress"
        assert claimed_task["claimed_by"] == "test_agent"
    
    def test_claim_already_claimed_task(self, temp_board_dir, sample_task):
        """Test claiming an already claimed task fails."""
        # Add already claimed task
        sample_task["status"] = "in_progress"
        sample_task["claimed_by"] = "other_agent"
        
        board_file = temp_board_dir / "board.json"
        board = json.loads(board_file.read_text())
        board["tasks"].append(sample_task)
        board_file.write_text(json.dumps(board, indent=2))
        
        # Try to claim
        agent = TestAgent()
        result = agent.claim_task(sample_task["id"])
        
        assert result is False
    
    def test_claim_nonexistent_task(self, temp_board_dir):
        """Test claiming a nonexistent task fails."""
        agent = TestAgent()
        result = agent.claim_task("task_does_not_exist")
        assert result is False


class TestCompleteTask:
    """Tests for complete_task() method."""
    
    def test_complete_claimed_task(self, temp_board_dir, sample_task):
        """Test completing a claimed task succeeds."""
        # Add claimed task
        sample_task["status"] = "in_progress"
        sample_task["claimed_by"] = "test_agent"
        
        board_file = temp_board_dir / "board.json"
        board = json.loads(board_file.read_text())
        board["tasks"].append(sample_task)
        board_file.write_text(json.dumps(board, indent=2))
        
        # Complete the task
        agent = TestAgent()
        agent.complete_task(sample_task["id"], "Test result")
        
        # Verify task was completed
        board = json.loads(board_file.read_text())
        completed_task = board["tasks"][0]
        assert completed_task["status"] == "done"
        assert completed_task["result"] == "Test result"
        assert completed_task["completed_by"] == "test_agent"


class TestPrioritySorting:
    """Tests for priority-based task sorting."""
    
    def test_get_tasks_sorted_by_priority(self, temp_board_dir):
        """Test that get_tasks() returns tasks sorted by priority."""
        board_file = temp_board_dir / "board.json"
        board = json.loads(board_file.read_text())
        
        # Add tasks with different priorities
        board["tasks"] = [
            {"id": "task_1", "status": "pending", "priority_order": 2, "created_at": "2026-03-06T00:00:00"},  # normal
            {"id": "task_2", "status": "pending", "priority_order": 0, "created_at": "2026-03-06T00:00:01"},  # critical
            {"id": "task_3", "status": "pending", "priority_order": 1, "created_at": "2026-03-06T00:00:02"},  # high
        ]
        board_file.write_text(json.dumps(board, indent=2))
        
        agent = TestAgent()
        tasks = agent.get_tasks()
        
        # Should be sorted: critical, high, normal
        assert tasks[0]["id"] == "task_2"
        assert tasks[1]["id"] == "task_3"
        assert tasks[2]["id"] == "task_1"


class TestRoleFiltering:
    """Tests for role-based task filtering."""
    
    def test_code_agent_claims_code_tasks(self, temp_board_dir):
        """Test that code agent only claims code tasks."""
        board_file = temp_board_dir / "board.json"
        board = json.loads(board_file.read_text())
        
        # Add tasks with different roles
        board["tasks"] = [
            {"id": "task_1", "status": "pending", "role": "code", "priority_order": 2, "created_at": "2026-03-06T00:00:00"},
            {"id": "task_2", "status": "pending", "role": "reasoning", "priority_order": 2, "created_at": "2026-03-06T00:00:01"},
            {"id": "task_3", "status": "pending", "role": None, "priority_order": 2, "created_at": "2026-03-06T00:00:02"},  # any role
        ]
        board_file.write_text(json.dumps(board, indent=2))
        
        agent = TestAgent(name="code_agent", role="code")
        tasks = agent.get_tasks()
        
        # Should only get code task and null-role task
        assert len(tasks) == 2
        task_ids = [t["id"] for t in tasks]
        assert "task_1" in task_ids  # code task
        assert "task_3" in task_ids  # null role
        assert "task_2" not in task_ids  # reasoning task (filtered out)
    
    def test_role_filter_disabled(self, temp_board_dir):
        """Test that role filtering can be disabled."""
        board_file = temp_board_dir / "board.json"
        board = json.loads(board_file.read_text())
        
        board["tasks"] = [
            {"id": "task_1", "status": "pending", "role": "code", "priority_order": 2, "created_at": "2026-03-06T00:00:00"},
            {"id": "task_2", "status": "pending", "role": "reasoning", "priority_order": 2, "created_at": "2026-03-06T00:00:01"},
        ]
        board_file.write_text(json.dumps(board, indent=2))
        
        agent = TestAgent(role="code")
        tasks = agent.get_tasks(role_filter=False)
        
        # Should get all tasks when filter disabled
        assert len(tasks) == 2
