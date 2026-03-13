"""
rag_service.py — Clowder v2 RAG Service
Provides context retrieval and seeding for the RAG pipeline.

EmbeddingService is injected (not created here) so this module works
whether called from FastAPI or from tests with a mock encoder.
"""

import datetime
from typing import Callable, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ContextItem, RetrievalLog, TaskEmbedding


async def query_context(
    session: AsyncSession,
    query_text: str,
    encode_fn: Callable[[str], list[float]],
    top_k: int = 5,
    agent_id: str = "system",
    source_type_filter: Optional[str] = None,
) -> list[dict]:
    """
    Retrieve top_k semantically similar context items for query_text.

    Uses pgvector <=> (cosine distance) operator for similarity search.
    Falls back to recency-based retrieval if pgvector is unavailable or
    if the embedding column does not support cosine_distance (e.g. JSON
    fallback column when pgvector is not installed).

    Returns list of dicts with keys: id, source_type, source_id, content, tags
    """
    try:
        query_embedding = encode_fn(query_text)

        # pgvector cosine similarity query.
        # ContextItem.embedding is a Vector(384) column when pgvector is
        # installed, which exposes the .cosine_distance() comparator.
        stmt = select(ContextItem).order_by(
            ContextItem.embedding.cosine_distance(query_embedding)
        ).limit(top_k)

        if source_type_filter:
            stmt = stmt.where(ContextItem.source_type == source_type_filter)

        result = await session.execute(stmt)
        items = result.scalars().all()

    except Exception:
        # pgvector not available, embedding column is JSON, or encode_fn
        # raised — fall back to most-recent records.
        stmt = select(ContextItem).order_by(desc(ContextItem.created_at)).limit(top_k)
        if source_type_filter:
            stmt = stmt.where(ContextItem.source_type == source_type_filter)
        result = await session.execute(stmt)
        items = result.scalars().all()

    # Log retrieval
    log = RetrievalLog(
        agent_id=agent_id,
        query_text=query_text[:500],
        results_returned=len(items),
    )
    session.add(log)
    await session.commit()

    return [
        {
            "id": item.id,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "content": item.content,
            "tags": item.tags or [],
        }
        for item in items
    ]


async def seed_from_task(
    session: AsyncSession,
    task_id: str,
    task_title: str,
    result_text: str,
    encode_fn: Callable[[str], list[float]],
    tags: Optional[list[str]] = None,
) -> int:
    """
    Store a completed task result as a context item and task embedding.
    Called when a task is marked done.
    Returns the ContextItem id.
    """
    content = f"Task: {task_title}\nResult: {result_text}"

    try:
        embedding = encode_fn(content)
    except Exception:
        embedding = None

    # Store in context_items
    item = ContextItem(
        source_type="task_result",
        source_id=task_id,
        content=content,
        embedding=embedding,
        tags=tags or [],
    )
    session.add(item)

    # Store in task_embeddings
    task_emb = TaskEmbedding(
        task_id=task_id,
        embedding=embedding,
        summary_text=result_text[:500],
    )
    session.add(task_emb)

    await session.commit()
    await session.refresh(item)
    return item.id


async def seed_from_message(
    session: AsyncSession,
    message_id: str,
    sender: str,
    channel: str,
    content: str,
    encode_fn: Callable[[str], list[float]],
) -> int:
    """
    Store a chat message as a context item.
    Called asynchronously after a message is saved to DB.
    Returns the ContextItem id.
    """
    full_content = f"[{channel}] {sender}: {content}"

    try:
        embedding = encode_fn(full_content)
    except Exception:
        embedding = None

    item = ContextItem(
        source_type="chat_message",
        source_id=message_id,
        content=full_content,
        embedding=embedding,
        tags=[channel],
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item.id
