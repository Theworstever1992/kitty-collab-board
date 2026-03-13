
import asyncio
import importlib
import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# NullPool mode: must be set before backend.database is imported so the
# module-level engine is created without a connection pool. This prevents
# asyncpg connections from being bound to a specific event loop, which would
# cause "got Future attached to a different loop" errors when multiple test
# modules each create their own TestClient on different event loops.
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://clowder:clowder@localhost:5433/clowder_test")

# Import Base and models from backend
from backend.database import Base
import backend.models  # Ensures all models are registered on Base.metadata

# Test database URL — using the postgres-test service on port 5433
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://clowder:clowder@localhost:5433/clowder_test"
)

@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """
    Create a function-scoped engine. 
    Creates all tables at the start and drops them at the end.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        from sqlalchemy import text
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine

    # Clear data without dropping schema — preserves tables for any module-scoped
    # TestClient still running in the same pytest session.
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Function-scoped session factory.
    Rolls back every transaction after test completion to ensure isolation.
    """
    SessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with SessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture()
def board_dir(monkeypatch, tmp_path):
    """
    Override CLOWDER_BOARD_DIR and reload affected modules.
    """
    monkeypatch.setenv("CLOWDER_BOARD_DIR", str(tmp_path))
    import agents.atomic
    import agents.channels
    import agents.context_manager
    import agents.file_backend
    import agents.agent_client
    import backend.config
    
    for mod in [agents.atomic, agents.channels, agents.context_manager, agents.file_backend, agents.agent_client, backend.config]:
        importlib.reload(mod)
        
    return tmp_path
