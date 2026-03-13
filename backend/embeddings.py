"""
embeddings.py — Clowder v2 Embedding Service
Singleton wrapper around sentence-transformers.
Loaded once at API startup via FastAPI lifespan. Shared across all request handlers.
"""

from __future__ import annotations
from typing import Optional

_service: Optional["EmbeddingService"] = None


class EmbeddingService:
    """
    Wraps sentence-transformers SentenceTransformer.
    encode() is synchronous (the model is CPU-bound).
    Call from async handlers via asyncio.get_event_loop().run_in_executor() if needed,
    but for Phase 2 direct call is acceptable — model is fast for short texts.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimensions = 384  # all-MiniLM-L6-v2 output dims

    def encode(self, text: str) -> list[float]:
        """Encode text to a 384-dimensional embedding vector."""
        vector = self.model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple texts efficiently."""
        vectors = self.model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]


def init_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    """Called once from FastAPI lifespan. Stores singleton in module-level _service."""
    global _service
    _service = EmbeddingService(model_name)
    return _service


def get_embedding_service() -> EmbeddingService:
    """FastAPI dependency — returns the singleton. Raises if not initialized."""
    if _service is None:
        raise RuntimeError("EmbeddingService not initialized. Call init_embedding_service() at startup.")
    return _service
