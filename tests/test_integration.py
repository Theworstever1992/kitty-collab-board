
import json
import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from backend.main import app
from backend.models import Task, ContextItem, Idea, ChatMessage, Agent
from agents.pm_agent import PmAgent
from agents.agent_client import AgentClient

@pytest.fixture(autouse=True)
def mock_embeddings():
    """Mock the embedding service to avoid loading the real model in tests."""
    with pytest.MonkeyPatch().context() as m:
        from unittest.mock import MagicMock
        mock_svc = MagicMock()
        mock_svc.encode.return_value = [0.1] * 384
        m.setattr("backend.embeddings._service", mock_svc)
        yield mock_svc

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_e2e_scenario_1_task_lifecycle(api_client, db_session, board_dir):
    """
    E2E scenario 1: task → PM → leader → agent → complete → RAG retrieves on next task
    """
    from backend.database import engine as app_engine
    print(f"DEBUG DB: db_session engine={db_session.get_bind().url}")
    print(f"DEBUG DB: app_engine={app_engine.url}")
    
    # 1. User posts task to pm_tasks.json
    task_id = "user-task-001"
    pm_tasks_path = board_dir / "pm_tasks.json"
    board_dir.mkdir(parents=True, exist_ok=True)
    with open(pm_tasks_path, "w") as f:
        json.dump({"tasks": [{"id": task_id, "title": "Implement auth tokens", "description": "Need JWT support", "status": "pending"}]}, f)
    
    # 2. PM Agent decomposes
    pm = PmAgent(name="pm-tester", board_dir=board_dir)
    pending = pm.get_pending_tasks()
    assert len(pending) == 1
    
    plan_id = pm.propose_plan(pending[0])
    assert plan_id is not None
    
    # 3. Simulate human approval (write to board/channels/tasks)
    # In real flow, meow.py would do this. Here we manually seed the task in DB.
    # We'll skip the actual BaseLeader skeleton and directly test AgentClient.
    subtask_id = "subtask-auth-001"
    db_session.add(Task(
        id=subtask_id, 
        title="Implementation: Implement auth tokens", 
        description="Write JWT logic", 
        status="pending"
    ))
    await db_session.commit()
    
    # 4. Agent claims and completes
    client = AgentClient(agent_name="agent-coder", role="developer", api_base="http://test")
    client._online = True # Force online
    
    # Mocking REST calls for AgentClient since it uses urllib.request not httpx
    with pytest.MonkeyPatch().context() as m:
        # We need to mock the urllib calls inside AgentClient
        import urllib.request
        from unittest.mock import MagicMock
        
        def mock_urlopen(req, timeout=None):
            url = req.full_url if hasattr(req, "full_url") else req
            print(f"DEBUG MOCK: url={url}")
            m_res = MagicMock()
            m_res.status = 200
            m_res.__enter__.return_value = m_res
            
            if "claim" in url:
                resp = json.dumps({"claimed": True}).encode()
                print(f"DEBUG MOCK: returning {resp}")
                m_res.read.return_value = resp
            elif "complete" in url:
                resp = json.dumps({"ok": True}).encode()
                print(f"DEBUG MOCK: returning {resp}")
                m_res.read.return_value = resp
            elif url.endswith("/api/health"):
                resp = json.dumps({"status": "ok"}).encode()
                print(f"DEBUG MOCK: returning {resp}")
                m_res.read.return_value = resp
            else:
                print("DEBUG MOCK: returning null")
                m_res.read.return_value = b"null"
            return m_res
            
        m.setattr(urllib.request, "urlopen", mock_urlopen)
        
        assert client.claim_task(subtask_id) is True
        
        # Manually update DB to reflect the claim (since we mocked the REST call)
        task = await db_session.get(Task, subtask_id)
        task.status = "claimed"
        task.claimed_by = "agent-coder"
        task.claimed_at = "now"
        await db_session.commit()

        assert client.complete_task(subtask_id, "JWT auth implemented using PyJWT.") is True

    # 5. Verify RAG seeding (backend/main.py complete_task does this)
    complete_payload = {"agent_name": "agent-coder", "result": "JWT auth implemented using PyJWT."}
    resp = await api_client.post(f"/api/tasks/{subtask_id}/complete", json=complete_payload)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    
    # Check ContextItem in DB
    # We need to make sure the session sees the changes from the API client
    await db_session.commit() # End current transaction to see committed data from other sessions
    result = await db_session.execute(select(ContextItem).where(ContextItem.source_id == subtask_id))
    ctx_item = result.scalar_one()
    assert "JWT" in ctx_item.content

    # 6. New similar task posted - check context retrieval on claim
    new_task_id = "user-task-002"
    db_session.add(Task(
        id=new_task_id, 
        title="Refresh tokens for auth", 
        description="Need to refresh JWTs", 
        status="pending"
    ))
    await db_session.commit()
    
    # Claiming task via API should inject context
    claim_payload = {"agent_name": "agent-coder", "claimed_at": "now"}
    resp = await api_client.post(f"/api/tasks/{new_task_id}/claim", json=claim_payload)
    assert resp.status_code == 200
    
    # Verify context injected into description
    updated_task = await db_session.get(Task, new_task_id)
    assert "Relevant context from past work" in updated_task.description
    assert "JWT" in updated_task.description

@pytest.mark.asyncio
async def test_e2e_scenario_2_chat_to_idea(api_client, db_session):
    """
    E2E scenario 2: chat → idea surfaces → PM approves → new task
    """
    # 1. Post chat message
    chat_payload = {"sender": "qwen", "content": "We should implement a cat-sized keyboard for the agents."}
    resp = await api_client.post("/api/v2/chat/general", json=chat_payload)
    assert resp.status_code == 200
    msg_id = resp.json()["id"]
    
    # 2. Idea surfaces (simulated manual creation for now, as trending logic is complex to trigger)
    idea_payload = {
        "title": "Cat-sized Keyboards",
        "description": "Ergonomic hardware for feline developers",
        "submitted_by": "trending-agent",
        "source_message_id": msg_id
    }
    resp = await api_client.post("/api/v2/ideas", json=idea_payload)
    assert resp.status_code == 200
    idea_id = resp.json()["id"]
    
    # 3. PM approves
    approve_payload = {"status": "approved", "reviewed_by": "pm"}
    resp = await api_client.patch(f"/api/v2/ideas/{idea_id}/status", json=approve_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    
    # 4. Approved idea leads to new task (simulated)
    db_session.add(Task(
        id="task-keyboard-001",
        title="Procure Cat-sized Keyboards",
        description="Based on approved idea",
        status="pending"
    ))
    await db_session.commit()
    assert (await db_session.get(Task, "task-keyboard-001")) is not None

@pytest.mark.asyncio
async def test_e2e_scenario_3_agent_portability(api_client, db_session):
    """
    E2E scenario 3: agent exported → deleted → imported → works on new task
    """
    agent_name = "portable-cat"
    # 1. Register agent
    db_session.add(Agent(name=agent_name, role="specialist", model="gpt-4o", bio="I love boxes"))
    await db_session.commit()
    
    # 2. Export agent
    resp = await api_client.get(f"/api/v2/agents/{agent_name}/export")
    assert resp.status_code == 200
    export_data = resp.json()
    assert export_data["name"] == agent_name
    
    # 3. Delete agent
    agent = await db_session.get(Agent, agent_name)
    await db_session.delete(agent)
    await db_session.commit()
    assert (await db_session.get(Agent, agent_name)) is None
    
    # 4. Import agent
    resp = await api_client.post("/api/v2/agents/import", json=export_data)
    assert resp.status_code == 200
    
    # 5. Works on new task
    imported = await db_session.get(Agent, agent_name)
    assert imported is not None
    assert imported.role == "specialist"
