import pytest
import datetime
from sqlalchemy import select
from backend.models import ChatMessage, MessageReaction, TrendingDiscussion, Idea
from backend.api.trending import (
    compute_trending_score,
    update_trending_scores,
    maybe_surface_idea,
    get_trending,
    trigger_update,
    IDEAS_AUTO_SURFACE_THRESHOLD
)

@pytest.mark.asyncio
async def test_trending_flow(db_session):
    """Test full trending score and auto-surface flow."""
    # 1. Create a message
    msg = ChatMessage(id="msg-1", channel="general", sender="cat1", content="New toy idea")
    db_session.add(msg)
    await db_session.commit()
    
    # 2. Add reactions
    for i in range(5):
        db_session.add(MessageReaction(message_id="msg-1", reactor_id=f"cat{i}", reaction_type="like"))
    await db_session.commit()
    
    # 3. Add replies
    for i in range(4):
        db_session.add(ChatMessage(id=f"reply-{i}", channel="general", sender=f"cat{i}", content="Agree", thread_id="msg-1"))
    await db_session.commit()
    
    # 4. Compute score
    # score = 5 (reactions) + 4 * 1.5 (replies) = 5 + 6 = 11.0
    score = await compute_trending_score(db_session, "msg-1")
    assert score == 11.0
    
    # 5. Update trending scores
    updated = await update_trending_scores(db_session)
    assert len(updated) == 1
    assert updated[0]["message_id"] == "msg-1"
    assert updated[0]["score"] == 11.0
    
    # Verify record in TrendingDiscussion
    res = await db_session.execute(select(TrendingDiscussion).where(TrendingDiscussion.message_id == "msg-1"))
    td = res.scalar_one()
    assert td.current_score == 11.0

    # 6. Maybe surface idea
    # Threshold is 10, so it should surface
    surfaced = await maybe_surface_idea(db_session, "msg-1", 11.0)
    assert surfaced is True
    
    # Verify Idea in DB
    result = await db_session.execute(select(Idea).where(Idea.source_message_id == "msg-1"))
    idea = result.scalar_one()
    assert "Trending: New toy idea" in idea.title

    # 7. Test update path (upsert)
    # Add another reaction
    db_session.add(MessageReaction(message_id="msg-1", reactor_id="cat-new", reaction_type="love"))
    await db_session.commit()

    # Update again
    updated2 = await update_trending_scores(db_session)
    assert len(updated2) == 1
    assert updated2[0]["score"] == 12.0

    # Verify TrendingDiscussion was updated
    await db_session.refresh(td)
    assert td.current_score == 12.0

@pytest.mark.asyncio
async def test_compute_trending_score_edge_cases(db_session):
    # Non-existent message
    assert await compute_trending_score(db_session, "no-such-msg") == 0.0

    # Old message
    old_ts = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3)
    msg = ChatMessage(id="old-msg", channel="general", sender="cat", content="Old news", timestamp=old_ts)
    db_session.add(msg)
    await db_session.commit()

    assert await compute_trending_score(db_session, "old-msg") == 0.0

@pytest.mark.asyncio
async def test_update_trending_scores_empty(db_session):
    updated = await update_trending_scores(db_session)
    assert updated == []

@pytest.mark.asyncio
async def test_maybe_surface_idea_edge_cases(db_session):
    # Score below threshold
    assert await maybe_surface_idea(db_session, "msg-any", 1.0) is False

    # Message already surfaced as idea
    msg = ChatMessage(id="msg-2", channel="general", sender="cat", content="Another idea")
    db_session.add(msg)
    db_session.add(Idea(author_id="system", title="Idea 2", source_message_id="msg-2"))
    await db_session.commit()

    assert await maybe_surface_idea(db_session, "msg-2", 20.0) is False

    # Message not found
    assert await maybe_surface_idea(db_session, "missing-msg", 20.0) is False

@pytest.mark.asyncio
async def test_endpoints_direct(db_session, monkeypatch):
    # Mock SessionLocal to use our test db_session
    from backend.api import trending

    class MockSession:
        async def __aenter__(self): return db_session
        async def __aexit__(self, *args): pass

    monkeypatch.setattr(trending, "SessionLocal", MockSession)

    # Seed data
    db_session.add(TrendingDiscussion(message_id="m1", current_score=15.0, window_start=datetime.datetime.now()))
    await db_session.commit()

    # Test get_trending
    res = await get_trending()
    assert len(res) == 1
    assert res[0]["message_id"] == "m1"

    # Test trigger_update
    # We need a message with a reaction in the window for trigger_update to do something
    now = datetime.datetime.now(datetime.timezone.utc)
    db_session.add(ChatMessage(id="m3", channel="h", sender="s", content="c", timestamp=now))
    db_session.add(MessageReaction(message_id="m3", reactor_id="r", reaction_type="l", created_at=now))
    await db_session.commit()

    res_update = await trigger_update()
    assert res_update["scores_updated"] >= 1
