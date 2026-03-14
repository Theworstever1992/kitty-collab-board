import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_api_health(api_client):
    resp = await api_client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
