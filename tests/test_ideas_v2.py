import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import Idea, Agent

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_ideas_api_v2(api_client, db_session):
    # 1. Create
    payload = {"title": "Idea", "submitted_by": "tester"}
    resp = await api_client.post("/api/v2/ideas", json=payload)
    assert resp.status_code == 200
    idea_id = resp.json()["id"]

    # 2. List
    resp = await api_client.get("/api/v2/ideas")
    assert resp.status_code == 200

    # 3. Get
    resp = await api_client.get(f"/api/v2/ideas/{idea_id}")
    assert resp.status_code == 200

    # 4. Vote
    resp = await api_client.post(f"/api/v2/ideas/{idea_id}/vote", json={"voter_id": "v1"})
    assert resp.status_code == 200

    # 5. Unvote
    resp = await api_client.delete(f"/api/v2/ideas/{idea_id}/vote?voter_id=v1")
    assert resp.status_code == 200

    # 6. Status
    resp = await api_client.patch(f"/api/v2/ideas/{idea_id}/status", json={"status": "approved"})
    assert resp.status_code == 200
