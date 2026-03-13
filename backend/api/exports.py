"""
exports.py — Agent export/import for portability across projects.
"""

import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select

from backend.database import SessionLocal
from backend.models import Agent

router = APIRouter(prefix="/api/v2/agents", tags=["exports"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class ImportAgentRequest(BaseModel):
    name: str
    role: str
    model: str | None = None
    bio: str | None = None
    skills: list[str] | None = None
    personality_seed: str | None = None
    rag_config: dict | None = None
    system_prompt: str | None = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{name}/export")
async def export_agent(name: str, format: str = "json"):
    """
    Export an agent profile for portability.

    format=json (default) — returns JSON dict with profile + metadata.
    format=md             — returns a Markdown summary as text/markdown.
    """
    async with SessionLocal() as db:
        agent = await db.get(Agent, name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

    export_dict = {
        "name": agent.name,
        "role": agent.role,
        "model": agent.model,
        "bio": agent.bio or "",
        "skills": agent.skills or [],
        "personality_seed": agent.personality_seed or "",
        "rag_config": {},
        "system_prompt": "",
        "exported_at": datetime.datetime.now(datetime.UTC).isoformat() + "Z",
    }

    if format == "md":
        skills_list = "\n".join(
            f"- {s}" for s in (agent.skills or [])
        ) or "_(none)_"
        md_text = (
            f"# Agent: {agent.name}\n"
            f"**Role:** {agent.role}\n"
            f"**Bio:** {agent.bio or ''}\n"
            f"## Skills\n"
            f"{skills_list}\n"
            f"## Personality Seed\n"
            f"{agent.personality_seed or ''}\n"
        )
        return Response(content=md_text, media_type="text/markdown")

    return export_dict


@router.post("/import")
async def import_agent(req: ImportAgentRequest):
    """
    Import an agent from an exported profile dict.

    - If an agent with req.name already exists: updates profile fields
      (bio, skills, personality_seed) without overwriting name or model.
    - If the name is new: creates a fresh Agent row with all provided fields.

    Returns {"imported": True, "name": <name>, "created": <bool>}.
    """
    if not req.name:
        raise HTTPException(status_code=422, detail="name is required")
    if not req.role:
        raise HTTPException(status_code=422, detail="role is required")

    async with SessionLocal() as db:
        existing = await db.get(Agent, req.name)
        created = existing is None

        if existing:
            # Update profile fields only — name and model are not overwritten
            existing.role = req.role
            if req.bio is not None:
                existing.bio = req.bio
            if req.skills is not None:
                existing.skills = req.skills
            if req.personality_seed is not None:
                existing.personality_seed = req.personality_seed
        else:
            db.add(Agent(
                name=req.name,
                role=req.role,
                model=req.model or "unknown",
                bio=req.bio,
                skills=req.skills,
                personality_seed=req.personality_seed,
                hired_at=datetime.datetime.now(datetime.UTC),
            ))

        await db.commit()

    return {"imported": True, "name": req.name, "created": created}
