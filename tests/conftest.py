"""
conftest.py — Kitty Collab Board
Pytest fixtures and configuration.
"""

import json
import os
import tempfile
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_board_dir():
    """
    Create a temporary board directory for isolated tests.
    Automatically cleaned up after test.
    """
    temp_dir = tempfile.mkdtemp(prefix="clowder_test_")
    board_dir = Path(temp_dir) / "board"
    board_dir.mkdir()
    
    # Create empty board.json
    board_file = board_dir / "board.json"
    board_file.write_text(json.dumps({
        "created_at": "2026-03-06T00:00:00",
        "tasks": []
    }, indent=2))
    
    # Create empty agents.json
    agents_file = board_dir / "agents.json"
    agents_file.write_text("{}")
    
    # Set environment variable for test duration
    old_env = os.environ.get("CLOWDER_BOARD_DIR")
    os.environ["CLOWDER_BOARD_DIR"] = str(board_dir)
    
    yield board_dir
    
    # Cleanup
    if old_env:
        os.environ["CLOWDER_BOARD_DIR"] = old_env
    else:
        os.environ.pop("CLOWDER_BOARD_DIR", None)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_task():
    """Return a sample task dict for testing."""
    return {
        "id": "task_1234567890",
        "title": "Test Task",
        "description": "A test task for unit tests",
        "prompt": "Do something for testing",
        "status": "pending",
        "created_at": "2026-03-06T00:00:00",
        "claimed_by": None,
        "result": None,
        "role": None,
        "priority": "normal",
        "priority_order": 2,
    }


@pytest.fixture
def sample_task_critical():
    """Return a critical priority task."""
    task = sample_task()
    task["priority"] = "critical"
    task["priority_order"] = 0
    return task


@pytest.fixture
def sample_task_with_role():
    """Return a task with role assigned."""
    task = sample_task()
    task["role"] = "code"
    return task


@pytest.fixture
def mock_provider():
    """
    Mock provider for testing agent logic without API calls.
    """
    class MockProvider:
        def __init__(self, model="mock-model", available=True):
            self.model = model
            self._available = available
            self.call_count = 0
            self.last_prompt = None
        
        def complete(self, prompt: str, system: str = "", config: dict = None) -> str:
            self.call_count += 1
            self.last_prompt = prompt
            return f"Mock response to: {prompt[:50]}..."
        
        def is_available(self) -> bool:
            return self._available
    
    return MockProvider


@pytest.fixture
def failing_mock_provider():
    """
    Mock provider that always fails (for error handling tests).
    """
    class FailingMockProvider:
        def __init__(self, error_message="Provider unavailable"):
            self.error_message = error_message
        
        def complete(self, prompt: str, system: str = "", config: dict = None) -> str:
            raise RuntimeError(self.error_message)
        
        def is_available(self) -> bool:
            return False
    
    return FailingMockProvider
