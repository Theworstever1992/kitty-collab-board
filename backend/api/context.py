"""
context.py — Mid-task context retrieval endpoint.
Agents call this during task execution to request more relevant context.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.database import SessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v2/context", tags=["context"])


class ContextQueryRequest(BaseModel):
    query: str
    agent_id: str = "unknown"
    top_k: int = 5
    source_type: str | None = None


async def get_session():
    async with SessionLocal() as session:
        yield session


@router.post("/query")
async def query_context_endpoint(
    req: ContextQueryRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        from backend.rag_service import query_context
        from backend.embeddings import get_embedding_service
        svc = get_embedding_service()
        results = await query_context(
            session=session,
            query_text=req.query,
            encode_fn=svc.encode,
            top_k=req.top_k,
            agent_id=req.agent_id,
            source_type_filter=req.source_type,
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        return {"results": [], "count": 0, "error": str(e)}
