"""
trending.py — Trending discussion scoring and ideas auto-surface trigger.

Score formula: score = reaction_count + (reply_count * 1.5)
Score decays to 0 after IDEAS_WINDOW_HOURS (default: 48h).
Auto-surfaces when score >= IDEAS_AUTO_SURFACE_THRESHOLD (default: 10).
"""

import datetime

from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import SessionLocal
from backend.models import ChatMessage, Idea, IdeaVote, MessageReaction, TrendingDiscussion

IDEAS_WINDOW_HOURS = 48
IDEAS_AUTO_SURFACE_THRESHOLD = 10

router = APIRouter(prefix="/api/v2/trending", tags=["trending"])


async def compute_trending_score(session: AsyncSession, message_id: str) -> float:
    """
    Compute trending score for a message.

    Score = reaction_count + (reply_count * 1.5)
    Returns 0.0 if the message is older than IDEAS_WINDOW_HOURS or not found.
    """
    # Fetch the message to check its age
    msg = await session.get(ChatMessage, message_id)
    if msg is None:
        return 0.0

    # Check age — if the message is outside the window, score decays to 0
    now = datetime.datetime.now(datetime.timezone.utc)
    msg_ts = msg.timestamp
    if msg_ts is not None and msg_ts.tzinfo is None:
        # Make naive datetimes timezone-aware for comparison
        msg_ts = msg_ts.replace(tzinfo=datetime.timezone.utc)

    if msg_ts is None or (now - msg_ts).total_seconds() > IDEAS_WINDOW_HOURS * 3600:
        return 0.0

    # Count reactions for this message
    reaction_count_result = await session.execute(
        select(func.count(MessageReaction.id)).where(
            MessageReaction.message_id == message_id
        )
    )
    reaction_count: int = reaction_count_result.scalar_one() or 0

    # Count replies — ChatMessage rows where thread_id == message_id
    reply_count_result = await session.execute(
        select(func.count(ChatMessage.id)).where(
            ChatMessage.thread_id == message_id
        )
    )
    reply_count: int = reply_count_result.scalar_one() or 0

    score = reaction_count + (reply_count * 1.5)
    return score


async def update_trending_scores(session: AsyncSession) -> list[dict]:
    """
    Recompute scores for all messages that have reactions within the window.

    Upserts TrendingDiscussion rows. Returns the updated list as dicts.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    window_start = now - datetime.timedelta(hours=IDEAS_WINDOW_HOURS)

    # Find all message_ids with at least one reaction in the window
    result = await session.execute(
        select(MessageReaction.message_id)
        .where(MessageReaction.created_at >= window_start)
        .distinct()
    )
    message_ids: list[str] = list(result.scalars().all())

    updated: list[dict] = []

    for message_id in message_ids:
        score = await compute_trending_score(session, message_id)

        # Upsert: look for an existing TrendingDiscussion row
        existing_result = await session.execute(
            select(TrendingDiscussion).where(
                TrendingDiscussion.message_id == message_id
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing is not None:
            existing.current_score = score
            existing.window_start = window_start
        else:
            td = TrendingDiscussion(
                message_id=message_id,
                current_score=score,
                window_start=window_start,
            )
            session.add(td)

        updated.append({"message_id": message_id, "score": score})

    await session.commit()
    return updated


async def maybe_surface_idea(
    session: AsyncSession, message_id: str, score: float
) -> bool:
    """
    If score >= threshold and the message isn't already in the ideas table,
    insert a new Idea row.

    Returns True if a new idea was created, False otherwise.
    """
    if score < IDEAS_AUTO_SURFACE_THRESHOLD:
        return False

    # Check if an idea already exists for this source message
    existing_result = await session.execute(
        select(Idea).where(Idea.source_message_id == message_id)
    )
    if existing_result.scalar_one_or_none() is not None:
        return False

    # Fetch the message to pull its content for the title
    msg = await session.get(ChatMessage, message_id)
    if msg is None:
        return False

    title = f"Trending: {msg.content[:100]}"

    idea = Idea(
        author_id="system",  # auto-surfaced by the trending system
        title=title,
        description="",
        status="pending",
        source_message_id=message_id,
    )
    session.add(idea)
    await session.commit()
    return True


# ── REST endpoints ─────────────────────────────────────────────────────────────


@router.get("")
async def get_trending():
    """Return the top 10 TrendingDiscussion rows by score."""
    async with SessionLocal() as db:
        result = await db.execute(
            select(TrendingDiscussion)
            .order_by(TrendingDiscussion.current_score.desc())
            .limit(10)
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "message_id": r.message_id,
                "current_score": r.current_score,
                "window_start": r.window_start.isoformat() if r.window_start else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


@router.post("/update")
async def trigger_update():
    """
    Recompute all trending scores and surface ideas for any that cross the threshold.

    Returns the count of newly surfaced ideas.
    """
    async with SessionLocal() as db:
        updated = await update_trending_scores(db)

        new_ideas = 0
        for entry in updated:
            if entry["score"] >= IDEAS_AUTO_SURFACE_THRESHOLD:
                surfaced = await maybe_surface_idea(db, entry["message_id"], entry["score"])
                if surfaced:
                    new_ideas += 1

        return {
            "scores_updated": len(updated),
            "new_ideas_surfaced": new_ideas,
        }
