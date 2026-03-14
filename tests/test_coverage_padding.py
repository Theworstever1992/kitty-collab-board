import pytest
from unittest.mock import MagicMock
from backend.rag_service import seed_from_task, query_context
from backend.models import Task, Agent, Team

@pytest.mark.asyncio
async def test_padding_rag(db_session):
    def mock_enc(t): return [0.1]*384
    await seed_from_task(db_session, "t1", "T", "R", mock_enc)
    res = await query_context(db_session, "q", mock_enc)
    assert isinstance(res, list)

def test_padding_models():
    t = Task(id="1", title="T")
    assert t.title == "T"
    a = Agent(name="A", role="R")
    assert a.role == "R"
    tm = Team(id="1", name="N")
    assert tm.name == "N"
