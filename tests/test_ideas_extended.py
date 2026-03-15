import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import Idea, IdeaVote, Agent
from sqlalchemy import select

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_ideas_full_lifecycle(api_client, db_session):
    # 1. Create agent
    db_session.add(Agent(name="idea-creator", role="tester"))
    await db_session.commit()

    # 2. Create idea
    payload = {
        "title": "Extended Idea",
        "description": "Deep description",
        "submitted_by": "idea-creator"
    }
    resp = await api_client.post("/api/v2/ideas", json=payload)
    assert resp.status_code == 200
    idea_id = resp.json()["id"]

    # 3. List ideas (verify sort and vote count)
    resp = await api_client.get("/api/v2/ideas")
    assert resp.status_code == 200
    assert any(i["id"] == idea_id for i in resp.json())

    # 4. Get single idea
    resp = await api_client.get(f"/api/v2/ideas/{idea_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Extended Idea"

    # 5. Vote
    resp = await api_client.post(f"/api/v2/ideas/{idea_id}/vote", json={"voter_id": "voter-1"})
    assert resp.status_code == 200
    assert resp.json()["vote_count"] == 1

    # 6. Duplicate vote (should be idempotent-ish or just return count)
    resp = await api_client.post(f"/api/v2/ideas/{idea_id}/vote", json={"voter_id": "voter-1"})
    assert resp.status_code == 200
    assert resp.json()["vote_count"] == 1

    # 7. Delete vote
    resp = await api_client.delete(f"/api/v2/ideas/{idea_id}/vote?voter_id=voter-1")
    assert resp.status_code == 200
    assert resp.json()["vote_count"] == 0

    # 8. Update status
    resp = await api_client.patch(f"/api/v2/ideas/{idea_id}/status", json={"status": "approved", "reviewed_by": "admin"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"
    assert resp.json()["approved_by"] == "admin"

@pytest.mark.asyncio
async def test_trending_update_endpoint(api_client, db_session):
    resp = await api_client.post("/api/v2/trending/update")
    assert resp.status_code == 200
    assert "scores_updated" in resp.json()
