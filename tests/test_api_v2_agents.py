import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import Agent

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_agents_api_v2(api_client, db_session):
    # 1. Register
    db_session.add(Agent(name="v2-agent", role="r"))
    await db_session.commit()

    # 2. List
    resp = await api_client.get("/api/v2/agents")
    assert resp.status_code == 200

    # 3. Get
    resp = await api_client.get("/api/v2/agents/v2-agent")
    assert resp.status_code == 200

    # 4. Update Profile
    resp = await api_client.patch("/api/v2/agents/v2-agent/profile", json={"bio": "New bio"})
    assert resp.status_code == 200
    assert resp.json()["bio"] == "New bio"

    # 5. Update Avatar
    svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
    resp = await api_client.patch("/api/v2/agents/v2-agent/avatar", json={"avatar_svg": svg})
    assert resp.status_code == 200

    # 6. Heartbeat
    resp = await api_client.post("/api/v2/agents/v2-agent/heartbeat")
    assert resp.status_code == 200
