"""
agents.py — Agent profile endpoints with avatar SVG validation.
"""

# defusedxml protects against XXE, billion-laughs, and other XML injection attacks.
# This is a security-conscious drop-in replacement for xml.etree.ElementTree.
import defusedxml.ElementTree as ET

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from backend.database import SessionLocal
from backend.models import Agent

router = APIRouter(prefix="/api/v2/agents", tags=["agents"])


# ── Pydantic models ────────────────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    bio: str | None = None
    skills: list[str] | None = None
    personality_seed: str | None = None
    avatar_svg: str | None = None  # validated before storing


# ── Avatar SVG validation ──────────────────────────────────────────────────────

def validate_avatar_svg(svg_text: str) -> None:
    """
    Validate an SVG string for use as an agent avatar.

    Checks:
    - Size must not exceed 50 KB (51,200 bytes).
    - Must be well-formed XML parseable by defusedxml (protects against XXE and
      other XML injection attacks).
    - Root element must be <svg> (with or without namespace prefix).

    Raises HTTPException(422) on any violation.
    """
    if len(svg_text.encode()) > 51_200:
        raise HTTPException(status_code=422, detail="Avatar exceeds 50KB limit")

    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        raise HTTPException(status_code=422, detail="Invalid SVG: malformed XML")

    # ElementTree represents namespaced tags as "{namespace}localname"
    # Accept both bare "svg" and namespace-qualified "{...}svg"
    tag = root.tag
    if not (tag == "svg" or tag.endswith("}svg")):
        raise HTTPException(status_code=422, detail="Invalid SVG: root element is not <svg>")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _agent_summary(a: Agent) -> dict:
    """Return a lightweight agent dict suitable for list responses."""
    return {
        "name": a.name,
        "role": a.role,
        "model": a.model,
        "team": a.team,
        "status": a.status,
        "last_seen": a.last_seen.isoformat() if a.last_seen else None,
        "bio": a.bio,
        "skills": a.skills,
    }


def _agent_full(a: Agent) -> dict:
    """Return the full agent profile dict."""
    return {
        "name": a.name,
        "role": a.role,
        "model": a.model,
        "team": a.team,
        "status": a.status,
        "last_seen": a.last_seen.isoformat() if a.last_seen else None,
        "started_at": a.started_at.isoformat() if a.started_at else None,
        "bio": a.bio,
        "avatar_svg": a.avatar_svg,
        "skills": a.skills,
        "personality_seed": a.personality_seed,
        "hired_at": a.hired_at.isoformat() if a.hired_at else None,
        "fired_at": a.fired_at.isoformat() if a.fired_at else None,
        "fire_reason": a.fire_reason,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_agents():
    """List all agents (summary fields only)."""
    async with SessionLocal() as db:
        rows = (await db.execute(select(Agent))).scalars().all()
        return [_agent_summary(a) for a in rows]


@router.get("/{name}")
async def get_agent(name: str):
    """Get a single agent's full profile."""
    async with SessionLocal() as db:
        agent = await db.get(Agent, name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return _agent_full(agent)


@router.patch("/{name}/profile")
async def update_profile(name: str, req: UpdateProfileRequest):
    """
    Update an agent's profile fields (bio, skills, personality_seed, avatar_svg).
    avatar_svg is validated for size, XML well-formedness, and root element before storage.
    """
    if req.avatar_svg is not None:
        validate_avatar_svg(req.avatar_svg)

    async with SessionLocal() as db:
        agent = await db.get(Agent, name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        if req.bio is not None:
            agent.bio = req.bio
        if req.skills is not None:
            agent.skills = req.skills
        if req.personality_seed is not None:
            agent.personality_seed = req.personality_seed
        if req.avatar_svg is not None:
            agent.avatar_svg = req.avatar_svg

        await db.commit()
        await db.refresh(agent)
        return _agent_full(agent)


@router.patch("/{name}/avatar")
async def update_avatar(name: str, req: UpdateProfileRequest):
    """
    Update an agent's avatar SVG specifically.
    Matches the frontend api.updateAvatar call.
    """
    if req.avatar_svg is None:
        raise HTTPException(status_code=400, detail="avatar_svg is required")
    
    validate_avatar_svg(req.avatar_svg)

    async with SessionLocal() as db:
        agent = await db.get(Agent, name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent.avatar_svg = req.avatar_svg
        await db.commit()
        await db.refresh(agent)
        return _agent_full(agent)
