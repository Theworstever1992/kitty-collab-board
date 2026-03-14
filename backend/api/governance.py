"""
governance.py — Governance API: token reporting and efficiency.
Includes token efficiency scoring per agent.
"""

from typing import Optional, List
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query, Depends
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import TokenUsage

router = APIRouter(prefix="/api/v2/governance", tags=["governance"])


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.get("/token-report")
async def token_report(db: AsyncSession = Depends(get_db)):
    """
    Per-agent token totals.
    Groups TokenUsage rows by agent, returns list of
    {agent, total_input, total_output, total_cost_usd, request_count}.
    """
    result = await db.execute(
        select(
            TokenUsage.agent,
            func.sum(TokenUsage.input_tokens).label("total_input"),
            func.sum(TokenUsage.output_tokens).label("total_output"),
            func.sum(TokenUsage.cost_usd).label("total_cost_usd"),
            func.count(TokenUsage.id).label("request_count"),
        ).group_by(TokenUsage.agent)
    )
    rows = result.all()
    return [
        {
            "agent": row.agent,
            "total_input": row.total_input or 0,
            "total_output": row.total_output or 0,
            "total_cost_usd": round(row.total_cost_usd or 0.0, 6),
            "request_count": row.request_count or 0,
        }
        for row in rows
    ]


@router.get("/token-efficiency")
async def token_efficiency(
    agent_id: Optional[str] = Query(None, description="Filter by specific agent"),
    days: int = Query(7, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """
    Calculate token efficiency score per agent.
    
    Efficiency = (output_tokens / input_tokens) * cost_factor
    Higher score = more efficient (more output per input token)
    
    Returns agents sorted by efficiency score (descending).
    """
    # Get token usage for the specified period
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    query = select(
        TokenUsage.agent,
        func.sum(TokenUsage.input_tokens).label("total_input"),
        func.sum(TokenUsage.output_tokens).label("total_output"),
        func.sum(TokenUsage.cost_usd).label("total_cost"),
        func.count(TokenUsage.id).label("request_count"),
        func.avg(TokenUsage.input_tokens).label("avg_input"),
        func.avg(TokenUsage.output_tokens).label("avg_output"),
    ).where(
        TokenUsage.logged_at >= cutoff
    )

    if agent_id:
        query = query.where(TokenUsage.agent == agent_id)

    query = query.group_by(TokenUsage.agent).order_by(desc("total_output"))

    result = await db.execute(query)
    rows = result.all()

    efficiency_data = []
    for row in rows:
        # Calculate efficiency score
        input_tokens = row.total_input or 0
        output_tokens = row.total_output or 0
        
        # Efficiency ratio: output per input token
        efficiency_ratio = (output_tokens / input_tokens * 100) if input_tokens > 0 else 0
        
        # Cost per output token (lower is better)
        cost_per_output = (row.total_cost / output_tokens * 1000) if output_tokens > 0 else 0
        
        # Combined efficiency score (0-100)
        # Higher ratio + lower cost = higher score
        efficiency_score = min(100, efficiency_ratio * (1 / (cost_per_output + 0.01)))
        
        efficiency_data.append({
            "agent_id": row.agent,
            "total_input_tokens": input_tokens,
            "total_output_tokens": output_tokens,
            "total_cost_usd": round(row.total_cost or 0.0, 6),
            "request_count": row.request_count or 0,
            "avg_input_tokens": round(row.avg_input or 0, 2),
            "avg_output_tokens": round(row.avg_output or 0, 2),
            "efficiency_ratio": round(efficiency_ratio, 2),
            "cost_per_1k_output": round(cost_per_output, 4),
            "efficiency_score": round(efficiency_score, 2),
            "period_days": days,
        })

    # Sort by efficiency score descending
    efficiency_data.sort(key=lambda x: x["efficiency_score"], reverse=True)

    return efficiency_data
