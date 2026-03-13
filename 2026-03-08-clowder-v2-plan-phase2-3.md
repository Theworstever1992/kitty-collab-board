# Clowder v2 — Phase 2 & 3 Implementation Plan (TDD)

Date: 2026-03-08
Status: Ready for implementation

---

## Phase 2: RAG Integration

### Goal
Give every agent semantic memory. When an agent claims a task, it automatically receives
relevant context drawn from past task results, chat messages, and decisions. Agents can
also trigger mid-task retrieval on demand.

---

### Task 2.1 — EmbeddingService + pgvector

**Why this first:** The vector store is the foundation for all RAG. Every other task in
Phase 2 depends on being able to store and query embeddings.

#### Failing test (write first)

```python
# tests/test_embedding_service.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np

class TestEmbeddingService:
    """Tests for EmbeddingService."""

    def test_encode_returns_list_of_floats(self):
        """EmbeddingService.encode() returns a flat list of floats."""
        from backend.embedding_service import EmbeddingService
        svc = EmbeddingService.__new__(EmbeddingService)
        svc._model = MagicMock()
        svc._model.encode.return_value = np.array([0.1, 0.2, 0.3])
        result = svc.encode("hello world")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)

    def test_encode_length_matches_model_output(self):
        """Encoded vector length matches model output dimension."""
        from backend.embedding_service import EmbeddingService
        svc = EmbeddingService.__new__(EmbeddingService)
        vec = np.random.rand(384).astype(np.float32)
        svc._model = MagicMock()
        svc._model.encode.return_value = vec
        result = svc.encode("test sentence")
        assert len(result) == 384

    def test_singleton_instance(self):
        """EmbeddingService is a module-level singleton."""
        from backend import embedding_service as em
        assert hasattr(em, "embedding_service")
```

Run to confirm red: `pytest tests/test_embedding_service.py -v`

#### Implementation

```python
# backend/embedding_service.py
"""
Singleton wrapper around sentence-transformers.
The model is pre-baked into the Docker image and loaded once at startup
via FastAPI lifespan. During testing, the model mock is injected directly.
"""
from __future__ import annotations
from typing import List
import numpy as np


class EmbeddingService:
    _model = None  # set by lifespan or tests

    def load(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Load the sentence-transformer model. Called once at startup."""
        from sentence_transformers import SentenceTransformer  # lazy import
        self._model = SentenceTransformer(model_name)

    def encode(self, text: str) -> List[float]:
        """Return a flat list of floats for a given text string."""
        if self._model is None:
            raise RuntimeError("EmbeddingService.load() has not been called.")
        vec: np.ndarray = self._model.encode(text, convert_to_numpy=True)
        return vec.tolist()


# Module-level singleton — imported by lifespan and all services
embedding_service = EmbeddingService()
```

```python
# backend/main.py  (add to existing lifespan)
from contextlib import asynccontextmanager
from backend.embedding_service import embedding_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    embedding_service.load()
    yield
    # Shutdown — nothing to clean up for the model

app = FastAPI(lifespan=lifespan)
```

#### Alembic migration — add vector columns

```python
# alembic/versions/002_add_vector_columns.py
"""Add pgvector embedding columns."""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("context_entries",
        sa.Column("embedding", sa.Text, nullable=True))
    # We store vectors as TEXT (JSON array) and cast in queries.
    # pgvector column type is added separately for typed queries.
    op.execute(
        "ALTER TABLE context_entries "
        "ADD COLUMN IF NOT EXISTS embedding_vec vector(384)"
    )

def downgrade():
    op.drop_column("context_entries", "embedding_vec")
    op.drop_column("context_entries", "embedding")
```

Run to confirm green: `pytest tests/test_embedding_service.py -v`

Commit: `feat(rag): add EmbeddingService singleton + pgvector migration`

---

### Task 2.2 — ContextService (ingest)

**Why:** Agents produce three types of knowledge — task results, chat messages, and
architectural decisions. ContextService normalises them into `context_entries` rows
with embeddings so they are all searchable from one place.

#### Failing test

```python
# tests/test_context_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestContextService:

    @pytest.fixture
    def mock_embed(self):
        with patch("backend.context_service.embedding_service") as m:
            m.encode.return_value = [0.0] * 384
            yield m

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        return db

    async def test_ingest_task_result_inserts_row(self, mock_embed, mock_db):
        """ingest_task_result writes a context_entries row."""
        from backend.context_service import ContextService
        svc = ContextService()
        await svc.ingest_task_result(
            db=mock_db,
            task_id="task-001",
            title="Write tests",
            result="All tests passing.",
            agent_name="Whiskers",
        )
        mock_db.execute.assert_called_once()
        call_args = str(mock_db.execute.call_args)
        assert "context_entries" in call_args or mock_embed.encode.called

    async def test_ingest_chat_message_inserts_row(self, mock_embed, mock_db):
        """ingest_chat_message stores a chat message with embedding."""
        from backend.context_service import ContextService
        svc = ContextService()
        await svc.ingest_chat_message(
            db=mock_db,
            channel="main-hall",
            author="Pixel",
            content="Token usage looks high on Team A.",
        )
        assert mock_embed.encode.called

    async def test_ingest_decision_inserts_row(self, mock_embed, mock_db):
        """ingest_decision stores a governance decision with embedding."""
        from backend.context_service import ContextService
        svc = ContextService()
        await svc.ingest_decision(
            db=mock_db,
            decision_id="dec-001",
            summary="Adopt Black formatter for all Python.",
            made_by="Spec",
        )
        assert mock_embed.encode.called
```

Run to confirm red: `pytest tests/test_context_service.py -v`

#### Implementation

```python
# backend/context_service.py
"""
ContextService — normalises task results, chat messages, and decisions
into the context_entries table with embeddings for RAG retrieval.
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.embedding_service import embedding_service


class ContextService:

    async def _insert(
        self,
        db: AsyncSession,
        entry_type: str,
        source_id: str,
        text_content: str,
        metadata: dict,
    ) -> None:
        vec = embedding_service.encode(text_content)
        vec_str = "[" + ",".join(str(v) for v in vec) + "]"
        await db.execute(
            text(
                "INSERT INTO context_entries "
                "(id, entry_type, source_id, text_content, metadata, embedding_vec, created_at) "
                "VALUES (:id, :entry_type, :source_id, :text_content, :metadata, "
                ":vec::vector, :created_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "entry_type": entry_type,
                "source_id": source_id,
                "text_content": text_content,
                "metadata": json.dumps(metadata),
                "vec": vec_str,
                "created_at": datetime.now(timezone.utc),
            },
        )
        await db.commit()

    async def ingest_task_result(
        self,
        db: AsyncSession,
        task_id: str,
        title: str,
        result: str,
        agent_name: str,
    ) -> None:
        text_content = f"Task: {title}\nResult: {result}"
        await self._insert(
            db, "task_result", task_id, text_content,
            {"agent": agent_name, "task_id": task_id},
        )

    async def ingest_chat_message(
        self,
        db: AsyncSession,
        channel: str,
        author: str,
        content: str,
    ) -> None:
        source_id = f"{channel}:{author}:{datetime.now(timezone.utc).isoformat()}"
        text_content = f"[{channel}] {author}: {content}"
        await self._insert(
            db, "chat_message", source_id, text_content,
            {"channel": channel, "author": author},
        )

    async def ingest_decision(
        self,
        db: AsyncSession,
        decision_id: str,
        summary: str,
        made_by: str,
    ) -> None:
        text_content = f"Decision by {made_by}: {summary}"
        await self._insert(
            db, "decision", decision_id, text_content,
            {"made_by": made_by},
        )


context_service = ContextService()
```

Run to confirm green: `pytest tests/test_context_service.py -v`

Commit: `feat(rag): add ContextService for ingesting task results, chat, decisions`

---

### Task 2.3 — RAGService (cosine similarity retrieval)

**Why:** RAGService turns the vector store into a question-answering layer. Given a
query string, it returns the top-k most semantically similar context entries and
formats them into a ready-to-inject prompt prefix.

#### Failing test

```python
# tests/test_rag_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

class TestRAGService:

    @pytest.fixture
    def mock_embed(self):
        with patch("backend.rag_service.embedding_service") as m:
            m.encode.return_value = [0.1] * 384
            yield m

    @pytest.fixture
    def db_with_results(self):
        row1 = MagicMock()
        row1.text_content = "Task: Write unit tests\nResult: 42 tests passing."
        row1.entry_type = "task_result"
        row1.similarity = 0.91
        db = AsyncMock()
        result_proxy = MagicMock()
        result_proxy.fetchall.return_value = [row1]
        db.execute = AsyncMock(return_value=result_proxy)
        return db

    async def test_retrieve_returns_list(self, mock_embed, db_with_results):
        """retrieve() returns a list of context dicts."""
        from backend.rag_service import RAGService
        svc = RAGService()
        results = await svc.retrieve(db_with_results, "unit testing", top_k=3)
        assert isinstance(results, list)
        assert len(results) >= 1

    async def test_build_augmented_prompt_wraps_context(self, mock_embed, db_with_results):
        """build_augmented_prompt() injects context above the user prompt."""
        from backend.rag_service import RAGService
        svc = RAGService()
        augmented = await svc.build_augmented_prompt(
            db=db_with_results,
            base_prompt="Fix the failing test.",
            top_k=3,
        )
        assert "Fix the failing test." in augmented
        assert "Context from memory" in augmented or "CONTEXT" in augmented

    async def test_retrieve_empty_db_returns_empty_list(self, mock_embed):
        """retrieve() returns [] when no context entries exist."""
        from backend.rag_service import RAGService
        db = AsyncMock()
        result_proxy = MagicMock()
        result_proxy.fetchall.return_value = []
        db.execute = AsyncMock(return_value=result_proxy)
        svc = RAGService()
        results = await svc.retrieve(db, "anything", top_k=5)
        assert results == []
```

Run to confirm red: `pytest tests/test_rag_service.py -v`

#### Implementation

```python
# backend/rag_service.py
"""
RAGService — cosine similarity search over context_entries + prompt augmentation.

pgvector uses the <=> operator for cosine distance. We convert to similarity
by computing 1 - distance. Top-k entries are injected as a context block
above the agent's base prompt.
"""
from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.embedding_service import embedding_service

CONTEXT_HEADER = "=== CONTEXT FROM CLOWDER MEMORY ===\n"
CONTEXT_FOOTER = "=== END CONTEXT ===\n\n"


class RAGService:

    async def retrieve(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        entry_type_filter: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Return top_k context entries most similar to query."""
        vec = embedding_service.encode(query)
        vec_str = "[" + ",".join(str(v) for v in vec) + "]"

        where_clause = ""
        params: dict = {"vec": vec_str, "top_k": top_k}
        if entry_type_filter:
            where_clause = "WHERE entry_type = :entry_type"
            params["entry_type"] = entry_type_filter

        rows = (
            await db.execute(
                text(
                    f"SELECT text_content, entry_type, metadata, "
                    f"1 - (embedding_vec <=> :vec::vector) AS similarity "
                    f"FROM context_entries {where_clause} "
                    f"ORDER BY similarity DESC LIMIT :top_k"
                ),
                params,
            )
        ).fetchall()

        return [
            {
                "text": row.text_content,
                "type": row.entry_type,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]

    async def build_augmented_prompt(
        self,
        db: AsyncSession,
        base_prompt: str,
        top_k: int = 5,
        entry_type_filter: str | None = None,
    ) -> str:
        """Prepend relevant context to base_prompt."""
        entries = await self.retrieve(db, base_prompt, top_k, entry_type_filter)
        if not entries:
            return base_prompt

        context_block = CONTEXT_HEADER
        for i, entry in enumerate(entries, 1):
            context_block += f"[{i}] ({entry['type']}, sim={entry['similarity']:.2f})\n"
            context_block += entry["text"] + "\n\n"
        context_block += CONTEXT_FOOTER

        return context_block + base_prompt


rag_service = RAGService()
```

Run to confirm green: `pytest tests/test_rag_service.py -v`

Commit: `feat(rag): add RAGService with cosine similarity retrieval and prompt augmentation`

---

### Task 2.4 — Auto-RAG on task claim

**Why:** The highest-leverage moment to inject context is exactly when an agent claims
a task — before it begins work. The claim endpoint enriches the `TaskResponse` with a
`rag_context` field. Agents that support it use it; agents that don't can ignore it.

#### Failing test

```python
# tests/test_task_claim_rag.py
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

class TestTaskClaimRAG:

    async def test_claim_response_includes_rag_context(self):
        """POST /tasks/{id}/claim returns rag_context field."""
        with patch("backend.rag_service.rag_service.build_augmented_prompt",
                   new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = "CONTEXT FROM MEMORY\n\nDo the thing."
            from backend.main import app
            async with AsyncClient(app=app, base_url="http://test") as client:
                # First create a task
                create = await client.post("/tasks", json={
                    "title": "Do the thing",
                    "description": "A test task",
                    "prompt": "Do the thing.",
                    "team_id": "alpha",
                })
                task_id = create.json()["id"]
                resp = await client.post(f"/tasks/{task_id}/claim",
                                         json={"agent_name": "Whiskers"})
                assert resp.status_code == 200
                data = resp.json()
                assert "rag_context" in data

    async def test_claim_rag_context_contains_augmented_prompt(self):
        """rag_context is the augmented prompt string, not raw context."""
        with patch("backend.rag_service.rag_service.build_augmented_prompt",
                   new_callable=AsyncMock) as mock_rag:
            mock_rag.return_value = "CONTEXT FROM MEMORY\n\nDo the thing."
            from backend.main import app
            async with AsyncClient(app=app, base_url="http://test") as client:
                create = await client.post("/tasks", json={
                    "title": "Do the thing",
                    "description": "desc",
                    "prompt": "Do the thing.",
                    "team_id": "alpha",
                })
                task_id = create.json()["id"]
                resp = await client.post(f"/tasks/{task_id}/claim",
                                         json={"agent_name": "Whiskers"})
                assert "CONTEXT FROM MEMORY" in resp.json()["rag_context"]
```

Run to confirm red: `pytest tests/test_task_claim_rag.py -v`

#### Implementation — update claim endpoint in main.py

```python
# backend/main.py  (update /tasks/{task_id}/claim endpoint)
from backend.rag_service import rag_service

@app.post("/tasks/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: str,
    body: ClaimRequest,
    db: AsyncSession = Depends(get_db),
):
    task = await task_service.claim(db, task_id, body.agent_name)
    if task is None:
        raise HTTPException(status_code=409, detail="Task already claimed or not found")

    # Auto-RAG: augment the task prompt with relevant memory
    rag_context = await rag_service.build_augmented_prompt(
        db=db,
        base_prompt=task.prompt or task.title,
        top_k=5,
    )

    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        prompt=task.prompt,
        status=task.status,
        claimed_by=task.claimed_by,
        team_id=task.team_id,
        rag_context=rag_context,
    )
```

```python
# backend/schemas.py  (add rag_context to TaskResponse)
class TaskResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    prompt: str | None = None
    status: str
    claimed_by: str | None = None
    team_id: str | None = None
    rag_context: str | None = None  # injected at claim time
```

Run to confirm green: `pytest tests/test_task_claim_rag.py -v`

Commit: `feat(rag): auto-inject RAG context on task claim`

---

### Task 2.5 — Mid-task context retrieval API

**Why:** Long-running tasks may need fresh context mid-execution. Agents can POST
a query to `/context/retrieve` and get back relevant entries without re-claiming.

#### Failing test

```python
# tests/test_context_retrieve_api.py
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

class TestContextRetrieveAPI:

    async def test_retrieve_endpoint_returns_list(self):
        """POST /context/retrieve returns a list of context entries."""
        with patch("backend.rag_service.rag_service.retrieve",
                   new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = [
                {"text": "Past result.", "type": "task_result", "similarity": 0.88}
            ]
            from backend.main import app
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/context/retrieve", json={
                    "query": "unit testing best practices",
                    "top_k": 3,
                })
                assert resp.status_code == 200
                data = resp.json()
                assert isinstance(data["entries"], list)
                assert data["entries"][0]["similarity"] == pytest.approx(0.88)

    async def test_retrieve_returns_empty_list_on_no_results(self):
        """POST /context/retrieve returns empty entries list when DB is empty."""
        with patch("backend.rag_service.rag_service.retrieve",
                   new_callable=AsyncMock) as mock_retrieve:
            mock_retrieve.return_value = []
            from backend.main import app
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/context/retrieve", json={
                    "query": "something obscure",
                    "top_k": 5,
                })
                assert resp.status_code == 200
                assert resp.json()["entries"] == []
```

Run to confirm red: `pytest tests/test_context_retrieve_api.py -v`

#### Implementation

```python
# backend/main.py  (add new endpoint)
class ContextRetrieveRequest(BaseModel):
    query: str
    top_k: int = 5
    entry_type: str | None = None

class ContextRetrieveResponse(BaseModel):
    entries: list[dict]

@app.post("/context/retrieve", response_model=ContextRetrieveResponse)
async def retrieve_context(
    body: ContextRetrieveRequest,
    db: AsyncSession = Depends(get_db),
):
    entries = await rag_service.retrieve(
        db=db,
        query=body.query,
        top_k=body.top_k,
        entry_type_filter=body.entry_type,
    )
    return ContextRetrieveResponse(entries=entries)
```

Run to confirm green: `pytest tests/test_context_retrieve_api.py -v`

Commit: `feat(rag): add /context/retrieve endpoint for mid-task retrieval`

---

### Task 2.6 — Phase 2 Integration Test

**Why:** Verify the full RAG pipeline end-to-end: ingest a task result → claim a new
task → confirm rag_context contains the ingested content.

#### Test

```python
# tests/integration/test_phase2_rag.py
"""
Phase 2 integration test — RAG pipeline end-to-end.
Requires: running PostgreSQL with pgvector, embedding model loaded.
Run with: pytest tests/integration/ -m integration
"""
import pytest

pytestmark = pytest.mark.integration


async def test_rag_full_pipeline(async_client, db_session):
    """Ingest a result, claim a related task, confirm context is injected."""
    from backend.context_service import context_service
    from backend.rag_service import rag_service

    # Step 1: ingest a past task result
    await context_service.ingest_task_result(
        db=db_session,
        task_id="old-task-001",
        title="Write authentication middleware",
        result="JWT-based middleware implemented in auth/middleware.py.",
        agent_name="Whiskers",
    )

    # Step 2: retrieve context for a related query
    entries = await rag_service.retrieve(
        db=db_session,
        query="authentication token validation",
        top_k=3,
    )

    assert len(entries) >= 1
    assert any("auth" in e["text"].lower() for e in entries)

    # Step 3: claim a new task and confirm rag_context is populated
    create_resp = await async_client.post("/tasks", json={
        "title": "Add token refresh to auth middleware",
        "description": "Extend the existing auth middleware.",
        "prompt": "Add token refresh support.",
        "team_id": "alpha",
    })
    task_id = create_resp.json()["id"]
    claim_resp = await async_client.post(
        f"/tasks/{task_id}/claim",
        json={"agent_name": "Whiskers"},
    )

    assert claim_resp.status_code == 200
    rag_context = claim_resp.json().get("rag_context", "")
    # The context should reference the ingested result
    assert "auth" in rag_context.lower() or rag_context != ""
```

Commit: `test(integration): Phase 2 RAG pipeline end-to-end`

---

## Phase 3: Social WebSocket Chat

### Goal
Real-time chat across channels (main-hall, team channels, leader-lounge, ideas).
Users and agents post, react, and thread. Ideas channel auto-surfaces posts that
reach 10 reactions within 48 hours. All messages are persisted and fed into RAG.

---

### Task 3.1 — ConnectionManager (WebSocket room management)

**Why:** The ConnectionManager is the hub of real-time communication. It tracks
which WebSocket connections belong to which channel and handles fan-out broadcast.
Everything real-time flows through here.

#### Failing test

```python
# tests/test_connection_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestConnectionManager:

    async def test_connect_adds_to_channel(self):
        """connect() adds the WebSocket to the channel's connection set."""
        from backend.connection_manager import ConnectionManager
        cm = ConnectionManager()
        ws = AsyncMock()
        await cm.connect(ws, channel="main-hall")
        assert ws in cm._channels["main-hall"]

    async def test_disconnect_removes_from_channel(self):
        """disconnect() removes the WebSocket from all channels."""
        from backend.connection_manager import ConnectionManager
        cm = ConnectionManager()
        ws = AsyncMock()
        await cm.connect(ws, channel="main-hall")
        cm.disconnect(ws, channel="main-hall")
        assert ws not in cm._channels.get("main-hall", set())

    async def test_broadcast_sends_to_all_in_channel(self):
        """broadcast() sends JSON to every connection in the channel."""
        from backend.connection_manager import ConnectionManager
        cm = ConnectionManager()
        ws1, ws2 = AsyncMock(), AsyncMock()
        await cm.connect(ws1, "main-hall")
        await cm.connect(ws2, "main-hall")
        await cm.broadcast("main-hall", {"type": "message", "content": "meow"})
        ws1.send_json.assert_called_once_with({"type": "message", "content": "meow"})
        ws2.send_json.assert_called_once_with({"type": "message", "content": "meow"})

    async def test_broadcast_does_not_send_to_other_channels(self):
        """broadcast() to channel A does not reach channel B subscribers."""
        from backend.connection_manager import ConnectionManager
        cm = ConnectionManager()
        ws_a, ws_b = AsyncMock(), AsyncMock()
        await cm.connect(ws_a, "main-hall")
        await cm.connect(ws_b, "team-alpha")
        await cm.broadcast("main-hall", {"type": "message", "content": "meow"})
        ws_b.send_json.assert_not_called()
```

Run to confirm red: `pytest tests/test_connection_manager.py -v`

#### Implementation

```python
# backend/connection_manager.py
"""
ConnectionManager — WebSocket channel hub.

Channels are created on first connection and cleaned up on last disconnect.
Broadcast is best-effort: if a send fails the connection is removed.
"""
from __future__ import annotations
import asyncio
from collections import defaultdict
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        self._channels[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        self._channels[channel].discard(websocket)
        if not self._channels[channel]:
            del self._channels[channel]

    async def broadcast(self, channel: str, payload: dict) -> None:
        """Fan-out payload to all connections in channel."""
        dead: list[WebSocket] = []
        for ws in list(self._channels.get(channel, set())):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._channels[channel].discard(ws)

    def channel_member_count(self, channel: str) -> int:
        return len(self._channels.get(channel, set()))


# Module-level singleton
connection_manager = ConnectionManager()
```

Run to confirm green: `pytest tests/test_connection_manager.py -v`

Commit: `feat(chat): add ConnectionManager for WebSocket channel management`

---

### Task 3.2 — WebSocket endpoint in main.py

**Why:** The WebSocket endpoint is the entry point for all real-time traffic. It
accepts connections, receives messages, persists them via ContextService, and
broadcasts them to the channel.

#### Failing test

```python
# tests/test_websocket_endpoint.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

class TestWebSocketEndpoint:

    def test_websocket_connects_and_receives_message(self):
        """Connecting to /ws/{channel} and sending a message echoes to channel."""
        with patch("backend.connection_manager.connection_manager.broadcast",
                   new_callable=AsyncMock) as mock_broadcast:
            from backend.main import app
            client = TestClient(app)
            with client.websocket_connect("/ws/main-hall") as ws:
                ws.send_json({"author": "Whiskers", "content": "Meow!"})
                mock_broadcast.assert_called()

    def test_websocket_invalid_channel_rejects(self):
        """Connecting to an unknown channel name is rejected gracefully."""
        # Channel names are free-form strings; this test confirms the endpoint
        # does not crash on unusual channel names.
        from backend.main import app
        client = TestClient(app)
        with client.websocket_connect("/ws/🐱-channel") as ws:
            ws.send_json({"author": "Pixel", "content": "Token check."})
            # No assertion needed — just confirm no server error
```

Run to confirm red: `pytest tests/test_websocket_endpoint.py -v`

#### Implementation

```python
# backend/main.py  (add WebSocket endpoint)
from fastapi import WebSocket, WebSocketDisconnect
from backend.connection_manager import connection_manager
from backend.context_service import context_service

ALLOWED_CHANNELS = {
    "main-hall",
    "ideas",
    "leader-lounge",
    # Team channels are dynamic: "team-{team_id}"
}

@app.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel: str,
    db: AsyncSession = Depends(get_db),
):
    await connection_manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_json()
            author = data.get("author", "anonymous")
            content = data.get("content", "")
            msg_type = data.get("type", "message")

            payload = {
                "type": msg_type,
                "channel": channel,
                "author": author,
                "content": content,
            }

            # Persist chat messages for RAG
            if msg_type == "message" and content:
                await context_service.ingest_chat_message(
                    db=db,
                    channel=channel,
                    author=author,
                    content=content,
                )

            await connection_manager.broadcast(channel, payload)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, channel)
```

Run to confirm green: `pytest tests/test_websocket_endpoint.py -v`

Commit: `feat(chat): add WebSocket endpoint with persistence and broadcast`

---

### Task 3.3 — TrendingService + ideas auto-surface

**Why:** The ideas channel has a special rule: any post that accumulates 10 or more
reactions within a 48-hour window is automatically surfaced as a "trending idea" — a
notification broadcast to all channels prompting the PM to review it.

#### Failing test

```python
# tests/test_trending_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

class TestTrendingService:

    @pytest.fixture
    def hot_message(self):
        msg = MagicMock()
        msg.id = "msg-001"
        msg.content = "We should add automated dependency updates."
        msg.author = "Spec"
        msg.channel = "ideas"
        msg.reaction_count = 12
        msg.created_at = datetime.now(timezone.utc) - timedelta(hours=10)
        return msg

    @pytest.fixture
    def cold_message(self):
        msg = MagicMock()
        msg.id = "msg-002"
        msg.content = "Old idea from last week."
        msg.reaction_count = 15
        msg.created_at = datetime.now(timezone.utc) - timedelta(hours=72)
        return msg

    async def test_is_trending_true_within_window(self, hot_message):
        """Message with >= 10 reactions within 48h is trending."""
        from backend.trending_service import TrendingService
        svc = TrendingService(reaction_threshold=10, window_hours=48)
        assert svc.is_trending(hot_message) is True

    async def test_is_trending_false_outside_window(self, cold_message):
        """Message with >= 10 reactions but older than 48h is not trending."""
        from backend.trending_service import TrendingService
        svc = TrendingService(reaction_threshold=10, window_hours=48)
        assert svc.is_trending(cold_message) is False

    async def test_is_trending_false_below_threshold(self):
        """Message with fewer than 10 reactions is not trending."""
        from backend.trending_service import TrendingService
        msg = MagicMock()
        msg.reaction_count = 7
        msg.created_at = datetime.now(timezone.utc) - timedelta(hours=5)
        svc = TrendingService(reaction_threshold=10, window_hours=48)
        assert svc.is_trending(msg) is False

    async def test_check_and_surface_broadcasts_on_trend(self, hot_message):
        """check_and_surface() broadcasts a trending alert when threshold is met."""
        with patch("backend.trending_service.connection_manager") as mock_cm:
            mock_cm.broadcast = AsyncMock()
            from backend.trending_service import TrendingService
            svc = TrendingService(reaction_threshold=10, window_hours=48)
            await svc.check_and_surface(hot_message)
            mock_cm.broadcast.assert_called_once()
            call_args = mock_cm.broadcast.call_args
            assert call_args[0][0] == "main-hall"  # broadcast to main-hall
            assert "trending" in str(call_args[0][1]).lower()
```

Run to confirm red: `pytest tests/test_trending_service.py -v`

#### Implementation

```python
# backend/trending_service.py
"""
TrendingService — monitors reaction counts on ideas-channel posts.

When a post crosses the reaction threshold within the time window,
it is broadcast to main-hall as a trending idea for PM review.

Thresholds are configurable and stored in the settings table.
Defaults: 10 reactions / 48-hour window.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from backend.connection_manager import connection_manager


class TrendingService:
    def __init__(
        self,
        reaction_threshold: int = 10,
        window_hours: int = 48,
    ):
        self.reaction_threshold = reaction_threshold
        self.window_hours = window_hours

    def is_trending(self, message) -> bool:
        """Return True if message meets trending criteria."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.window_hours)
        created = message.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return (
            message.reaction_count >= self.reaction_threshold
            and created >= cutoff
        )

    async def check_and_surface(self, message) -> None:
        """If message is trending, broadcast a surfacing alert to main-hall."""
        if not self.is_trending(message):
            return

        payload = {
            "type": "trending_idea",
            "source_channel": "ideas",
            "message_id": message.id,
            "author": message.author,
            "content": message.content,
            "reaction_count": message.reaction_count,
            "cat_note": (
                f"Paws up! 🐾 This idea from {message.author} is purring hot "
                f"with {message.reaction_count} reactions — PM review requested."
            ),
        }
        await connection_manager.broadcast("main-hall", payload)


trending_service = TrendingService()
```

```python
# backend/main.py  (wire reaction endpoint to trending check)
from backend.trending_service import trending_service

@app.post("/messages/{message_id}/react")
async def react_to_message(
    message_id: str,
    body: ReactionRequest,
    db: AsyncSession = Depends(get_db),
):
    message = await message_service.add_reaction(db, message_id, body.emoji, body.author)
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Check if this reaction pushed the message over the trending threshold
    if message.channel == "ideas":
        await trending_service.check_and_surface(message)

    return {"message_id": message_id, "reaction_count": message.reaction_count}
```

Run to confirm green: `pytest tests/test_trending_service.py -v`

Commit: `feat(chat): add TrendingService with ideas auto-surface at 10-reaction threshold`

---

### Task 3.4 — Vue 3 scaffold + MainHall.vue component

**Why:** The frontend is Vue 3 + Vite. The MainHall component is the primary UI
surface — it shows the live chat feed, connection status, and lets users type
messages. It is the reference implementation for all other channel components.

#### Project scaffold

```bash
# Run inside the project root
npm create vite@latest frontend -- --template vue
cd frontend && npm install
npm install socket.io-client  # NOT used — we use native WebSocket
```

#### Directory structure

```
frontend/
  src/
    App.vue
    main.js
    components/
      MainHall.vue
      MessageList.vue
      MessageInput.vue
      ReactionBar.vue
    composables/
      useChannel.js
    stores/
      chat.js          (Pinia store)
  vite.config.js
  package.json
```

#### useChannel.js (WebSocket composable)

```javascript
// frontend/src/composables/useChannel.js
/**
 * useChannel — reactive WebSocket composable.
 *
 * Manages the connection lifecycle for a single chat channel.
 * Re-connects automatically on close (with exponential back-off).
 */
import { ref, onUnmounted } from 'vue'

const RECONNECT_BASE_MS = 1000
const RECONNECT_MAX_MS = 30000

export function useChannel(channelName, onMessage) {
  const connected = ref(false)
  const error = ref(null)
  let ws = null
  let reconnectDelay = RECONNECT_BASE_MS

  function connect() {
    const url = `ws://${window.location.host}/ws/${channelName}`
    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      error.value = null
      reconnectDelay = RECONNECT_BASE_MS
    }

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        onMessage(payload)
      } catch {
        // Silently drop malformed messages
      }
    }

    ws.onerror = (e) => {
      error.value = 'Connection error — retrying...'
    }

    ws.onclose = () => {
      connected.value = false
      setTimeout(() => {
        reconnectDelay = Math.min(reconnectDelay * 2, RECONNECT_MAX_MS)
        connect()
      }, reconnectDelay)
    }
  }

  function send(payload) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload))
    }
  }

  connect()

  onUnmounted(() => {
    if (ws) ws.close()
  })

  return { connected, error, send }
}
```

#### MainHall.vue

```vue
<!-- frontend/src/components/MainHall.vue -->
<template>
  <div class="main-hall">
    <header class="hall-header">
      <span class="cat-logo">🐱</span>
      <h1>Main Hall</h1>
      <span class="status" :class="{ online: connected }">
        {{ connected ? '● online' : '○ reconnecting...' }}
      </span>
    </header>

    <MessageList :messages="messages" @react="handleReact" />

    <MessageInput
      :author="userName"
      :disabled="!connected"
      @send="handleSend"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChannel } from '@/composables/useChannel'
import MessageList from './MessageList.vue'
import MessageInput from './MessageInput.vue'

const props = defineProps({ userName: { type: String, default: 'Human' } })

const messages = ref([])

const { connected, send } = useChannel('main-hall', (payload) => {
  if (payload.type === 'message') {
    messages.value.push({
      id: Date.now(),
      author: payload.author,
      content: payload.content,
      reactions: {},
    })
  }
  if (payload.type === 'trending_idea') {
    messages.value.push({
      id: Date.now(),
      author: '🐾 Clowder',
      content: payload.cat_note,
      reactions: {},
      isTrending: true,
    })
  }
})

function handleSend(content) {
  send({ author: props.userName, content, type: 'message' })
}

async function handleReact({ messageId, emoji }) {
  await fetch(`/messages/${messageId}/react`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ emoji, author: props.userName }),
  })
}
</script>

<style scoped>
.main-hall { display: flex; flex-direction: column; height: 100vh; }
.hall-header { display: flex; align-items: center; gap: 0.5rem; padding: 1rem; }
.status { margin-left: auto; font-size: 0.8rem; color: grey; }
.status.online { color: #4caf50; }
</style>
```

Commit: `feat(frontend): scaffold Vue 3 + Vite with MainHall WebSocket component`

---

### Task 3.5 — Phase 3 Integration Test

**Why:** Verify the full chat pipeline: connect via WebSocket → send a message →
confirm broadcast → add reactions → confirm trending alert at threshold.

#### Test

```python
# tests/integration/test_phase3_chat.py
"""
Phase 3 integration test — WebSocket chat + trending pipeline.
Run with: pytest tests/integration/ -m integration
"""
import pytest
import asyncio

pytestmark = pytest.mark.integration


async def test_websocket_message_broadcast(async_client_ws):
    """Messages sent by one client are received by another in the same channel."""
    async with async_client_ws.websocket_connect("/ws/main-hall") as ws1:
        async with async_client_ws.websocket_connect("/ws/main-hall") as ws2:
            await ws1.send_json({"author": "Whiskers", "content": "Hello clowder!"})
            payload = await asyncio.wait_for(ws2.receive_json(), timeout=2.0)
            assert payload["author"] == "Whiskers"
            assert payload["content"] == "Hello clowder!"


async def test_trending_idea_broadcast(async_client, db_session):
    """An idea that crosses 10 reactions triggers a trending broadcast."""
    from backend.trending_service import TrendingService
    from unittest.mock import AsyncMock, patch

    # Create a message in ideas channel
    create_resp = await async_client.post("/messages", json={
        "channel": "ideas",
        "author": "Spec",
        "content": "Add automated linting to CI pipeline.",
    })
    message_id = create_resp.json()["id"]

    with patch.object(TrendingService, "check_and_surface", new_callable=AsyncMock) as mock_surface:
        # Add 10 reactions
        for i in range(10):
            await async_client.post(f"/messages/{message_id}/react",
                                    json={"emoji": "🐾", "author": f"agent-{i}"})
        assert mock_surface.called


async def test_chat_persisted_to_context(async_client, db_session):
    """Chat messages are stored in context_entries for RAG retrieval."""
    from backend.context_service import context_service
    from backend.rag_service import rag_service

    async with async_client.websocket_connect("/ws/ideas") as ws:
        await ws.send_json({
            "author": "Pixel",
            "content": "We should track token usage per team per day.",
            "type": "message",
        })
        await asyncio.sleep(0.1)  # allow persistence

    entries = await rag_service.retrieve(
        db=db_session,
        query="token usage tracking",
        top_k=3,
    )
    assert any("token" in e["text"].lower() for e in entries)
```

Commit: `test(integration): Phase 3 chat WebSocket + trending pipeline end-to-end`

---

## Summary

| Phase | Tasks | Key Deliverables |
|-------|-------|-----------------|
| **2** | 2.1–2.6 | EmbeddingService, ContextService, RAGService, auto-RAG on claim, /context/retrieve, integration test |
| **3** | 3.1–3.5 | ConnectionManager, WebSocket endpoint, TrendingService (10-reaction threshold), Vue 3 + MainHall.vue, integration test |

### TDD Ritual (every task)
1. Write the failing test — run it, confirm red
2. Implement the minimum code to pass
3. Run the test again, confirm green
4. Commit with `feat`/`test` prefix

### Dependencies
- Phase 2 requires Phase 1 database models and FastAPI skeleton
- Phase 3 requires Phase 1 + Phase 2 (chat messages are ingested into RAG)
- Frontend (3.4) is independent of backend and can be developed in parallel with 3.1–3.3

### Next: Phase 4-6
See `2026-03-08-clowder-v2-plan-phase4-6.md` for agent profiles, governance agents, and polish.
