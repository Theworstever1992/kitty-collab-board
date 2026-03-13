
import pytest
from sqlalchemy import select
from backend.models import ChatMessage, MessageReaction, TrendingDiscussion, Idea
from backend.api.trending import compute_trending_score, update_trending_scores, maybe_surface_idea

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
    
    # 6. Maybe surface idea
    # Threshold is 10, so it should surface
    surfaced = await maybe_surface_idea(db_session, "msg-1", 11.0)
    assert surfaced is True
    
    # Verify Idea in DB
    result = await db_session.execute(select(Idea).where(Idea.source_message_id == "msg-1"))
    idea = result.scalar_one()
    assert "Trending: New toy idea" in idea.title
