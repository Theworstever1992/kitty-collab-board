"""
config.py — Kitty Collab Board v2
Settings for the online backend. All values from environment variables.
"""

import os
from pathlib import Path

# PostgreSQL connection
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://clowder:clowder@localhost:5432/clowder",
)

# Board directory (shared with FileBackend for sync)
BOARD_DIR: Path = Path(os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board"))

# v2 API
API_HOST: str = os.environ.get("CLOWDER_API_HOST", "0.0.0.0")
API_PORT: int = int(os.environ.get("CLOWDER_API_PORT", "9000"))

# RAG (Phase 2 — embedding model name)
EMBEDDING_MODEL: str = os.environ.get("CLOWDER_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
RAG_TOP_K: int = int(os.environ.get("CLOWDER_RAG_TOP_K", "5"))

# Debug
DEBUG: bool = os.environ.get("CLOWDER_DEBUG", "").lower() in ("1", "true", "yes")
