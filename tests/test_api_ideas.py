import pytest
from backend.models import Idea, IdeaVote
from backend.api.ideas import (
    list_ideas,
    create_idea,
    get_idea,
    update_idea_status,
    vote_for_idea,
    delete_vote,
    CreateIdeaRequest,
    UpdateIdeaStatusRequest,
    VoteRequest
)
from fastapi import HTTPException

@pytest.fixture
def mock_session_local(db_session, monkeypatch):
    from backend.api import ideas
    class MockSession:
        async def __aenter__(self): return db_session
        async def __aexit__(self, *args): pass
    monkeypatch.setattr(ideas, "SessionLocal", MockSession)
    return db_session

@pytest.mark.asyncio
async def test_ideas_lifecycle(mock_session_local):
    # 1. Create
    req = CreateIdeaRequest(title="Test Idea", description="Desc")
    created = await create_idea(req)
    assert created["title"] == "Test Idea"
    idea_id = created["id"]

    # 2. Get
    fetched = await get_idea(idea_id)
    assert fetched["id"] == idea_id

    # 3. List
    ideas_list = await list_ideas()
    assert len(ideas_list) >= 1
    assert any(i["id"] == idea_id for i in ideas_list)

    # 4. Vote
    v_req = VoteRequest(voter_id="cat1")
    v_res = await vote_for_idea(idea_id, v_req)
    assert v_res["vote_count"] == 1

    # 5. Update status
    u_req = UpdateIdeaStatusRequest(status="approved", reviewed_by="manager")
    updated = await update_idea_status(idea_id, u_req)
    assert updated["status"] == "approved"

    # 6. Delete vote
    d_res = await delete_vote(idea_id, "cat1")
    assert d_res["vote_count"] == 0

@pytest.mark.asyncio
async def test_ideas_errors(mock_session_local):
    with pytest.raises(HTTPException) as exc:
        await get_idea(999)
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        await update_idea_status(999, UpdateIdeaStatusRequest(status="approved"))
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        await vote_for_idea(999, VoteRequest(voter_id="v"))
    assert exc.value.status_code == 404

    # Invalid status
    with pytest.raises(HTTPException) as exc:
        await update_idea_status(1, UpdateIdeaStatusRequest(status="invalid"))
    assert exc.value.status_code == 422
