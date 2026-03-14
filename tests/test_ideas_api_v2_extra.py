import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_ideas_api_v2_errors(api_client):
    # Update status invalid
    resp = await api_client.patch("/api/v2/ideas/1/status", json={"status": "invalid"})
    assert resp.status_code == 422
