"""
database.py — Kitty Collab Board v2
SQLAlchemy async engine + session factory.

Uses asyncpg driver for non-blocking PostgreSQL access.
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from backend.config import DATABASE_URL

# NullPool in test mode: each DB operation gets a fresh connection so the
# asyncpg pool is never bound to a specific event loop. This lets multiple
# test modules each create their own TestClient without "got Future attached
# to a different loop" errors.
_pool_kwargs = {"poolclass": NullPool} if os.environ.get("TESTING") else {"pool_pre_ping": True}

engine = create_async_engine(DATABASE_URL, echo=False, **_pool_kwargs)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def create_tables() -> None:
    """Create all tables. Called once from FastAPI lifespan."""
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for async database sessions."""
    async with SessionLocal() as session:
        yield session
