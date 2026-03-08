"""
test_agent.py — Kitty Collab Board
Tests for agent lifecycle: register, heartbeat, deregister.
"""

import json
from pathlib import Path

from agents.base_agent import BaseAgent


class TestAgent(BaseAgent):
    """Test agent for lifecycle tests."""
    def __init__(self, name="test_agent", role="general"):
        super().__init__(name=name, model="test-model", role=role)


class TestRegistration:
    """Tests for agent registration."""
    
    def test_register_adds_agent(self, temp_board_dir):
        """Test that register() adds agent to agents.json."""
        agent = TestAgent()
        agent.register()
        
        agents_file = temp_board_dir / "agents.json"
        agents = json.loads(agents_file.read_text())
        
        assert "test_agent" in agents
        assert agents["test_agent"]["status"] == "online"
        assert agents["test_agent"]["model"] == "test-model"
        assert agents["test_agent"]["role"] == "general"
    
    def test_register_updates_existing(self, temp_board_dir):
        """Test that register() updates existing agent entry."""
        # Pre-populate agents.json
        agents_file = temp_board_dir / "agents.json"
        agents_file.write_text(json.dumps({
            "test_agent": {
                "status": "offline",
                "model": "old-model"
            }
        }, indent=2))
        
        agent = TestAgent()
        agent.register()
        
        agents = json.loads(agents_file.read_text())
        assert agents["test_agent"]["status"] == "online"
        assert agents["test_agent"]["model"] == "test-model"


class TestDeregistration:
    """Tests for agent deregistration."""
    
    def test_deregister_marks_offline(self, temp_board_dir):
        """Test that deregister() marks agent as offline."""
        # Pre-populate with online agent
        agents_file = temp_board_dir / "agents.json"
        agents_file.write_text(json.dumps({
            "test_agent": {
                "status": "online",
                "model": "test-model"
            }
        }, indent=2))
        
        agent = TestAgent()
        agent.deregister()
        
        agents = json.loads(agents_file.read_text())
        assert agents["test_agent"]["status"] == "offline"


class TestHeartbeat:
    """Tests for agent heartbeat."""
    
    def test_heartbeat_updates_last_seen(self, temp_board_dir):
        """Test that _heartbeat() updates last_seen timestamp."""
        import time
        
        # Pre-populate with old timestamp
        agents_file = temp_board_dir / "agents.json"
        old_time = "2026-03-05T00:00:00"
        agents_file.write_text(json.dumps({
            "test_agent": {
                "status": "online",
                "last_seen": old_time
            }
        }, indent=2))
        
        agent = TestAgent()
        agent._heartbeat()
        
        agents = json.loads(agents_file.read_text())
        assert agents["test_agent"]["last_seen"] != old_time


class TestGenericAgent:
    """Tests for GenericAgent class."""
    
    def test_generic_agent_initialization(self, mock_provider):
        """Test GenericAgent initializes correctly."""
        from agents.generic_agent import GenericAgent
        
        config = {
            "name": "test_bot",
            "model": "test-model",
            "provider": "mock",
            "role": "code",
            "max_tokens": 2048
        }
        
        provider = mock_provider()
        agent = GenericAgent(config, provider)
        
        assert agent.name == "test_bot"
        assert agent.model == "test-model"
        assert agent.role == "code"
    
    def test_generic_agent_handles_task(self, mock_provider, sample_task):
        """Test GenericAgent.handle_task() calls provider."""
        from agents.generic_agent import GenericAgent
        
        config = {
            "name": "test_bot",
            "model": "test-model",
            "provider": "mock",
            "role": "code"
        }
        
        provider = mock_provider()
        agent = GenericAgent(config, provider)
        
        result = agent.handle_task(sample_task)
        
        assert provider.call_count == 1
        assert "Test Task" in result


class TestErrorHandling:
    """Tests for error handling in agent loop."""
    
    def test_mark_blocked_sets_status(self, temp_board_dir, sample_task):
        """Test that _mark_blocked() sets task status to blocked."""
        # Add task to board
        board_file = temp_board_dir / "board.json"
        board = json.loads(board_file.read_text())
        board["tasks"].append(sample_task)
        board_file.write_text(json.dumps(board, indent=2))
        
        agent = TestAgent()
        agent._mark_blocked(sample_task["id"], "Test error")
        
        board = json.loads(board_file.read_text())
        task = board["tasks"][0]
        assert task["status"] == "blocked"
        assert task["block_reason"] == "Test error"
        assert task["blocked_by"] == "test_agent"
