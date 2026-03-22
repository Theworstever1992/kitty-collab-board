"""
tasks_v2.py — v2 task endpoints under /api/v2/tasks.

Mirrors the task routes in main.py but lives under the /api/v2 prefix
so the frontend API client (which calls /api/v2/tasks/*) can reach them.
"""

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Task

router = APIRouter(prefix="/api/v2/tasks", tags=["tasks-v2"])


class ClaimRequest(BaseModel):
    agent_name: str
    claimed_at: str


class CompleteRequest(BaseModel):
    agent_name: str
    result: str
    completed_at: str | None = None


def _task_dict(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "role": t.role,
        "team_id": t.team_id,
        "priority": t.priority,
        "priority_order": t.priority_order,
        "skills": t.skills,
        "blocked_by": t.blocked_by,
        "claimed_by": t.claimed_by,
        "claimed_at": t.claimed_at,
        "result": t.result,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("")
async def list_tasks(team_id: str | None = None, db: AsyncSession = Depends(get_db)):
    """List all tasks, optionally filtered by team_id."""
    q = select(Task)
    if team_id:
        q = q.where(Task.team_id == team_id)
    rows = (await db.execute(q)).scalars().all()
    return [_task_dict(t) for t in rows]


@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_dict(task)


@router.post("/{task_id}/claim")
async def claim_task(task_id: str, req: ClaimRequest, db: AsyncSession = Depends(get_db)):
    """First-claim-wins: only transitions pending → claimed."""
    result = await db.execute(
        update(Task)
        .where(Task.id == task_id, Task.status == "pending")
        .values(
            status="claimed",
            claimed_by=req.agent_name,
            claimed_at=req.claimed_at,
        )
    )
    await db.commit()
    return {"claimed": result.rowcount == 1}


@router.post("/{task_id}/complete")
async def complete_task(task_id: str, req: CompleteRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        update(Task)
        .where(Task.id == task_id, Task.claimed_by == req.agent_name)
        .values(
            status="done",
            result=req.result,
            completed_at=datetime.datetime.now(datetime.timezone.utc),
        )
    )
    await db.commit()
    return {"ok": result.rowcount == 1}
