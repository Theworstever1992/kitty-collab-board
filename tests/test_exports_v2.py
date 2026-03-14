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
async def test_exports_api_v2(api_client, db_session):
    db_session.add(Agent(name="exp", role="r"))
    await db_session.commit()

    resp = await api_client.get("/api/v2/agents/exp/export?format=json")
    assert resp.status_code == 200

    resp = await api_client.get("/api/v2/agents/exp/export?format=md")
    assert resp.status_code == 200

    payload = {"name": "imp", "role": "r"}
    resp = await api_client.post("/api/v2/agents/import", json=payload)
    assert resp.status_code == 200
