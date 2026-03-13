"""
ideas.py — Ideas feed endpoints.
Ideas surface organically from trending chat, or are manually promoted.
"""

import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import SessionLocal
from backend.models import Idea, IdeaVote

router = APIRouter(prefix="/api/v2/ideas", tags=["ideas"])


# ── Pydantic request models ────────────────────────────────────────────────────


class CreateIdeaRequest(BaseModel):
    title: str
    description: str = ""
    source_message_id: Optional[str] = None
    submitted_by: str = "operator"


class UpdateIdeaStatusRequest(BaseModel):
    status: str  # "approved" | "rejected" | "pending"
    reviewed_by: str = "operator"


class VoteRequest(BaseModel):
    voter_id: str


# ── Helper ────────────────────────────────────────────────────────────────────


async def _idea_with_votes(session: AsyncSession, idea: Idea) -> dict:
    """Serialize an Idea ORM row, augmenting with its current vote count."""
    vote_count_result = await session.execute(
        select(func.count(IdeaVote.id)).where(IdeaVote.idea_id == idea.id)
    )
    vote_count: int = vote_count_result.scalar_one() or 0

    return {
        "id": idea.id,
        "author_id": idea.author_id,
        "title": idea.title,
        "description": idea.description,
        "status": idea.status,
        "approved_by": idea.approved_by,
        "source_message_id": idea.source_message_id,
        "created_at": idea.created_at.isoformat() if idea.created_at else None,
        "vote_count": vote_count,
    }


# ── REST endpoints ─────────────────────────────────────────────────────────────


@router.get("")
async def list_ideas():
    """List all ideas sorted by vote count descending."""
    async with SessionLocal() as db:
        # Fetch all ideas
        result = await db.execute(select(Idea).order_by(Idea.created_at.desc()))
        ideas = result.scalars().all()

        # Build vote counts in one query: {idea_id: count}
        vote_counts_result = await db.execute(
            select(IdeaVote.idea_id, func.count(IdeaVote.id).label("cnt"))
            .group_by(IdeaVote.idea_id)
        )
        vote_map: dict[int, int] = {
            row.idea_id: row.cnt for row in vote_counts_result
        }

        items = []
        for idea in ideas:
            items.append(
                {
                    "id": idea.id,
                    "author_id": idea.author_id,
                    "title": idea.title,
                    "description": idea.description,
                    "status": idea.status,
                    "approved_by": idea.approved_by,
                    "source_message_id": idea.source_message_id,
                    "created_at": idea.created_at.isoformat() if idea.created_at else None,
                    "vote_count": vote_map.get(idea.id, 0),
                }
            )

        # Sort by vote count descending
        items.sort(key=lambda x: x["vote_count"], reverse=True)
        return items


@router.post("")
async def create_idea(req: CreateIdeaRequest):
    """Manually create an idea (status defaults to 'pending')."""
    async with SessionLocal() as db:
        idea = Idea(
            author_id=req.submitted_by,
            title=req.title,
            description=req.description,
            status="pending",
            source_message_id=req.source_message_id,
        )
        db.add(idea)
        await db.commit()
        return await _idea_with_votes(db, idea)


@router.get("/{idea_id}")
async def get_idea(idea_id: int):
    """Fetch a single idea by ID."""
    async with SessionLocal() as db:
        idea = await db.get(Idea, idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Idea not found")
        return await _idea_with_votes(db, idea)


@router.patch("/{idea_id}/status")
async def update_idea_status(idea_id: int, req: UpdateIdeaStatusRequest):
    """Update an idea's status and record who reviewed it."""
    valid_statuses = {"approved", "rejected", "pending"}
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status '{req.status}'. Must be one of: {sorted(valid_statuses)}",
        )

    async with SessionLocal() as db:
        idea = await db.get(Idea, idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Idea not found")

        idea.status = req.status
        # Idea model only has approved_by — use it for both approve and reject reviewer
        idea.approved_by = req.reviewed_by

        await db.commit()
        return await _idea_with_votes(db, idea)


@router.post("/{idea_id}/vote")
async def vote_for_idea(idea_id: int, req: VoteRequest):
    """
    Upsert a vote from voter_id for the given idea.
    Returns the current vote count after the operation.
    """
    async with SessionLocal() as db:
        idea = await db.get(Idea, idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Idea not found")

        # Check for existing vote from this voter
        existing_result = await db.execute(
            select(IdeaVote).where(
                IdeaVote.idea_id == idea_id,
                IdeaVote.voter_id == req.voter_id,
            )
        )
        existing_vote = existing_result.scalar_one_or_none()

        if existing_vote is None:
            vote = IdeaVote(idea_id=idea_id, voter_id=req.voter_id)
            db.add(vote)
            await db.commit()

        # Return current vote count
        count_result = await db.execute(
            select(func.count(IdeaVote.id)).where(IdeaVote.idea_id == idea_id)
        )
        vote_count: int = count_result.scalar_one() or 0
        return {"idea_id": idea_id, "vote_count": vote_count}


@router.delete("/{idea_id}/vote")
async def delete_vote(idea_id: int, voter_id: str):
    """Remove a vote from voter_id for the given idea."""
    async with SessionLocal() as db:
        idea = await db.get(Idea, idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Idea not found")

        result = await db.execute(
            select(IdeaVote).where(
                IdeaVote.idea_id == idea_id,
                IdeaVote.voter_id == voter_id,
            )
        )
        vote = result.scalar_one_or_none()

        if vote is None:
            raise HTTPException(status_code=404, detail="Vote not found")

        await db.delete(vote)
        await db.commit()

        count_result = await db.execute(
            select(func.count(IdeaVote.id)).where(IdeaVote.idea_id == idea_id)
        )
        vote_count: int = count_result.scalar_one() or 0
        return {"idea_id": idea_id, "vote_count": vote_count}
