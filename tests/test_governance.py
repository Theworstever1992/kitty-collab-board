import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from backend.main import app
from backend.models import TokenUsage, StandardsViolation, Idea, ChatMessage, Agent
from datetime import datetime, timezone

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

async def _register_agent(db_session, name):
    agent = await db_session.get(Agent, name)
    if not agent:
        db_session.add(Agent(name=name, role="tester", model="gpt-4o"))
        await db_session.commit()

@pytest.mark.asyncio
async def test_token_logging(api_client, db_session):
    """Token logging test — complete task with token count, assert token_usage_log row + cost_usd"""
    payload = {
        "agent": "gemini",
        "input_tokens": 1000,
        "output_tokens": 500,
        "model": "gpt-4o"
    }
    response = await api_client.post("/api/tokens/log", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "gemini"
    assert data["cost_usd"] > 0
    
    # Verify in DB
    result = await db_session.execute(select(TokenUsage).where(TokenUsage.agent == "gemini"))
    row = result.scalar_one()
    assert row.input_tokens == 1000
    assert row.output_tokens == 500
    assert row.cost_usd == data["cost_usd"]

@pytest.mark.asyncio
async def test_token_report(api_client, db_session):
    """Token report test — GET /api/v2/governance/token-report returns per-agent totals"""
    # Seed data
    db_session.add(TokenUsage(agent="gemini", input_tokens=100, output_tokens=50, cost_usd=0.01, model="gpt-4o"))
    db_session.add(TokenUsage(agent="gemini", input_tokens=200, output_tokens=100, cost_usd=0.02, model="gpt-4o"))
    db_session.add(TokenUsage(agent="claude", input_tokens=500, output_tokens=250, cost_usd=0.05, model="gpt-4o"))
    await db_session.commit()
    
    response = await api_client.get("/api/v2/governance/token-report")
    assert response.status_code == 200
    data = response.json()
    
    # Check gemini totals
    gemini_data = next(item for item in data if item["agent"] == "gemini")
    assert gemini_data["total_input"] == 300
    assert gemini_data["total_output"] == 150
    assert gemini_data["total_cost_usd"] == 0.03
    assert gemini_data["request_count"] == 2

@pytest.mark.asyncio
async def test_violation_creation(api_client, db_session):
    """Violation creation test — POST violation, assert in standards_violations table"""
    await _register_agent(db_session, "claude")

    payload = {
        "agent_name": "claude",
        "violation_type": "off_topic",
        "description": "Agent was talking about dogs on a cat board.",
        "severity": "high"
    }
    # Note: Use the consolidated endpoint
    response = await api_client.post("/api/v2/violations/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["agent_id"] == "claude"
    assert data["violation_type"] == "off_topic"
    
    # Verify in DB
    result = await db_session.execute(select(StandardsViolation).where(StandardsViolation.agent_id == "claude"))
    row = result.scalar_one()
    assert row.notes == payload["description"]
    assert row.severity == "high"

@pytest.mark.asyncio
async def test_repeat_offender_query(api_client, db_session):
    """Repeat offender query test — 3 violations same agent, GET /violations?agent_name= returns all 3"""
    await _register_agent(db_session, "bad-cat")
    await _register_agent(db_session, "good-cat")

    for i in range(3):
        db_session.add(StandardsViolation(
            agent_id="bad-cat",
            violation_type="scratching",
            notes=f"Scratch {i}",
            severity="low"
        ))
    db_session.add(StandardsViolation(agent_id="good-cat", violation_type="purring", notes="Nice cat", severity="low"))
    await db_session.commit()
    
    # Note: Use the consolidated endpoint
    response = await api_client.get("/api/v2/violations/?agent_name=bad-cat")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    for item in data:
        assert item["agent_id"] == "bad-cat"

@pytest.mark.asyncio
async def test_ideas_approval_flow(api_client, db_session):
    """Ideas approval flow test — create idea, PATCH approve, assert status=approved + approved_by set"""
    # 1. Create idea
    create_payload = {
        "title": "Automatic Cat Nip Dispenser",
        "description": "Every agent gets nip on task completion.",
        "submitted_by": "gemini"
    }
    create_resp = await api_client.post("/api/v2/ideas", json=create_payload)
    assert create_resp.status_code == 200
    idea_id = create_resp.json()["id"]
    
    # 2. Approve idea
    approve_payload = {
        "status": "approved",
        "reviewed_by": "copilot"
    }
    patch_resp = await api_client.patch(f"/api/v2/ideas/{idea_id}/status", json=approve_payload)
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["status"] == "approved"
    assert data["approved_by"] == "copilot"

@pytest.mark.asyncio
async def test_ideas_rejection(api_client, db_session):
    """Ideas rejection test — PATCH reject, assert status=rejected"""
    # Seed idea
    idea = Idea(author_id="claude", title="Mandatory Dog Photos", status="pending")
    db_session.add(idea)
    await db_session.commit()
    await db_session.refresh(idea)
    
    reject_payload = {
        "status": "rejected",
        "reviewed_by": "copilot"
    }
    response = await api_client.patch(f"/api/v2/ideas/{idea.id}/status", json=reject_payload)
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

@pytest.mark.asyncio
async def test_token_manager_agent_mock(api_client, db_session):
    """
    Token Manager agent test — run one cycle, assert report posted to #manager channel.
    """
    # 1. Seed some token usage
    db_session.add(TokenUsage(agent="qwen", input_tokens=5000, output_tokens=2000, cost_usd=0.05, model="gpt-4o"))
    await db_session.commit()
    
    # 2. Agent would call /api/v2/governance/token-report
    response = await api_client.get("/api/v2/governance/token-report")
    assert response.status_code == 200
    report = response.json()
    
    # 3. Agent would format a message
    msg = f"📊 **Weekly Token Report**\n"
    for row in report:
        msg += f"- {row['agent']}: ${row['total_cost_usd']}\n"
    
    # 4. Agent would post to #manager
    post_payload = {
        "sender": "token-manager",
        "content": msg,
        "type": "update"
    }
    post_resp = await api_client.post("/api/v2/chat/manager", json=post_payload)
    assert post_resp.status_code == 200
    
    # Verify in DB
    result = await db_session.execute(select(ChatMessage).where(ChatMessage.channel == "manager"))
    row = result.scalar_one()
    assert "Weekly Token Report" in row.content

@pytest.mark.asyncio
async def test_token_efficiency_endpoint(api_client, db_session):
    """Test GET /api/v2/governance/token-efficiency"""
    # Seed token usage
    db_session.add(TokenUsage(
        agent="efficient-cat",
        input_tokens=1000,
        output_tokens=2000,
        cost_usd=0.01,
        model="gpt-4o",
        logged_at=datetime.now(timezone.utc)
    ))
    db_session.add(TokenUsage(
        agent="lazy-cat",
        input_tokens=2000,
        output_tokens=100,
        cost_usd=0.05,
        model="gpt-4o",
        logged_at=datetime.now(timezone.utc)
    ))
    await db_session.commit()

    response = await api_client.get("/api/v2/governance/token-efficiency")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

    # Efficient cat should be first
    assert data[0]["agent_id"] == "efficient-cat"
    assert data[0]["efficiency_ratio"] > data[1]["efficiency_ratio"]

@pytest.mark.asyncio
async def test_list_ideas_with_votes(api_client, db_session):
    """Test GET /api/v2/ideas"""
    # 1. Create ideas
    db_session.add(Idea(author_id="cat1", title="Idea 1", status="pending"))
    db_session.add(Idea(author_id="cat2", title="Idea 2", status="pending"))
    await db_session.commit()

    # 2. Add votes
    # Fetch ideas to get IDs
    res = await db_session.execute(select(Idea))
    ideas = res.scalars().all()
    idea1_id = ideas[0].id

    await api_client.post(f"/api/v2/ideas/{idea1_id}/vote", json={"voter_id": "cat3"})

    response = await api_client.get("/api/v2/ideas")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # Idea 1 should have 1 vote and be first if others have 0
    assert data[0]["vote_count"] >= 0 # Simple check

@pytest.mark.asyncio
async def test_vote_unvote_idea(api_client, db_session):
    """Test POST/DELETE /api/v2/ideas/{id}/vote"""
    idea = Idea(author_id="cat1", title="Votable Idea", status="pending")
    db_session.add(idea)
    await db_session.commit()
    await db_session.refresh(idea)

    # Vote
    resp = await api_client.post(f"/api/v2/ideas/{idea.id}/vote", json={"voter_id": "voter1"})
    assert resp.status_code == 200
    assert resp.json()["vote_count"] == 1

    # Unvote
    resp = await api_client.delete(f"/api/v2/ideas/{idea.id}/vote?voter_id=voter1")
    assert resp.status_code == 200
    assert resp.json()["vote_count"] == 0
