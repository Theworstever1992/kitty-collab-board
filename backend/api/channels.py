"""
channels.py — Channel listing endpoint for the v2 API.

Derives the channel list dynamically from distinct channel names in the
ChatMessage table, with per-channel message counts.  A set of well-known
default channels is always included so the sidebar is never empty.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import ChatMessage

router = APIRouter(prefix="/api/v2/channels", tags=["channels"])

# Well-known channels always surfaced in the sidebar even before any messages
_DEFAULT_CHANNELS: dict[str, str] = {
    "main-hall":  "General discussion for the whole team",
    "war-room":   "High-priority escalations and major decisions",
    "assembly":   "System announcements",
    "manager":    "Manager coordination channel",
    "team-alpha": "Team Alpha workspace",
    "team-beta":  "Team Beta workspace",
}


def _default_channel(name: str, count: int = 0) -> dict:
    return {
        "name": name,
        "description": _DEFAULT_CHANNELS.get(name, ""),
        "message_count": count,
    }


@router.get("")
async def list_channels(db: AsyncSession = Depends(get_db)):
    """
    Return all channels with message counts.

    Includes every channel that has at least one ChatMessage plus the
    well-known default channels (with count = 0 if no messages yet).
    """
    result = await db.execute(
        select(
            ChatMessage.channel,
            func.count(ChatMessage.id).label("message_count"),
        ).group_by(ChatMessage.channel)
    )
    rows = result.all()

    seen: dict[str, int] = {row.channel: row.message_count for row in rows}

    # Merge defaults — preserve real counts for defaults that have messages
    for name in _DEFAULT_CHANNELS:
        seen.setdefault(name, 0)

    return [
        _default_channel(name, count)
        for name, count in sorted(seen.items())
    ]
