import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import Agent, Task, Team

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_tasks_api_v2(api_client, db_session):
    db_session.add(Task(id="task-v2", title="T", status="pending"))
    await db_session.commit()
    resp = await api_client.get("/api/tasks")
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_teams_api_v2(api_client, db_session):
    payload = {"name": "Team V2"}
    resp = await api_client.post("/api/v2/teams", json=payload)
    assert resp.status_code == 200
    team_id = resp.json()["id"]
    resp = await api_client.get(f"/api/v2/teams/{team_id}")
    assert resp.status_code == 200
