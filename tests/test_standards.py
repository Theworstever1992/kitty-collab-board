import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import StandardsViolation, Agent

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
async def test_standards_api_comprehensive(api_client, db_session):
    await _register_agent(db_session, "std-agent")

    # 1. Create violation
    payload = {
        "violation_type": "off_topic",
        "agent_name": "std-agent",
        "description": "Notes",
        "severity": "low"
    }
    resp = await api_client.post("/api/v2/violations/", json=payload)
    assert resp.status_code == 201

    # 2. List violations with filters
    resp = await api_client.get("/api/v2/violations/?agent_name=std-agent&severity=low")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # 3. Repeat offenders
    # Add more violations to hit the threshold
    for _ in range(2):
        db_session.add(StandardsViolation(agent_id="std-agent", violation_type="v", severity="low"))
    await db_session.commit()

    resp = await api_client.get("/api/v2/violations/repeat-offenders?min_violations=3")
    assert resp.status_code == 200
    assert any(o["agent_id"] == "std-agent" for o in resp.json())

    # 4. Error cases
    resp = await api_client.post("/api/v2/violations/", json={"violation_type": "v", "agent_name": "std-agent", "severity": "invalid"})
    assert resp.status_code == 400

    resp = await api_client.post("/api/v2/violations/", json={"violation_type": "v", "agent_name": "non-existent"})
    assert resp.status_code == 404
