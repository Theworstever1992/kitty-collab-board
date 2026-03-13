
import pytest
import json
import datetime
from pathlib import Path
from agents.profiles import ProfileManager, get_profile_manager
from agents.manager import ManagerRegistry, get_manager_registry
from agents.base_agent import BaseAgent
from agents.base_leader import BaseLeader

def test_profile_manager(tmp_path, monkeypatch):
    """Test v1 file-based profile manager."""
    profiles_file = tmp_path / "profiles.json"
    monkeypatch.setattr("agents.profiles.PROFILES_FILE", profiles_file)
    
    pm = ProfileManager()
    
    # Create
    p = pm.create_profile("test-cat", "Likes milk", role="developer", skills=["lapping"])
    assert p["name"] == "test-cat"
    assert p["skills"] == ["lapping"]
    
    # Get
    p2 = pm.get_profile("test-cat")
    assert p2["bio"] == "Likes milk"
    
    # List
    all_p = pm.list_profiles()
    assert len(all_p) == 1
    
    # Update
    pm.update_profile("test-cat", {"bio": "Likes cream"})
    assert pm.get_profile("test-cat")["bio"] == "Likes cream"
    
    # Delete (soft)
    pm.delete_profile("test-cat")
    assert pm.get_profile("test-cat")["status"] == "fired"
    
    # Hard delete
    pm.hard_delete_profile("test-cat")
    assert pm.get_profile("test-cat") is None

def test_manager_registry(tmp_path, monkeypatch):
    """Test manager role registry."""
    mgr_file = tmp_path / "manager.json"
    monkeypatch.setattr("agents.manager.MANAGER_FILE", mgr_file)
    
    reg = ManagerRegistry()
    
    # Initial
    assert reg.get_current_manager() is None
    
    # Assign
    reg.assign_manager("claude", assigned_by="human")
    curr = reg.get_current_manager()
    assert curr["agent"] == "claude"
    
    # History
    hist = reg.list_managers()
    assert len(hist) == 1
    
    # Revoke
    reg.revoke_manager("claude")
    assert reg.get_current_manager() is None

@pytest.mark.asyncio
async def test_base_agent_logic(board_dir):
    """Test BaseAgent helper methods and state."""
    agent = BaseAgent(name="test-agent", model="gpt-4o", role="tester")
    assert agent.name == "test-agent"
    assert agent.status == "initializing"
    
    # We can test some methods if they are pure enough
    # Most BaseAgent methods involve infinite loops or external calls
    pass

def test_base_leader_logic(board_dir):
    """Test BaseLeader board operations."""
    leader = BaseLeader(name="lead-cat", team_id="team-alpha", board_dir=board_dir)
    
    # 1. Seed board.json
    board_file = board_dir / "board.json"
    board_dir.mkdir(parents=True, exist_ok=True)
    with open(board_file, "w") as f:
        json.dump({
            "tasks": [
                {"id": "t1", "title": "Task 1", "assigned_to_team": "team-alpha", "status": "pending"},
                {"id": "t2", "title": "Task 2", "assigned_to_team": "team-beta", "status": "pending"}
            ]
        }, f)
    
    # 2. Get assigned tasks
    tasks = leader.get_assigned_tasks()
    assert len(tasks) == 1
    assert tasks[0]["id"] == "t1"
    
    # 3. Claim task
    assert leader.claim_task("t1") is True
    # Verify board updated
    with open(board_file, "r") as f:
        data = json.load(f)
        t1 = next(t for t in data["tasks"] if t["id"] == "t1")
        assert t1["status"] == "claimed"
        assert t1["claimed_by"] == "lead-cat"
    
    # 4. Complete task
    leader.complete_task("t1", "All done!")
    with open(board_file, "r") as f:
        data = json.load(f)
        t1 = next(t for t in data["tasks"] if t["id"] == "t1")
        assert t1["status"] == "done"
        assert t1["result"] == "All done!"
    
    # 5. Spawn agent
    agent_id = leader.spawn_agent({"name": "worker-cat", "role": "developer"})
    assert agent_id is not None
    team_board_file = board_dir / "teams" / "team-alpha" / "board.json"
    assert team_board_file.exists()
