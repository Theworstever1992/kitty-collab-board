
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models import StandardsViolation, Agent

router = APIRouter(prefix="/api/v2/violations", tags=["standards"])


@router.get("/")
async def list_violations(
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    violation_type: Optional[str] = Query(None, description="Filter by violation type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, description="Max results"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    List standards violations with optional filters.
    """
    stmt = select(StandardsViolation).order_by(desc(StandardsViolation.flagged_at)).limit(limit)
    
    if agent_id:
        stmt = stmt.where(StandardsViolation.agent_id == agent_id)
    if violation_type:
        stmt = stmt.where(StandardsViolation.violation_type == violation_type)
    if severity:
        stmt = stmt.where(StandardsViolation.severity == severity)
    
    result = await db.execute(stmt)
    violations = result.scalars().all()
    
    res_list = []
    for v in violations:
        v_dict = {
            "id": v.id,
            "violation_type": v.violation_type,
            "agent_id": v.agent_id,
            "task_id": v.task_id,
            "severity": v.severity,
            "notes": v.notes,
            "flagged_at": v.flagged_at.isoformat() if v.flagged_at else None,
        }
        res_list.append(v_dict)
    
    return res_list


@router.get("/repeat-offenders")
async def get_repeat_offenders(
    min_violations: int = Query(3, description="Minimum violations to be considered repeat offender"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Get agents with multiple violations.
    """
    stmt = (
        select(
            StandardsViolation.agent_id,
            func.count(StandardsViolation.id).label("violation_count"),
            func.max(StandardsViolation.flagged_at).label("last_violation"),
        )
        .group_by(StandardsViolation.agent_id)
        .having(func.count(StandardsViolation.id) >= min_violations)
        .order_by(desc("violation_count"))
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    offenders = []
    for row in rows:
        offenders.append({
            "agent_id": row.agent_id,
            "total_violations": row.violation_count,
            "last_violation": row.last_violation.isoformat() if row.last_violation else None,
        })
    
    return offenders


from pydantic import BaseModel
class ViolationIn(BaseModel):
    violation_type: str
    agent_id: str
    task_id: Optional[str] = None
    severity: str = "medium"
    notes: Optional[str] = None

@router.post("/", status_code=201)
async def create_violation(
    req: ViolationIn,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Create a new standards violation.
    """
    if req.severity not in ["low", "medium", "high", "critical"]:
        raise HTTPException(status_code=400, detail="Invalid severity level")
    
    # Check if agent exists
    agent = await db.get(Agent, req.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {req.agent_id} not found")
    
    violation = StandardsViolation(
        violation_type=req.violation_type,
        agent_id=req.agent_id,
        task_id=req.task_id,
        severity=req.severity,
        notes=req.notes,
        flagged_at=datetime.now(datetime.UTC),
    )
    
    db.add(violation)
    await db.commit()
    await db.refresh(violation)
    
    return {
        "id": violation.id,
        "violation_type": req.violation_type,
        "agent_id": req.agent_id,
        "task_id": req.task_id,
        "severity": req.severity,
        "notes": req.notes,
        "flagged_at": violation.flagged_at.isoformat(),
    }
