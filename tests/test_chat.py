"""
tests/test_chat.py — WebSocket and chat persistence tests (Sprint 3)

These tests exercise:
  - The /ws/{room} WebSocket endpoint (ConnectionManager, missed-message replay)
  - The /api/channels/{channel}/messages REST endpoint (persist + read)
  - The MessageReaction ORM model

Requirements:
  - postgres-test container running on port 5433 (TEST_DATABASE_URL env var)
  - DATABASE_URL must be set to the test DB *before* backend.main is imported.
    The module sets os.environ["DATABASE_URL"] before the import so the
    SQLAlchemy engine is created against the test database.

Run:
    pytest tests/test_chat.py -v
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient

# ── Redirect the app's DB to the test database before importing main ───────────
# database.py reads DATABASE_URL at import time (module-level engine creation).
# We must set DATABASE_URL *before* `from backend.main import app` so the
# engine is bound to the test DB on port 5433.
_TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://clowder:clowder@localhost:5433/clowder_test",
)
# Force-set even if already set — we always want port 5433 in tests.
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["TESTING"] = "1"  # triggers NullPool in database.py → no event-loop binding

# Attempt to import the app; skip the whole module if the DB is unreachable or
# a hard dependency (e.g. asyncpg) is missing.
try:
    from backend.main import app  # noqa: E402 — must come after env-var setup
    _SKIP_REASON: str | None = None
except Exception as exc:  # pragma: no cover
    app = None  # type: ignore[assignment]
    _SKIP_REASON = f"backend.main could not be imported: {exc}"

# Decorator applied to every test that needs the app / DB
_needs_app = pytest.mark.skipif(
    _SKIP_REASON is not None,
    reason=_SKIP_REASON or "",
)

# ── Module-scoped TestClient ──────────────────────────────────────────────────
# A single TestClient (and its anyio portal + event loop) is shared across all
# tests in this module. This keeps the SQLAlchemy asyncpg connection pool on
# ONE event loop, avoiding the "Future attached to a different loop" error that
# occurs when multiple TestClient instances are created sequentially (each
# starts a fresh loop but inherits the same module-level engine).
#
# The client is entered as a context manager in a module-scoped fixture so
# that the lifespan (create_tables, init_embedding_service) runs once.

@pytest.fixture(scope="module")
def http_client():
    """Module-scoped TestClient — shares the asyncpg pool across all tests."""
    if app is None:
        pytest.skip(_SKIP_REASON)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── Helpers ───────────────────────────────────────────────────────────────────

def _unique() -> str:
    """Return a short unique string suitable for use in content / channel names."""
    return uuid.uuid4().hex[:8]


def _post_message(
    client: TestClient,
    channel: str,
    content: str,
    sender: str = "test-agent",
    msg_type: str = "chat",
    thread_id: str | None = None,
) -> dict:
    """POST a message via the REST API and return the response JSON."""
    payload: dict = {"content": content, "sender": sender, "type": msg_type}
    if thread_id is not None:
        payload["thread_id"] = thread_id
    resp = client.post(f"/api/channels/{channel}/messages", json=payload)
    resp.raise_for_status()
    return resp.json()


# ── Test 1: connect and receive history ───────────────────────────────────────

@_needs_app
def test_ws_connect_receives_history(http_client):
    """
    Connecting to /ws/<room> must not raise.

    The server sends each history message as a separate JSON frame on connect.
    For a brand-new channel there is no history, so the server immediately
    awaits client input. We send one message to unblock the receive loop and
    consume the echo — asserting we get a dict back without error.

    Asserts: receive_json() returns a dict (the echo of our sent message).
    """
    channel = f"hist-{_unique()}"

    with http_client.websocket_connect(f"/ws/{channel}") as ws:
        ws.send_json({"sender": "probe", "content": "ping", "type": "chat"})
        data = ws.receive_json()

    assert isinstance(data, dict), f"Expected dict, got {type(data)}: {data}"


# ── Test 2: send a message and receive it back (broadcast echo) ───────────────

@_needs_app
def test_ws_message_broadcast(http_client):
    """
    After connecting to a room and sending a message, the same client receives
    the broadcast echo with the correct content.

    The server broadcasts to ALL connections in the room including the sender,
    so a single-client test is sufficient to verify broadcast is working.

    Asserts: received["content"] == the content we sent.
    """
    channel = f"bc-{_unique()}"
    content = f"hello from A {_unique()}"

    with http_client.websocket_connect(f"/ws/{channel}") as ws:
        ws.send_json({"sender": "agent-a", "content": content, "type": "chat"})
        received = ws.receive_json()

    assert received.get("content") == content, (
        f"Expected content={content!r}, got {received!r}"
    )


# ── Test 3: message persists to DB (verified via REST GET) ────────────────────

@_needs_app
def test_ws_message_persists_to_db(http_client):
    """
    After sending a message over WebSocket, the message is retrievable via
    GET /api/channels/{channel}/messages — confirming DB persistence.

    The broadcast echo confirms the server committed the message before
    broadcasting, so we can immediately query the REST endpoint.

    Asserts: unique content string appears in the REST response after WS send.
    """
    channel = f"persist-{_unique()}"
    unique_content = f"persist-check-{_unique()}"

    with http_client.websocket_connect(f"/ws/{channel}") as ws:
        ws.send_json({"sender": "agent-persist", "content": unique_content, "type": "chat"})
        # Consume the broadcast echo — the server commits before broadcasting
        ws.receive_json()

    resp = http_client.get(f"/api/channels/{channel}/messages")
    resp.raise_for_status()
    messages = resp.json()

    contents = [m["content"] for m in messages]
    assert unique_content in contents, (
        f"Unique content {unique_content!r} not found in persisted messages: {contents}"
    )


# ── Test 4: messages in different rooms are isolated ──────────────────────────

@_needs_app
def test_ws_different_rooms_isolated(http_client):
    """
    A message sent to room-alpha must be stored with channel == 'room-alpha'.
    The broadcast response's channel field must match the room.
    room-beta must remain empty since we never sent anything there.

    Asserts:
      - received["channel"] == channel_alpha
      - GET channel_beta returns []
    """
    suffix = _unique()
    channel_alpha = f"room-alpha-{suffix}"
    channel_beta = f"room-beta-{suffix}"
    content_alpha = f"alpha-only-{_unique()}"

    with http_client.websocket_connect(f"/ws/{channel_alpha}") as ws:
        ws.send_json({"sender": "agent-alpha", "content": content_alpha, "type": "chat"})
        received = ws.receive_json()

    assert received.get("channel") == channel_alpha, (
        f"Expected channel={channel_alpha!r}, got {received.get('channel')!r}"
    )

    # Beta channel must be empty (we never sent anything there)
    resp = http_client.get(f"/api/channels/{channel_beta}/messages")
    resp.raise_for_status()
    assert resp.json() == [], (
        f"Expected empty beta channel, got: {resp.json()}"
    )


# ── Test 5: MessageReaction ORM model fields ──────────────────────────────────

@_needs_app
@pytest.mark.asyncio
async def test_post_reaction_creates_row_async(db_session):
    """
    Verify the MessageReaction ORM model works end-to-end by inserting a row
    via db_session and reading it back.

    Correct field names from models.py (NOT 'reactor' or 'emoji' as naively
    assumed — the actual column names are):
        message_id    — str, reference to a chat message id
        reactor_id    — str, the agent/user who reacted
        reaction_type — str, e.g. "heart", "thumbs_up"
        id            — int, autoincrement PK assigned by DB
        created_at    — datetime, server default

    Asserts: inserted row is retrievable with correct reactor_id and reaction_type.
    """
    from backend.models import MessageReaction
    from sqlalchemy import select

    fake_msg_id = _unique()
    reaction = MessageReaction(
        message_id=fake_msg_id,
        reactor_id="gemini-test",
        reaction_type="heart",
    )
    db_session.add(reaction)
    await db_session.commit()
    await db_session.refresh(reaction)

    assert reaction.id is not None, "DB must assign an autoincrement id"

    result = await db_session.execute(
        select(MessageReaction).where(MessageReaction.message_id == fake_msg_id)
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].reactor_id == "gemini-test"
    assert rows[0].reaction_type == "heart"


# ── Test 6: thread_id is stored and retrievable ───────────────────────────────

@_needs_app
def test_thread_reply_stored(http_client):
    """
    POST a parent message then a reply with thread_id set to the parent's id.
    GET the channel messages and assert the reply row has the correct thread_id.

    Uses only the REST API (no WS) to keep this test simple and free of
    WebSocket teardown complexity.

    Asserts: exactly one message in the channel has thread_id == parent id,
             and its content matches the reply content.
    """
    channel = f"threads-{_unique()}"

    # Create parent
    parent_resp = _post_message(http_client, channel, "parent message", sender="parent-agent")
    parent_id = parent_resp["id"]
    assert parent_id, "Parent message must return an id"

    # Create reply referencing the parent
    reply_content = f"reply-{_unique()}"
    _post_message(http_client, channel, reply_content, sender="reply-agent", thread_id=parent_id)

    # Read back
    resp = http_client.get(f"/api/channels/{channel}/messages")
    resp.raise_for_status()
    messages = resp.json()

    replies = [m for m in messages if m.get("thread_id") == parent_id]
    assert len(replies) == 1, (
        f"Expected 1 reply with thread_id={parent_id!r}, found: {replies}"
    )
    assert replies[0]["content"] == reply_content


# ── Test 7: broadcast response has the required JSON structure ────────────────

@_needs_app
def test_ws_send_and_receive_json_structure(http_client):
    """
    The dict broadcast back by the server after receiving a message must
    contain all required keys: id, sender, content, type, channel, timestamp.

    These keys are produced by backend.main._msg_dict(). This test validates
    that the full pipeline (WS receive → DB persist → broadcast) returns a
    well-formed message envelope.

    Asserts:
      - All of {id, sender, content, type, channel, timestamp} are present
      - Spot-check values match what we sent
    """
    channel = f"struct-{_unique()}"

    with http_client.websocket_connect(f"/ws/{channel}") as ws:
        ws.send_json({"sender": "tester", "content": "structure check", "type": "chat"})
        received = ws.receive_json()

    required_keys = {"id", "sender", "content", "type", "channel", "timestamp"}
    missing = required_keys - set(received.keys())
    assert not missing, (
        f"Response missing required keys {missing}. Full response: {received}"
    )
    assert received["sender"] == "tester"
    assert received["content"] == "structure check"
    assert received["type"] == "chat"
    assert received["channel"] == channel
    assert received["id"] is not None
    assert received["timestamp"] is not None
