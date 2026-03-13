"""
onboarding.py — Onboarding flow for new agents joining the v2 system.
Handles registration, profile setup, avatar selection, and intro post.
"""

import httpx

DEFAULT_AVATARS = ["tabby", "tuxedo", "calico"]


def pick_default_avatar(agent_name: str) -> str:
    """Deterministically pick one of the 3 default avatar names based on agent name hash."""
    idx = sum(ord(c) for c in agent_name) % 3
    return DEFAULT_AVATARS[idx]


async def onboard_agent(
    api_base: str,
    name: str,
    role: str,
    bio: str = "",
    skills: list[str] | None = None,
    personality_seed: str = "",
) -> dict:
    """
    Full onboarding flow for a new agent joining the v2 system.

    Steps:
    1. POST /api/agents/register — register the agent (creates DB row / updates existing).
    2. PATCH /api/v2/agents/{name}/profile — set bio, skills, and personality_seed.
    3. POST /api/v2/chat/main-hall — post an intro message so other agents know about the arrival.

    Returns the registration response dict from step 1.

    Args:
        api_base:         Base URL of the v2 API, e.g. "http://localhost:9000".
        name:             Agent name (must be unique; used as primary key).
        role:             Agent role string, e.g. "coder" or "reviewer".
        bio:              Short bio paragraph (stored in Agent.bio).
        skills:           List of skill tags, e.g. ["python", "testing"].
        personality_seed: Freeform text that seeds the agent's personality prompt.

    Raises:
        httpx.HTTPStatusError: if any API call returns a non-2xx status.
    """
    if skills is None:
        skills = []

    avatar = pick_default_avatar(name)

    async with httpx.AsyncClient(base_url=api_base, timeout=10.0) as client:
        # Step 1 — Register
        reg_resp = await client.post(
            "/api/agents/register",
            json={"name": name, "role": role},
        )
        reg_resp.raise_for_status()
        registration_result = reg_resp.json()

        # Step 2 — Set profile
        profile_resp = await client.patch(
            f"/api/v2/agents/{name}/profile",
            json={
                "bio": bio,
                "skills": skills,
                "personality_seed": personality_seed,
            },
        )
        profile_resp.raise_for_status()

        # Step 3 — Post intro message to main-hall
        intro_content = (
            f"Hi everyone! I'm **{name}** ({role}). "
            f"Avatar style: {avatar}. "
            f"{bio}" if bio else f"Hi everyone! I'm **{name}** ({role}). Avatar style: {avatar}."
        )
        chat_resp = await client.post(
            "/api/v2/chat/main-hall",
            json={
                "sender": name,
                "content": intro_content,
                "type": "chat",
            },
        )
        chat_resp.raise_for_status()

    return registration_result
