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
async def test_agents_api_v2_errors(api_client, test_engine):
    # Get non-existent
    resp = await api_client.get("/api/v2/agents/ghost")
    assert resp.status_code == 404

    # Update non-existent
    resp = await api_client.patch("/api/v2/agents/ghost/profile", json={"bio": "..."})
    assert resp.status_code == 404

    # Update avatar missing payload
    resp = await api_client.patch("/api/v2/agents/ghost/avatar", json={})
    assert resp.status_code == 400
