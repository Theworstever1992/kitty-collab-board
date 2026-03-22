"""
test_collab_features.py — Tests for the new collaboration endpoints.

Covers:
- GET /api/v2/channels
- GET /api/v2/agents/{name}/profile  (the /profile suffix alias)
- GET /api/v2/tasks, POST /api/v2/tasks/{id}/claim, POST /api/v2/tasks/{id}/complete
- GET /api/v2/tokens/{agent}/budget
- GET /api/v2/governance/violations
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.models import Agent, ChatMessage, StandardsViolation, Task, TokenUsage


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── Channels ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_channels_returns_defaults(client, db_session):
    """With no messages, the default channels should still be listed."""
    resp = await client.get("/api/v2/channels")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "main-hall" in names
    assert "war-room" in names
    assert "assembly" in names


@pytest.mark.asyncio
async def test_list_channels_includes_message_count(client, db_session):
    """A channel that has messages should report the correct count."""
    db_session.add(ChatMessage(
        id="ch-msg-1",
        channel="test-collab-ch",
        sender="alice",
        content="hello",
        type="chat",
    ))
    await db_session.commit()

    resp = await client.get("/api/v2/channels")
    assert resp.status_code == 200
    entry = next((c for c in resp.json() if c["name"] == "test-collab-ch"), None)
    assert entry is not None
    assert entry["message_count"] == 1


# ── Agent /profile suffix ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_agent_profile_suffix(client, db_session):
    """GET /api/v2/agents/{name}/profile should return the full agent profile."""
    db_session.add(Agent(name="profile-agent", role="tester", model="test-model"))
    await db_session.commit()

    resp = await client.get("/api/v2/agents/profile-agent/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "profile-agent"
    assert data["role"] == "tester"


@pytest.mark.asyncio
async def test_get_agent_profile_not_found(client, db_session):
    resp = await client.get("/api/v2/agents/no-such-agent/profile")
    assert resp.status_code == 404


# ── v2 Task endpoints ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_v2_list_tasks(client, db_session):
    task_id = uuid.uuid4().hex[:16]
    db_session.add(Task(id=task_id, title="v2 task", status="pending"))
    await db_session.commit()

    resp = await client.get("/api/v2/tasks")
    assert resp.status_code == 200
    ids = [t["id"] for t in resp.json()]
    assert task_id in ids


@pytest.mark.asyncio
async def test_v2_claim_task(client, db_session):
    task_id = uuid.uuid4().hex[:16]
    db_session.add(Task(id=task_id, title="claim me", status="pending"))
    await db_session.commit()

    resp = await client.post(
        f"/api/v2/tasks/{task_id}/claim",
        json={"agent_name": "bot1", "claimed_at": "2026-01-01T00:00:00Z"},
    )
    assert resp.status_code == 200
    assert resp.json()["claimed"] is True


@pytest.mark.asyncio
async def test_v2_claim_task_first_claim_wins(client, db_session):
    """Second claim attempt on the same task must fail."""
    task_id = uuid.uuid4().hex[:16]
    db_session.add(Task(id=task_id, title="contested", status="pending"))
    await db_session.commit()

    r1 = await client.post(
        f"/api/v2/tasks/{task_id}/claim",
        json={"agent_name": "bot1", "claimed_at": "2026-01-01T00:00:00Z"},
    )
    r2 = await client.post(
        f"/api/v2/tasks/{task_id}/claim",
        json={"agent_name": "bot2", "claimed_at": "2026-01-01T00:00:01Z"},
    )
    assert r1.json()["claimed"] is True
    assert r2.json()["claimed"] is False


@pytest.mark.asyncio
async def test_v2_complete_task(client, db_session):
    task_id = uuid.uuid4().hex[:16]
    db_session.add(Task(id=task_id, title="complete me", status="claimed", claimed_by="bot1"))
    await db_session.commit()

    resp = await client.post(
        f"/api/v2/tasks/{task_id}/complete",
        json={"agent_name": "bot1", "result": "done"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# ── Token budget v2 ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_v2_token_budget(client, db_session):
    db_session.add(TokenUsage(
        agent="budget-bot",
        model="gpt-4o-mini",
        input_tokens=1000,
        output_tokens=500,
        cost_usd=0.00045,
    ))
    await db_session.commit()

    resp = await client.get("/api/v2/tokens/budget-bot/budget")
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent"] == "budget-bot"
    assert data["total_cost_usd"] > 0
    assert data["total_input_tokens"] == 1000
    assert data["total_output_tokens"] == 500
    assert data["ok"] is True


@pytest.mark.asyncio
async def test_v2_token_budget_empty(client, db_session):
    resp = await client.get("/api/v2/tokens/unknown-bot/budget")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cost_usd"] == 0
    assert data["total_input_tokens"] == 0


# ── Governance violations proxy ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_governance_violations_route(client, db_session):
    """GET /api/v2/governance/violations should return violations list."""
    # Need an agent before creating a violation
    db_session.add(Agent(name="viol-agent", role="worker"))
    db_session.add(StandardsViolation(
        violation_type="off_topic",
        agent_id="viol-agent",
        severity="medium",
        notes="talked about cats",
    ))
    await db_session.commit()

    resp = await client.get("/api/v2/governance/violations")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(v["agent_id"] == "viol-agent" for v in data)


@pytest.mark.asyncio
async def test_governance_violations_filter_by_agent(client, db_session):
    db_session.add(Agent(name="filter-agent", role="worker"))
    db_session.add(StandardsViolation(
        violation_type="spam",
        agent_id="filter-agent",
        severity="low",
    ))
    await db_session.commit()

    resp = await client.get("/api/v2/governance/violations?agent_id=filter-agent")
    assert resp.status_code == 200
    data = resp.json()
    assert all(v["agent_id"] == "filter-agent" for v in data)


@pytest.mark.asyncio
async def test_governance_violations_empty(client, db_session):
    resp = await client.get("/api/v2/governance/violations?agent_id=no-such-agent-xyz")
    assert resp.status_code == 200
    assert resp.json() == []
