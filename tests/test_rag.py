"""
test_rag.py — RAG Pipeline Test Suite (Sprint 2)
Tests backend.rag_service functions using a deterministic mock encoder
so tests run fast without loading sentence-transformers.
"""

import hashlib
import random

import pytest
from sqlalchemy import select


# ---------------------------------------------------------------------------
# Mock encoder — deterministic, no ML model needed
# ---------------------------------------------------------------------------

def mock_encode(text: str) -> list[float]:
    """Deterministic mock embedding — same text always gives same vector."""
    h = int(hashlib.md5(text.encode()).hexdigest(), 16)
    rng = random.Random(h)
    vec = [rng.uniform(-1, 1) for _ in range(384)]
    mag = sum(x**2 for x in vec) ** 0.5
    return [x / mag for x in vec]


# ---------------------------------------------------------------------------
# Test 1: mock_encode is deterministic and correct shape
# ---------------------------------------------------------------------------

def test_mock_encode_deterministic():
    vec = mock_encode("hello world")
    assert len(vec) == 384
    assert all(isinstance(x, float) for x in vec)
    assert vec == mock_encode("hello world")          # deterministic
    assert vec != mock_encode("different text")       # different input -> different vector


# ---------------------------------------------------------------------------
# Test 2: seed_from_task stores context_item and task_embedding
# ---------------------------------------------------------------------------

async def test_seed_from_task_creates_records(db_session):
    from backend.rag_service import seed_from_task
    from backend.models import ContextItem, TaskEmbedding

    item_id = await seed_from_task(
        session=db_session,
        task_id="task-test-001",
        task_title="Implement JWT auth",
        result_text="Used short-lived tokens with 15min expiry.",
        encode_fn=mock_encode,
    )
    assert item_id is not None

    result = await db_session.execute(
        select(ContextItem).where(ContextItem.source_id == "task-test-001")
    )
    item = result.scalar_one_or_none()
    assert item is not None
    assert item.source_type == "task_result"
    assert "JWT" in item.content

    emb = await db_session.execute(
        select(TaskEmbedding).where(TaskEmbedding.task_id == "task-test-001")
    )
    task_emb = emb.scalar_one_or_none()
    assert task_emb is not None


# ---------------------------------------------------------------------------
# Test 3: seed_from_message stores context_item
# ---------------------------------------------------------------------------

async def test_seed_from_message_creates_record(db_session):
    from backend.rag_service import seed_from_message
    from backend.models import ContextItem

    item_id = await seed_from_message(
        session=db_session,
        message_id="msg-abc-001",
        sender="qwen",
        channel="main-hall",
        content="We should use parallel code reviews for speed.",
        encode_fn=mock_encode,
    )
    assert item_id is not None

    result = await db_session.execute(
        select(ContextItem).where(ContextItem.source_id == "msg-abc-001")
    )
    item = result.scalar_one_or_none()
    assert item is not None
    assert item.source_type == "chat_message"
    assert "main-hall" in item.tags


# ---------------------------------------------------------------------------
# Test 4: query_context returns results and logs retrieval
# ---------------------------------------------------------------------------

async def test_query_context_returns_and_logs(db_session):
    from backend.rag_service import seed_from_task, query_context
    from backend.models import RetrievalLog

    # Seed some context first
    await seed_from_task(db_session, "task-q-001", "Setup OAuth", "OAuth2 with PKCE flow.", mock_encode)
    await seed_from_task(db_session, "task-q-002", "JWT refresh tokens", "Short-lived JWTs.", mock_encode)

    results = await query_context(
        session=db_session,
        query_text="authentication tokens",
        encode_fn=mock_encode,
        top_k=5,
        agent_id="gemini-test",
    )

    assert isinstance(results, list)
    assert len(results) >= 1
    for r in results:
        assert "content" in r
        assert "source_type" in r

    # Check retrieval was logged
    logs = await db_session.execute(
        select(RetrievalLog).where(RetrievalLog.agent_id == "gemini-test")
    )
    log_row = logs.scalar_one_or_none()
    assert log_row is not None
    assert log_row.results_returned >= 1


# ---------------------------------------------------------------------------
# Test 5: query_context with no stored data returns empty list (or list)
# ---------------------------------------------------------------------------

async def test_query_context_empty_returns_empty_list(db_session):
    from backend.rag_service import query_context

    results = await query_context(
        session=db_session,
        query_text="completely unrelated obscure topic xyz123",
        encode_fn=mock_encode,
        top_k=5,
        agent_id="gemini-empty-test",
    )
    assert isinstance(results, list)
    # May return results (recency fallback) or empty — must not raise


# ---------------------------------------------------------------------------
# Test 6: query_context source_type_filter works
# ---------------------------------------------------------------------------

async def test_query_context_filters_by_source_type(db_session):
    from backend.rag_service import seed_from_task, seed_from_message, query_context

    await seed_from_task(db_session, "task-f-001", "Deploy k8s", "Used helm charts.", mock_encode)
    await seed_from_message(
        db_session, "msg-f-001", "claude", "general", "Discussing deployment.", mock_encode
    )

    task_results = await query_context(
        session=db_session,
        query_text="deployment",
        encode_fn=mock_encode,
        top_k=10,
        agent_id="filter-test",
        source_type_filter="task_result",
    )
    assert all(r["source_type"] == "task_result" for r in task_results)


# ---------------------------------------------------------------------------
# Test 7: encode_fn exception is handled gracefully (embedding falls back to None)
# ---------------------------------------------------------------------------

async def test_seed_handles_encode_failure_gracefully(db_session):
    from backend.rag_service import seed_from_task
    from backend.models import ContextItem

    def bad_encode(text: str) -> list[float]:
        raise RuntimeError("Model not available")

    # Should not raise — embedding stored as None, content still saved
    item_id = await seed_from_task(
        session=db_session,
        task_id="task-bad-enc-001",
        task_title="Test task",
        result_text="Some result",
        encode_fn=bad_encode,
    )
    assert item_id is not None

    result = await db_session.execute(
        select(ContextItem).where(ContextItem.source_id == "task-bad-enc-001")
    )
    item = result.scalar_one_or_none()
    assert item is not None
    assert item.embedding is None  # stored without embedding
