import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models import ChatMessage, MessageReaction, TrendingDiscussion, Idea
from datetime import datetime, timezone, timedelta

@pytest_asyncio.fixture
async def api_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_trending_full_logic(api_client, db_session):
    # 1. Create a message
    msg = ChatMessage(id="trend-1", channel="gen", sender="c1", content="Cool tech")
    db_session.add(msg)
    await db_session.commit()

    # 2. Update scores (should be 0)
    resp = await api_client.post("/api/v2/trending/update")
    assert resp.status_code == 200

    # 3. Add reactions to message
    for i in range(12):
        db_session.add(MessageReaction(message_id="trend-1", reactor_id=f"u{i}", reaction_type="fire"))
    await db_session.commit()

    # 4. Trigger update - should surface idea now (score 12 > 10)
    resp = await api_client.post("/api/v2/trending/update")
    assert resp.status_code == 200
    assert resp.json()["new_ideas_surfaced"] >= 1

    # 5. Verify TrendingDiscussion and Idea
    resp = await api_client.get("/api/v2/trending")
    assert resp.status_code == 200
    assert any(t["message_id"] == "trend-1" for t in resp.json())
