import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import TokenUsage
from datetime import datetime, timezone

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_token_efficiency_logic(api_client, db_session):
    # Seed token usage
    db_session.add(TokenUsage(
        agent="efficient", input_tokens=100, output_tokens=1000, cost_usd=0.01, model="gpt-4", logged_at=datetime.now(timezone.utc)
    ))
    db_session.add(TokenUsage(
        agent="wasteful", input_tokens=1000, output_tokens=100, cost_usd=0.05, model="gpt-4", logged_at=datetime.now(timezone.utc)
    ))
    await db_session.commit()

    resp = await api_client.get("/api/v2/governance/token-efficiency")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    assert data[0]["agent_id"] == "efficient"
