"""
tests/test_profiles.py — Agent profile CRUD, avatar validation, and export/import (Sprint 4)

Tests exercise:
  - GET /api/v2/agents          — list agents
  - GET /api/v2/agents/{name}   — single agent full profile
  - PATCH /api/v2/agents/{name}/profile — update bio, skills, avatar_svg
  - GET /api/v2/agents/{name}/export?format=json — export profile as JSON
  - POST /api/v2/agents/import  — import an agent profile

Requirements:
  - postgres-test container on port 5433
  - DATABASE_URL must be set before backend.main is imported (done below)

Run:
    pytest tests/test_profiles.py -v
"""

import os
import uuid

# ── Point the app at the test database BEFORE any backend import ───────────────
_TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://clowder:clowder@localhost:5433/clowder_test",
)
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ["TESTING"] = "1"  # triggers NullPool in database.py → no event-loop binding

# Attempt to import the app; skip the whole module if unavailable.
try:
    from backend.main import app  # noqa: E402
    _SKIP_REASON: str | None = None
except Exception as exc:
    app = None  # type: ignore[assignment]
    _SKIP_REASON = f"backend.main could not be imported: {exc}"

import pytest
from fastapi.testclient import TestClient

_needs_app = pytest.mark.skipif(
    _SKIP_REASON is not None,
    reason=_SKIP_REASON or "",
)


# ── Module-scoped TestClient ──────────────────────────────────────────────────
# Shared across all tests: keeps the asyncpg pool on ONE event loop.

@pytest.fixture(scope="module")
def client():
    """Module-scoped TestClient — shares the asyncpg pool across all tests."""
    if app is None:
        pytest.skip(_SKIP_REASON)
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ── Helpers ───────────────────────────────────────────────────────────────────

def _uid() -> str:
    """Short unique suffix to avoid cross-test name collisions."""
    return uuid.uuid4().hex[:8]


def _register(client: TestClient, name: str, role: str = "tester") -> None:
    """Register an agent via the existing REST endpoint."""
    resp = client.post(
        "/api/agents/register",
        json={"name": name, "role": role, "model": "test-model"},
    )
    assert resp.status_code == 200, f"Register failed: {resp.text}"


# ── Test 1: profile CRUD (bio + skills) ──────────────────────────────────────

@_needs_app
def test_profile_crud(client):
    """
    Register an agent, PATCH bio + skills, then GET profile and assert both
    fields are present in the response.
    """
    name = f"agent-crud-{_uid()}"
    _register(client, name)

    patch_resp = client.patch(
        f"/api/v2/agents/{name}/profile",
        json={"bio": "I build things.", "skills": ["python", "testing"]},
    )
    assert patch_resp.status_code == 200, f"PATCH failed: {patch_resp.text}"

    get_resp = client.get(f"/api/v2/agents/{name}")
    assert get_resp.status_code == 200, f"GET failed: {get_resp.text}"
    data = get_resp.json()

    assert data["bio"] == "I build things.", f"bio mismatch: {data}"
    assert "python" in data["skills"], f"skills mismatch: {data}"
    assert "testing" in data["skills"], f"skills mismatch: {data}"


# ── Test 2: valid SVG avatar is accepted ─────────────────────────────────────

@_needs_app
def test_avatar_upload_valid_svg(client):
    """
    PATCH profile with a minimal but well-formed SVG string.
    Expect HTTP 200.
    """
    name = f"agent-svg-valid-{_uid()}"
    _register(client, name)

    valid_svg = '<svg xmlns="http://www.w3.org/2000/svg"><circle r="10"/></svg>'
    resp = client.patch(
        f"/api/v2/agents/{name}/profile",
        json={"avatar_svg": valid_svg},
    )
    assert resp.status_code == 200, f"Expected 200 for valid SVG, got {resp.status_code}: {resp.text}"


# ── Test 3: malformed XML is rejected ────────────────────────────────────────

@_needs_app
def test_avatar_rejection_malformed(client):
    """
    PATCH profile with non-XML garbage.
    Expect HTTP 422 (validation error).
    """
    name = f"agent-svg-bad-{_uid()}"
    _register(client, name)

    resp = client.patch(
        f"/api/v2/agents/{name}/profile",
        json={"avatar_svg": "not xml at all <<<"},
    )
    assert resp.status_code == 422, (
        f"Expected 422 for malformed XML, got {resp.status_code}: {resp.text}"
    )


# ── Test 4: SVG exceeding 50KB is rejected ───────────────────────────────────

@_needs_app
def test_avatar_rejection_too_large(client):
    """
    PATCH profile with a syntactically valid but oversized SVG (> 50KB).
    Expect HTTP 422.
    """
    name = f"agent-svg-big-{_uid()}"
    _register(client, name)

    # 60 000 'x' chars + a minimal SVG wrapper pushes well over 50KB.
    oversized_svg = "<svg>" + "x" * 60_000 + "</svg>"
    resp = client.patch(
        f"/api/v2/agents/{name}/profile",
        json={"avatar_svg": oversized_svg},
    )
    assert resp.status_code == 422, (
        f"Expected 422 for oversized avatar, got {resp.status_code}: {resp.text}"
    )


# ── Test 5: non-SVG root element is rejected ─────────────────────────────────

@_needs_app
def test_avatar_not_svg_root(client):
    """
    PATCH profile with well-formed XML whose root element is <html>, not <svg>.
    Expect HTTP 422.
    """
    name = f"agent-svg-html-{_uid()}"
    _register(client, name)

    resp = client.patch(
        f"/api/v2/agents/{name}/profile",
        json={"avatar_svg": "<html><body/></html>"},
    )
    assert resp.status_code == 422, (
        f"Expected 422 for non-svg root, got {resp.status_code}: {resp.text}"
    )


# ── Test 6: JSON export contains required keys ───────────────────────────────

@_needs_app
def test_export_json(client):
    """
    Register an agent, set bio and skills, export as JSON.
    Assert the response is a JSON object containing:
        name, role, bio, skills, exported_at
    """
    name = f"agent-export-{_uid()}"
    _register(client, name, role="exporter")

    # Set profile fields first
    client.patch(
        f"/api/v2/agents/{name}/profile",
        json={"bio": "Exported agent bio.", "skills": ["export", "json"]},
    ).raise_for_status()

    export_resp = client.get(f"/api/v2/agents/{name}/export?format=json")
    assert export_resp.status_code == 200, f"Export failed: {export_resp.text}"

    data = export_resp.json()
    required_keys = {"name", "role", "bio", "skills", "exported_at"}
    missing = required_keys - set(data.keys())
    assert not missing, f"Export JSON missing keys {missing}. Got: {list(data.keys())}"

    assert data["name"] == name
    assert data["role"] == "exporter"
    assert data["bio"] == "Exported agent bio."
    assert "export" in data["skills"]
    assert data["exported_at"]  # must be a non-empty string


# ── Test 7: import round-trip ─────────────────────────────────────────────────

@_needs_app
def test_import_round_trip(client):
    """
    Export an agent as JSON, rename it, POST to /api/v2/agents/import.
    Assert:
        - POST returns 200 with {"imported": True}
        - GET profile of the new agent returns the same bio as the original
    """
    # Step 1: create source agent and set its profile
    src_name = f"agent-src-{_uid()}"
    _register(client, src_name, role="source-role")
    original_bio = f"Round-trip bio {_uid()}"
    client.patch(
        f"/api/v2/agents/{src_name}/profile",
        json={"bio": original_bio, "skills": ["roundtrip"]},
    ).raise_for_status()

    # Step 2: export source agent
    export_resp = client.get(f"/api/v2/agents/{src_name}/export?format=json")
    export_resp.raise_for_status()
    export_data = export_resp.json()

    # Step 3: change name and import
    new_name = f"{src_name}-imported"
    export_data["name"] = new_name

    import_resp = client.post("/api/v2/agents/import", json=export_data)
    assert import_resp.status_code == 200, f"Import failed: {import_resp.text}"
    import_body = import_resp.json()
    assert import_body.get("imported") is True, f"Expected imported=True, got: {import_body}"

    # Step 4: verify the new agent's profile
    get_resp = client.get(f"/api/v2/agents/{new_name}")
    assert get_resp.status_code == 200, f"GET new agent failed: {get_resp.text}"
    profile = get_resp.json()
    assert profile["bio"] == original_bio, (
        f"bio mismatch after import: expected {original_bio!r}, got {profile.get('bio')!r}"
    )
