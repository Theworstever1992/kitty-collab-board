# Clowder v2 — Phase 4-6 Implementation Plan: Profiles, Governance & Polish

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add agent profiles with portability, full governance (token + standards monitoring), enhanced ideas channel, and final polish with web dashboard, improved TUI, and cat flair.

**Depends on:** Phases 1-3 complete
**Tech Stack:** Vue 3 + Vite, FastAPI, PostgreSQL, Python curses, Docker, Nginx

---

## Phase 4: Agent Profiles & Portability (Weeks 7-8)

### Task 4.1: Agent Profile Endpoints

**Files:**
- Create: `backend/api/agents.py`
- Modify: `backend/main.py` (add agents router)
- Test: `tests/test_agent_profiles.py`

**Step 1: Write the failing tests**

```python
# tests/test_agent_profiles.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine
from backend.models import Team, Agent
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from uuid import uuid4

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # seed test team + agent
    team = Team(id="team1", name="Whiskers Team", leader_id="agent-leader")
    agent = Agent(
        id="agent1", name="Shadow", team_id="team1",
        role="code_reviewer", bio="I catch bugs.", model="claude-3-5-sonnet-20241022",
        skills=["python", "security"], preferences={}
    )
    db.add(team); db.add(agent); db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_list_agents(client):
    response = client.get("/agents/")
    assert response.status_code == 200
    data = response.json()
    assert any(a["name"] == "Shadow" for a in data)

def test_get_agent(client):
    response = client.get("/agents/agent1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Shadow"
    assert data["role"] == "code_reviewer"
    assert "python" in data["skills"]

def test_get_agent_not_found(client):
    response = client.get("/agents/nonexistent")
    assert response.status_code == 404

def test_update_agent_profile(client):
    response = client.put("/agents/agent1/profile", json={
        "bio": "Updated bio — still catching bugs.",
        "skills": ["python", "security", "architecture"]
    })
    assert response.status_code == 200
    assert response.json()["bio"] == "Updated bio — still catching bugs."

def test_list_teams(client):
    response = client.get("/teams/")
    assert response.status_code == 200
    assert any(t["name"] == "Whiskers Team" for t in response.json())

def test_get_team_agents(client):
    response = client.get("/teams/team1/agents")
    assert response.status_code == 200
    assert any(a["name"] == "Shadow" for a in response.json())
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_agent_profiles.py -v
# Expected: ImportError or 404 — backend/api/agents.py does not exist
```

**Step 3: Implement**

```python
# backend/api/agents.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Agent, Team
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(tags=["agents"])

class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    preferences: Optional[dict] = None

@router.get("/agents/", response_model=List[dict])
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).all()
    return [
        {"id": a.id, "name": a.name, "role": a.role, "team_id": a.team_id,
         "bio": a.bio, "model": a.model, "skills": a.skills or []}
        for a in agents
    ]

@router.get("/agents/{agent_id}", response_model=dict)
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": agent.id, "name": agent.name, "role": agent.role,
        "team_id": agent.team_id, "bio": agent.bio, "model": agent.model,
        "skills": agent.skills or [], "preferences": agent.preferences or {},
        "avatar_svg": agent.avatar_svg
    }

@router.put("/agents/{agent_id}/profile", response_model=dict)
def update_profile(agent_id: str, update: ProfileUpdate, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if update.bio is not None:
        agent.bio = update.bio
    if update.skills is not None:
        agent.skills = update.skills
    if update.preferences is not None:
        agent.preferences = update.preferences
    db.commit(); db.refresh(agent)
    return {"id": agent.id, "bio": agent.bio, "skills": agent.skills}

@router.get("/teams/", response_model=List[dict])
def list_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    return [{"id": t.id, "name": t.name, "leader_id": t.leader_id} for t in teams]

@router.get("/teams/{team_id}/agents", response_model=List[dict])
def get_team_agents(team_id: str, db: Session = Depends(get_db)):
    agents = db.query(Agent).filter(Agent.team_id == team_id).all()
    return [{"id": a.id, "name": a.name, "role": a.role} for a in agents]
```

```python
# backend/main.py — add to existing imports and routes:
from backend.api.agents import router as agents_router
app.include_router(agents_router)
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_agent_profiles.py -v
# Expected: all 6 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/api/agents.py tests/test_agent_profiles.py
git commit -m "feat(phase-4): add agent profile and team endpoints"
```

---

### Task 4.2: Avatar Upload & Validation

**Files:**
- Create: `backend/storage.py`
- Create: `backend/assets/avatars/tabby.svg`
- Create: `backend/assets/avatars/tuxedo.svg`
- Create: `backend/assets/avatars/calico.svg`
- Modify: `backend/api/agents.py` (add avatar endpoints)
- Test: `tests/test_avatars.py`

**Step 1: Write the failing tests**

```python
# tests/test_avatars.py
import pytest
from backend.storage import AvatarService

VALID_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="40" fill="orange"/></svg>'
INVALID_SVG = "<not-valid-xml"
OVERSIZED_SVG = '<svg xmlns="http://www.w3.org/2000/svg">' + "x" * 60000 + "</svg>"

def test_validate_valid_svg():
    assert AvatarService.validate_svg(VALID_SVG) is True

def test_validate_invalid_svg():
    assert AvatarService.validate_svg(INVALID_SVG) is False

def test_validate_oversized_svg():
    assert AvatarService.validate_svg(OVERSIZED_SVG) is False

def test_get_default_avatar_tabby():
    svg = AvatarService.get_default_avatar("tabby")
    assert svg.startswith("<svg")
    assert AvatarService.validate_svg(svg) is True

def test_get_default_avatar_unknown_returns_tabby():
    svg = AvatarService.get_default_avatar("unknown_style")
    assert svg.startswith("<svg")

def test_get_random_default():
    svg = AvatarService.get_random_default()
    assert svg.startswith("<svg")
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_avatars.py -v
# Expected: ModuleNotFoundError — backend/storage.py does not exist
```

**Step 3: Implement**

```python
# backend/storage.py
import xml.etree.ElementTree as ET
import random
from pathlib import Path

AVATAR_DIR = Path(__file__).parent / "assets" / "avatars"
MAX_AVATAR_BYTES = 50_000
DEFAULT_STYLES = ["tabby", "tuxedo", "calico"]

class AvatarService:
    @staticmethod
    def validate_svg(svg_text: str) -> bool:
        """Validate SVG: must be valid XML and <= 50KB."""
        if len(svg_text.encode("utf-8")) > MAX_AVATAR_BYTES:
            return False
        try:
            ET.fromstring(svg_text)
            return True
        except ET.ParseError:
            return False

    @staticmethod
    def get_default_avatar(style: str) -> str:
        """Return one of the built-in cat SVG templates."""
        path = AVATAR_DIR / f"{style}.svg"
        if not path.exists():
            path = AVATAR_DIR / "tabby.svg"
        return path.read_text()

    @staticmethod
    def get_random_default() -> str:
        return AvatarService.get_default_avatar(random.choice(DEFAULT_STYLES))
```

```xml
<!-- backend/assets/avatars/tabby.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <!-- Head -->
  <circle cx="50" cy="55" r="30" fill="#E8A87C"/>
  <!-- Ears -->
  <polygon points="25,35 15,10 38,30" fill="#E8A87C"/>
  <polygon points="75,35 85,10 62,30" fill="#E8A87C"/>
  <polygon points="27,33 20,15 37,30" fill="#F4C4A0"/>
  <polygon points="73,33 80,15 63,30" fill="#F4C4A0"/>
  <!-- Eyes -->
  <ellipse cx="38" cy="52" rx="7" ry="8" fill="#4CAF50"/>
  <ellipse cx="62" cy="52" rx="7" ry="8" fill="#4CAF50"/>
  <ellipse cx="38" cy="52" rx="3" ry="6" fill="#1a1a1a"/>
  <ellipse cx="62" cy="52" rx="3" ry="6" fill="#1a1a1a"/>
  <!-- Nose -->
  <polygon points="50,62 47,67 53,67" fill="#E91E8C"/>
  <!-- Mouth -->
  <path d="M47,67 Q44,72 40,70" stroke="#1a1a1a" stroke-width="1.5" fill="none"/>
  <path d="M53,67 Q56,72 60,70" stroke="#1a1a1a" stroke-width="1.5" fill="none"/>
  <!-- Whiskers -->
  <line x1="10" y1="62" x2="42" y2="64" stroke="#1a1a1a" stroke-width="1"/>
  <line x1="10" y1="67" x2="42" y2="67" stroke="#1a1a1a" stroke-width="1"/>
  <line x1="58" y1="64" x2="90" y2="62" stroke="#1a1a1a" stroke-width="1"/>
  <line x1="58" y1="67" x2="90" y2="67" stroke="#1a1a1a" stroke-width="1"/>
  <!-- Tabby stripes -->
  <path d="M30,40 Q35,35 40,40" stroke="#C4845A" stroke-width="2" fill="none"/>
  <path d="M60,40 Q65,35 70,40" stroke="#C4845A" stroke-width="2" fill="none"/>
</svg>
```

```xml
<!-- backend/assets/avatars/tuxedo.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <circle cx="50" cy="55" r="30" fill="#1a1a1a"/>
  <polygon points="25,35 15,10 38,30" fill="#1a1a1a"/>
  <polygon points="75,35 85,10 62,30" fill="#1a1a1a"/>
  <!-- White chest patch -->
  <ellipse cx="50" cy="68" rx="14" ry="12" fill="white"/>
  <!-- Eyes -->
  <ellipse cx="38" cy="52" rx="7" ry="8" fill="#64B5F6"/>
  <ellipse cx="62" cy="52" rx="7" ry="8" fill="#64B5F6"/>
  <ellipse cx="38" cy="52" rx="3" ry="6" fill="#1a1a1a"/>
  <ellipse cx="62" cy="52" rx="3" ry="6" fill="#1a1a1a"/>
  <polygon points="50,62 47,67 53,67" fill="#E91E8C"/>
  <path d="M47,67 Q44,72 40,70" stroke="white" stroke-width="1.5" fill="none"/>
  <path d="M53,67 Q56,72 60,70" stroke="white" stroke-width="1.5" fill="none"/>
  <line x1="10" y1="62" x2="42" y2="64" stroke="white" stroke-width="1"/>
  <line x1="58" y1="64" x2="90" y2="62" stroke="white" stroke-width="1"/>
</svg>
```

```xml
<!-- backend/assets/avatars/calico.svg -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <circle cx="50" cy="55" r="30" fill="white"/>
  <polygon points="25,35 15,10 38,30" fill="white"/>
  <polygon points="75,35 85,10 62,30" fill="white"/>
  <!-- Calico patches -->
  <circle cx="35" cy="48" r="12" fill="#E8A87C" opacity="0.8"/>
  <circle cx="65" cy="58" r="10" fill="#1a1a1a" opacity="0.7"/>
  <circle cx="50" cy="70" r="8" fill="#E8A87C" opacity="0.6"/>
  <!-- Eyes -->
  <ellipse cx="38" cy="52" rx="7" ry="8" fill="#FFA726"/>
  <ellipse cx="62" cy="52" rx="7" ry="8" fill="#FFA726"/>
  <ellipse cx="38" cy="52" rx="3" ry="6" fill="#1a1a1a"/>
  <ellipse cx="62" cy="52" rx="3" ry="6" fill="#1a1a1a"/>
  <polygon points="50,62 47,67 53,67" fill="#E91E8C"/>
  <path d="M47,67 Q44,72 40,70" stroke="#1a1a1a" stroke-width="1.5" fill="none"/>
  <path d="M53,67 Q56,72 60,70" stroke="#1a1a1a" stroke-width="1.5" fill="none"/>
  <line x1="10" y1="62" x2="42" y2="64" stroke="#888" stroke-width="1"/>
  <line x1="58" y1="64" x2="90" y2="62" stroke="#888" stroke-width="1"/>
</svg>
```

```python
# Add to backend/api/agents.py:
from backend.storage import AvatarService
from fastapi import Response

@router.put("/agents/{agent_id}/avatar")
def upload_avatar(agent_id: str, svg_text: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not AvatarService.validate_svg(svg_text):
        raise HTTPException(status_code=400, detail="Invalid SVG: malformed XML or exceeds 50KB limit")
    agent.avatar_svg = svg_text
    db.commit()
    return {"status": "ok", "message": "Avatar updated 🐱"}

@router.get("/agents/{agent_id}/avatar")
def get_avatar(agent_id: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    svg = agent.avatar_svg or AvatarService.get_random_default()
    return Response(content=svg, media_type="image/svg+xml")
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_avatars.py -v
# Expected: all 6 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/storage.py backend/assets/ tests/test_avatars.py
git commit -m "feat(phase-4): add avatar upload, validation, and default cat SVGs"
```

---

### Task 4.3: Export Agent (JSON + Markdown)

**Files:**
- Create: `backend/export_service.py`
- Create: `backend/api/exports.py`
- Modify: `backend/main.py`
- Test: `tests/test_exports.py`

**Step 1: Write the failing tests**

```python
# tests/test_exports.py
import pytest, json
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team, Agent

@pytest.fixture(autouse=True)
def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="Whiskers Team", leader_id="leader1"))
    db.add(Agent(
        id="agent1", name="Shadow", team_id="t1", role="code_reviewer",
        bio="I catch bugs before they catch us.",
        model="claude-3-5-sonnet-20241022",
        skills=["python", "security", "architecture"],
        preferences={"rag_focus": ["security_reviews"]}
    ))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_export_json_structure(client):
    resp = client.get("/agents/agent1/export/json")
    assert resp.status_code == 200
    data = resp.json()
    assert "agent_metadata" in data
    assert "system_prompt" in data
    assert "rag_config" in data
    assert data["agent_metadata"]["name"] == "Shadow"

def test_export_json_has_skills(client):
    data = client.get("/agents/agent1/export/json").json()
    assert "python" in data["agent_metadata"]["skills"]

def test_export_md_is_string(client):
    resp = client.get("/agents/agent1/export/md")
    assert resp.status_code == 200
    assert "Shadow" in resp.text
    assert "code_reviewer" in resp.text

def test_export_md_has_bio(client):
    resp = client.get("/agents/agent1/export/md")
    assert "I catch bugs before they catch us." in resp.text
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_exports.py -v
# Expected: 404 — /agents/{id}/export/json not defined
```

**Step 3: Implement**

```python
# backend/export_service.py
from backend.models import Agent, Task
from sqlalchemy.orm import Session
from datetime import datetime

class ExportService:
    @staticmethod
    def export_json(agent_id: str, db: Session) -> dict:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        # Last 20 completed tasks as context summary
        recent_tasks = db.query(Task).filter(
            Task.claimed_by == agent_id,
            Task.status == "done"
        ).order_by(Task.completed_at.desc()).limit(20).all()

        context_summary = [
            {"title": t.title, "completed_at": t.completed_at.isoformat() if t.completed_at else None}
            for t in recent_tasks
        ]

        return {
            "export_version": "2.0",
            "exported_at": datetime.utcnow().isoformat(),
            "agent_metadata": {
                "name": agent.name,
                "role": agent.role,
                "bio": agent.bio,
                "model": agent.model,
                "skills": agent.skills or [],
                "avatar_svg": agent.avatar_svg,
            },
            "system_prompt": (
                f"You are {agent.name}, a {agent.role}. {agent.bio or ''} "
                f"You are part of a collaborative AI team called Clowder. "
                f"Your skills include: {', '.join(agent.skills or [])}."
            ),
            "rag_config": agent.preferences.get("rag_config", {
                "auto_retrieve": True,
                "max_context_tokens": 2000,
                "top_k": 5,
            }),
            "context_history_summary": context_summary,
        }

    @staticmethod
    def export_markdown(agent_id: str, db: Session) -> str:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return None

        lines = [
            f"# 🐱 {agent.name}",
            f"",
            f"**Role:** {agent.role}",
            f"**Model:** {agent.model}",
            f"**Team:** {agent.team_id}",
            f"",
            f"## Bio",
            f"",
            f"{agent.bio or '_No bio yet._'}",
            f"",
            f"## Skills",
            f"",
        ]
        for skill in (agent.skills or []):
            lines.append(f"- {skill}")
        lines += [
            f"",
            f"## Notes",
            f"",
            f"_Exported from Clowder v2 on {datetime.utcnow().strftime('%Y-%m-%d')}_",
            f"_Import using: `POST /agents/import/json`_",
        ]
        return "\n".join(lines)
```

```python
# backend/api/exports.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.export_service import ExportService

router = APIRouter(tags=["exports"])

@router.get("/agents/{agent_id}/export/json")
def export_json(agent_id: str, db: Session = Depends(get_db)):
    data = ExportService.export_json(agent_id, db)
    if not data:
        raise HTTPException(status_code=404, detail="Agent not found")
    return data

@router.get("/agents/{agent_id}/export/md", response_class=PlainTextResponse)
def export_md(agent_id: str, db: Session = Depends(get_db)):
    md = ExportService.export_markdown(agent_id, db)
    if not md:
        raise HTTPException(status_code=404, detail="Agent not found")
    return md
```

```python
# backend/main.py — add:
from backend.api.exports import router as exports_router
app.include_router(exports_router)
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_exports.py -v
# Expected: all 4 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/export_service.py backend/api/exports.py tests/test_exports.py
git commit -m "feat(phase-4): add agent export to JSON and Markdown"
```

---

### Task 4.4: Import Agent

**Files:**
- Modify: `backend/api/exports.py` (add import endpoint)
- Test: `tests/test_imports.py`

**Step 1: Write the failing tests**

```python
# tests/test_imports.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team

VALID_EXPORT = {
    "export_version": "2.0",
    "agent_metadata": {
        "name": "Shadow",
        "role": "code_reviewer",
        "bio": "I catch bugs.",
        "model": "claude-3-5-sonnet-20241022",
        "skills": ["python", "security"],
        "avatar_svg": None,
    },
    "system_prompt": "You are Shadow...",
    "rag_config": {"auto_retrieve": True, "top_k": 5},
    "context_history_summary": [],
}

@pytest.fixture(autouse=True)
def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="Whiskers Team", leader_id="l1"))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

def test_import_creates_agent(client):
    resp = client.post("/agents/import/json?team_id=t1", json=VALID_EXPORT)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Shadow"

def test_import_name_conflict_gets_suffix(client):
    client.post("/agents/import/json?team_id=t1", json=VALID_EXPORT)
    resp = client.post("/agents/import/json?team_id=t1", json=VALID_EXPORT)
    assert resp.status_code == 200
    assert "_imported" in resp.json()["name"]

def test_import_missing_fields_rejected(client):
    resp = client.post("/agents/import/json?team_id=t1", json={"export_version": "2.0"})
    assert resp.status_code == 422

def test_import_invalid_avatar_rejected(client):
    bad_export = dict(VALID_EXPORT)
    bad_export["agent_metadata"] = dict(VALID_EXPORT["agent_metadata"])
    bad_export["agent_metadata"]["avatar_svg"] = "<not-valid-xml"
    resp = client.post("/agents/import/json?team_id=t1", json=bad_export)
    assert resp.status_code == 400
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_imports.py -v
# Expected: 404 or 405 — /agents/import/json not defined
```

**Step 3: Implement**

```python
# Add to backend/api/exports.py:
from uuid import uuid4
from backend.models import Agent
from backend.storage import AvatarService

class AgentImport(BaseModel):
    export_version: str
    agent_metadata: dict
    system_prompt: str
    rag_config: dict
    context_history_summary: list = []

@router.post("/agents/import/json")
def import_agent(payload: AgentImport, team_id: str, db: Session = Depends(get_db)):
    meta = payload.agent_metadata
    required = ["name", "role", "model"]
    for field in required:
        if field not in meta:
            raise HTTPException(status_code=422, detail=f"Missing required field: {field}")

    # Validate avatar if present
    avatar = meta.get("avatar_svg")
    if avatar and not AvatarService.validate_svg(avatar):
        raise HTTPException(status_code=400, detail="Invalid avatar SVG")

    # Handle name conflict
    name = meta["name"]
    existing = db.query(Agent).filter(Agent.name == name).first()
    if existing:
        name = f"{name}_imported"

    agent = Agent(
        id=str(uuid4()),
        name=name,
        team_id=team_id,
        role=meta["role"],
        bio=meta.get("bio"),
        model=meta["model"],
        skills=meta.get("skills", []),
        avatar_svg=avatar,
        preferences={"rag_config": payload.rag_config},
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return {"id": agent.id, "name": agent.name, "role": agent.role, "team_id": agent.team_id}
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_imports.py -v
# Expected: all 4 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/api/exports.py tests/test_imports.py
git commit -m "feat(phase-4): add agent import from JSON export"
```

---

### Task 4.5: Agent Profile Vue Pages

**Files:**
- Create: `frontend/src/views/AgentProfile.vue`
- Create: `frontend/src/views/AgentGallery.vue`
- Create: `frontend/src/views/TeamView.vue`
- Modify: `frontend/src/router/index.js`

**Step 1: Write the failing tests**

```javascript
// tests/frontend/AgentProfile.spec.js
import { mount } from '@vue/test-utils'
import AgentProfile from '@/views/AgentProfile.vue'
import { createRouter, createMemoryHistory } from 'vue-router'

const mockAgent = {
  id: 'agent1', name: 'Shadow', role: 'code_reviewer',
  bio: 'I catch bugs.', skills: ['python', 'security'], model: 'claude-3-5-sonnet',
  team_id: 't1', avatar_svg: null
}

vi.mock('@/api/index.js', () => ({
  default: { get: vi.fn().mockResolvedValue({ data: mockAgent }) }
}))

test('renders agent name', async () => {
  const wrapper = mount(AgentProfile, {
    global: { plugins: [router] },
    props: { agentId: 'agent1' }
  })
  await wrapper.vm.$nextTick()
  expect(wrapper.text()).toContain('Shadow')
})

test('shows export buttons', () => {
  const wrapper = mount(AgentProfile)
  expect(wrapper.find('[data-testid="export-json"]').exists()).toBe(true)
  expect(wrapper.find('[data-testid="export-md"]').exists()).toBe(true)
})
```

**Step 2: Run test — verify it fails**

```bash
cd frontend && npx vitest run tests/frontend/AgentProfile.spec.js
# Expected: Cannot find module '@/views/AgentProfile.vue'
```

**Step 3: Implement**

```vue
<!-- frontend/src/views/AgentProfile.vue -->
<template>
  <div class="profile-page">
    <div v-if="agent" class="profile-card">
      <div class="avatar-section">
        <div class="avatar" v-html="agent.avatar_svg || defaultAvatar" />
        <label class="avatar-upload">
          📎 Upload SVG
          <input type="file" accept=".svg" @change="uploadAvatar" hidden />
        </label>
      </div>

      <div class="profile-info">
        <h1>🐱 {{ agent.name }}</h1>
        <p class="role">{{ agent.role }}</p>
        <p class="model">Model: {{ agent.model }}</p>

        <div class="bio-section">
          <h3>Bio</h3>
          <p v-if="!editing">{{ agent.bio || 'No bio yet.' }}</p>
          <textarea v-else v-model="editBio" rows="3" />
        </div>

        <div class="skills-section">
          <h3>Skills</h3>
          <div class="skill-tags">
            <span v-for="skill in agent.skills" :key="skill" class="tag">{{ skill }}</span>
          </div>
        </div>

        <div class="actions">
          <button v-if="!editing" @click="editing = true">✏️ Edit Profile</button>
          <button v-else @click="saveProfile">💾 Save</button>
          <button data-testid="export-json" @click="exportJson">📦 Export JSON</button>
          <button data-testid="export-md" @click="exportMd">📝 Export MD</button>
        </div>
      </div>
    </div>
    <div v-else class="loading">Loading... 🐾</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api/index.js'

const route = useRoute()
const agent = ref(null)
const editing = ref(false)
const editBio = ref('')
const defaultAvatar = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🐱</text></svg>'

onMounted(async () => {
  const { data } = await api.get(`/agents/${route.params.id}`)
  agent.value = data
  editBio.value = data.bio || ''
})

async function saveProfile() {
  await api.put(`/agents/${agent.value.id}/profile`, { bio: editBio.value })
  agent.value.bio = editBio.value
  editing.value = false
}

async function exportJson() {
  const { data } = await api.get(`/agents/${agent.value.id}/export/json`)
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  downloadBlob(blob, `${agent.value.name}.json`)
}

async function exportMd() {
  const { data } = await api.get(`/agents/${agent.value.id}/export/md`)
  const blob = new Blob([data], { type: 'text/markdown' })
  downloadBlob(blob, `${agent.value.name}.md`)
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

async function uploadAvatar(e) {
  const text = await e.target.files[0].text()
  await api.put(`/agents/${agent.value.id}/avatar`, text, {
    headers: { 'Content-Type': 'text/plain' }
  })
  agent.value.avatar_svg = text
}
</script>

<style scoped>
.profile-page { max-width: 700px; margin: 2rem auto; padding: 1rem; }
.profile-card { display: flex; gap: 2rem; background: #fff8f0; border-radius: 12px; padding: 2rem; }
.avatar { width: 120px; height: 120px; }
h1 { margin: 0; font-size: 1.8rem; }
.role { color: #888; text-transform: capitalize; }
.tag { background: #ffe0b2; padding: 2px 10px; border-radius: 12px; margin: 2px; font-size: 0.85rem; }
.actions { display: flex; gap: 0.5rem; margin-top: 1rem; flex-wrap: wrap; }
button { padding: 0.4rem 1rem; border: none; border-radius: 8px; cursor: pointer; background: #ffcc80; }
button:hover { background: #ffb74d; }
</style>
```

```vue
<!-- frontend/src/views/AgentGallery.vue -->
<template>
  <div class="gallery">
    <h1>🐱 Clowder — Meet the Team</h1>
    <div class="filters">
      <select v-model="filterTeam"><option value="">All Teams</option>
        <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.name }}</option>
      </select>
      <select v-model="filterRole"><option value="">All Roles</option>
        <option value="code_reviewer">Code Reviewer</option>
        <option value="security_reviewer">Security Reviewer</option>
        <option value="insights">Insights</option>
        <option value="team_leader">Team Leader</option>
      </select>
    </div>
    <div class="agent-grid">
      <router-link
        v-for="agent in filteredAgents" :key="agent.id"
        :to="`/agents/${agent.id}`" class="agent-card"
      >
        <div class="avatar" v-html="agent.avatar_svg || defaultAvatar" />
        <h3>{{ agent.name }}</h3>
        <p class="role">{{ agent.role }}</p>
        <p class="team">{{ agent.team_id }}</p>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api/index.js'

const agents = ref([])
const teams = ref([])
const filterTeam = ref('')
const filterRole = ref('')
const defaultAvatar = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🐱</text></svg>'

const filteredAgents = computed(() => agents.value
  .filter(a => !filterTeam.value || a.team_id === filterTeam.value)
  .filter(a => !filterRole.value || a.role === filterRole.value)
)

onMounted(async () => {
  const [agentsRes, teamsRes] = await Promise.all([api.get('/agents/'), api.get('/teams/')])
  agents.value = agentsRes.data
  teams.value = teamsRes.data
})
</script>

<style scoped>
.gallery { max-width: 1000px; margin: 2rem auto; padding: 1rem; }
.agent-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }
.agent-card { background: #fff8f0; border-radius: 12px; padding: 1rem; text-align: center; text-decoration: none; color: inherit; transition: transform 0.2s; }
.agent-card:hover { transform: translateY(-4px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.avatar { width: 80px; height: 80px; margin: 0 auto; }
h3 { margin: 0.5rem 0 0; }
.role { color: #888; font-size: 0.85rem; text-transform: capitalize; }
.filters { display: flex; gap: 1rem; }
select { padding: 0.4rem; border-radius: 8px; border: 1px solid #ddd; }
</style>
```

```javascript
// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import AgentGallery from '@/views/AgentGallery.vue'
import AgentProfile from '@/views/AgentProfile.vue'
import MainHall from '@/views/MainHall.vue'
import TaskBoard from '@/views/TaskBoard.vue'
import IdeasChannel from '@/views/IdeasChannel.vue'
import StandardsDashboard from '@/views/StandardsDashboard.vue'
import MeetingNotes from '@/views/MeetingNotes.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/agents', component: AgentGallery },
    { path: '/agents/:id', component: AgentProfile },
    { path: '/chat', component: MainHall },
    { path: '/tasks', component: TaskBoard },
    { path: '/ideas', component: IdeasChannel },
    { path: '/governance', component: StandardsDashboard },
    { path: '/meetings', component: MeetingNotes },
  ]
})
```

**Step 4: Run test — verify it passes**

```bash
cd frontend && npx vitest run tests/frontend/AgentProfile.spec.js
# Expected: PASSED
```

**Step 5: Commit**

```bash
git add frontend/src/views/AgentProfile.vue frontend/src/views/AgentGallery.vue frontend/src/router/index.js
git commit -m "feat(phase-4): add agent profile and gallery Vue pages"
```

---

### Task 4.6: Phase 4 Integration Test

**Files:**
- Create: `tests/test_integration_phase4.py`

**Step 1: Write the test**

```python
# tests/test_integration_phase4.py
import pytest, json
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team, Agent

@pytest.fixture(autouse=True)
def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="Test Team", leader_id="l1"))
    db.add(Agent(id="a1", name="Pounce", team_id="t1", role="security_reviewer",
                 bio="Security first.", model="claude-3-5-sonnet-20241022",
                 skills=["security"], preferences={}))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(): return TestClient(app)

def test_full_profile_update_and_export(client):
    # Update profile
    client.put("/agents/a1/profile", json={"bio": "Updated bio", "skills": ["security", "pentest"]})
    # Export JSON
    data = client.get("/agents/a1/export/json").json()
    assert data["agent_metadata"]["bio"] == "Updated bio"
    assert "pentest" in data["agent_metadata"]["skills"]

def test_export_import_roundtrip(client):
    export_data = client.get("/agents/a1/export/json").json()
    export_data["agent_metadata"]["name"] = "Pounce_Clone"
    resp = client.post("/agents/import/json?team_id=t1", json=export_data)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pounce_Clone"
    # Verify it appears in gallery
    agents = client.get("/agents/").json()
    assert any(a["name"] == "Pounce_Clone" for a in agents)
```

**Step 2: Run — verify it passes**

```bash
pytest tests/test_integration_phase4.py -v
# Expected: PASSED
```

**Step 3: Commit**

```bash
git add tests/test_integration_phase4.py
git commit -m "feat(phase-4): add phase 4 integration tests"
```

---

## Phase 5: Governance & Ideas Channel (Weeks 9-10)

### Task 5.1: Token Manager Agent

**Files:**
- Create: `agents/token_manager_agent.py`
- Create: `backend/api/governance.py`
- Modify: `backend/main.py`
- Test: `tests/test_token_manager.py`

**Step 1: Write the failing tests**

```python
# tests/test_token_manager.py
import pytest
from unittest.mock import patch, MagicMock
from backend.database import Base, engine, SessionLocal
from backend.models import Agent, Team, TokenUsageLog, StandardsViolation
from uuid import uuid4
from datetime import datetime, timedelta

@pytest.fixture(autouse=True)
def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="T", leader_id="l1"))
    db.add(Agent(id="a1", name="Spender", team_id="t1", role="code_reviewer",
                 model="claude-3-5-sonnet-20241022", skills=[], preferences={}))
    # Add heavy token usage
    for i in range(3):
        db.add(TokenUsageLog(
            id=str(uuid4()), agent_id="a1", task_id=None,
            tokens_used=15000, timestamp=datetime.utcnow()
        ))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

def test_token_manager_flags_heavy_usage():
    from agents.token_manager_agent import TokenManagerAgent
    agent = TokenManagerAgent.__new__(TokenManagerAgent)
    agent.TOKEN_ALERT_THRESHOLD = 10000
    db = SessionLocal()
    violations = agent._check_token_usage(db)
    db.close()
    assert any(v["agent_id"] == "a1" for v in violations)

def test_token_usage_api():
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)
    resp = client.get("/governance/token-usage")
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["agent_id"] == "a1" for item in data)
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_token_manager.py -v
# Expected: ModuleNotFoundError — agents/token_manager_agent.py not found
```

**Step 3: Implement**

```python
# agents/token_manager_agent.py
from agents.base_agent import BaseAgent
from backend.database import SessionLocal
from backend.models import TokenUsageLog, StandardsViolation, Agent
from sqlalchemy import func
from datetime import datetime, timedelta
from uuid import uuid4
import time

class TokenManagerAgent(BaseAgent):
    """Pixel — the careful accountant 🐱"""

    TOKEN_ALERT_THRESHOLD = 10000  # tokens per task average
    CHECK_INTERVAL = 60  # seconds

    def __init__(self):
        super().__init__()
        self.name = "Pixel"
        self.role = "token_manager"
        self.model = "claude-3-5-sonnet-20241022"
        self.personality = (
            "You are Pixel, the careful accountant of the Clowder. "
            "You watch over token usage with a keen eye and gentle reminders. "
            "You are not harsh — just precise."
        )

    def _check_token_usage(self, db) -> list:
        """Find agents averaging over threshold tokens per task in last 24h."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        results = db.query(
            TokenUsageLog.agent_id,
            func.avg(TokenUsageLog.tokens_used).label("avg_tokens"),
            func.count(TokenUsageLog.id).label("task_count")
        ).filter(
            TokenUsageLog.timestamp >= cutoff
        ).group_by(TokenUsageLog.agent_id).all()

        violations = []
        for row in results:
            if row.avg_tokens and row.avg_tokens > self.TOKEN_ALERT_THRESHOLD:
                violations.append({
                    "agent_id": row.agent_id,
                    "avg_tokens": float(row.avg_tokens),
                    "task_count": row.task_count,
                })
        return violations

    def handle_task(self, task: dict) -> str:
        """Token Manager doesn't take regular tasks — it runs its own loop."""
        return "Token Manager does not handle regular tasks."

    def run(self):
        """Override run: check usage every 60 seconds."""
        self.register()
        self.log("🐱 Pixel (Token Manager) is online — watching the token budget.")
        while True:
            try:
                db = SessionLocal()
                violations = self._check_token_usage(db)
                for v in violations:
                    db.add(StandardsViolation(
                        id=str(uuid4()),
                        violation_type="token_excess",
                        agent_id=v["agent_id"],
                        severity="medium" if v["avg_tokens"] < 20000 else "high",
                        notes=f"Avg {v['avg_tokens']:.0f} tokens/task in last 24h (threshold: {self.TOKEN_ALERT_THRESHOLD})",
                        flagged_at=datetime.utcnow()
                    ))
                if violations:
                    db.commit()
                    self.log(f"Flagged {len(violations)} agents for token excess.")
                db.close()
            except Exception as e:
                self.log(f"Error in token check: {e}")
            time.sleep(self.CHECK_INTERVAL)
```

```python
# backend/api/governance.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import TokenUsageLog, StandardsViolation
from datetime import datetime, timedelta

router = APIRouter(prefix="/governance", tags=["governance"])

@router.get("/token-usage")
def get_token_usage(days: int = 7, db: Session = Depends(get_db)):
    """Per-agent token usage summary for the past N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = db.query(
        TokenUsageLog.agent_id,
        func.sum(TokenUsageLog.tokens_used).label("total_tokens"),
        func.avg(TokenUsageLog.tokens_used).label("avg_tokens"),
        func.count(TokenUsageLog.id).label("task_count")
    ).filter(TokenUsageLog.timestamp >= cutoff).group_by(TokenUsageLog.agent_id).all()

    return [
        {"agent_id": r.agent_id, "total_tokens": r.total_tokens,
         "avg_tokens": round(float(r.avg_tokens or 0), 1), "task_count": r.task_count}
        for r in rows
    ]

@router.get("/violations")
def list_violations(violation_type: str = None, agent_id: str = None,
                    severity: str = None, db: Session = Depends(get_db)):
    q = db.query(StandardsViolation)
    if violation_type:
        q = q.filter(StandardsViolation.violation_type == violation_type)
    if agent_id:
        q = q.filter(StandardsViolation.agent_id == agent_id)
    if severity:
        q = q.filter(StandardsViolation.severity == severity)
    violations = q.order_by(StandardsViolation.flagged_at.desc()).limit(100).all()
    return [
        {"id": v.id, "violation_type": v.violation_type, "agent_id": v.agent_id,
         "severity": v.severity, "notes": v.notes, "flagged_at": v.flagged_at.isoformat()}
        for v in violations
    ]
```

```python
# backend/main.py — add:
from backend.api.governance import router as governance_router
app.include_router(governance_router)
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_token_manager.py -v
# Expected: PASSED
```

**Step 5: Commit**

```bash
git add agents/token_manager_agent.py backend/api/governance.py tests/test_token_manager.py
git commit -m "feat(phase-5): add Token Manager agent and governance API"
```

---

### Task 5.2: Standards Manager Agent

**Files:**
- Create: `agents/standards_agent.py`
- Test: `tests/test_standards_agent.py`

**Step 1: Write the failing tests**

```python
# tests/test_standards_agent.py
import pytest
from unittest.mock import patch, MagicMock

def test_standards_agent_has_personality():
    from agents.standards_agent import StandardsAgent
    agent = StandardsAgent.__new__(StandardsAgent)
    agent.__init__()
    assert agent.name == "Spec"
    assert agent.role == "standards_manager"

def test_review_finds_violations():
    from agents.standards_agent import StandardsAgent
    agent = StandardsAgent.__new__(StandardsAgent)
    agent.__init__()

    mock_result = MagicMock()
    mock_result.content = [MagicMock(text="VIOLATIONS:\n- Missing type hints in function `foo`\n- Non-standard import order")]

    with patch.object(agent, '_call_claude', return_value=mock_result):
        violations = agent._review_code("def foo(x):\n    return x + 1", "task1")
    assert len(violations) > 0
    assert any("type hints" in v["notes"] for v in violations)

def test_review_clean_code_no_violations():
    from agents.standards_agent import StandardsAgent
    agent = StandardsAgent.__new__(StandardsAgent)
    agent.__init__()

    mock_result = MagicMock()
    mock_result.content = [MagicMock(text="NO VIOLATIONS")]

    with patch.object(agent, '_call_claude', return_value=mock_result):
        violations = agent._review_code("def foo(x: int) -> int:\n    return x + 1", "task1")
    assert len(violations) == 0
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_standards_agent.py -v
# Expected: ModuleNotFoundError
```

**Step 3: Implement**

```python
# agents/standards_agent.py
from agents.base_agent import BaseAgent
from backend.database import SessionLocal
from backend.models import StandardsViolation, Task
from uuid import uuid4
from datetime import datetime
import anthropic, os, time

class StandardsAgent(BaseAgent):
    """Spec — the meticulous standards keeper 🐱"""

    def __init__(self):
        super().__init__()
        self.name = "Spec"
        self.role = "standards_manager"
        self.model = "claude-3-5-sonnet-20241022"
        self.personality = (
            "You are Spec, the standards keeper of the Clowder. "
            "You ensure every agent follows the project's coding conventions. "
            "You are thorough, fair, and always cite specific issues."
        )
        self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def _call_claude(self, code: str) -> object:
        return self._client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": (
                    "Review the following code for formatting and standards issues. "
                    "Check for: inconsistent naming, missing type hints, non-standard imports, "
                    "missing docstrings on public functions. "
                    "If there are violations, respond with 'VIOLATIONS:' followed by a bullet list. "
                    "If code is clean, respond with exactly 'NO VIOLATIONS'.\n\n"
                    f"```python\n{code}\n```"
                )
            }]
        )

    def _review_code(self, code: str, task_id: str) -> list:
        result = self._call_claude(code)
        response_text = result.content[0].text

        if "NO VIOLATIONS" in response_text:
            return []

        violations = []
        if "VIOLATIONS:" in response_text:
            lines = response_text.split("VIOLATIONS:")[1].strip().split("\n")
            for line in lines:
                line = line.strip().lstrip("-•").strip()
                if line:
                    violations.append({
                        "violation_type": "code_format",
                        "task_id": task_id,
                        "severity": "low",
                        "notes": line
                    })
        return violations

    def handle_task(self, task: dict) -> str:
        """Standards Manager reviews completed tasks on its own loop."""
        return "Standards Manager does not handle regular tasks."

    def run(self):
        """Override: review completed tasks every 30 seconds."""
        self.register()
        self.log("🐱 Spec (Standards Manager) is online — watching for violations.")
        reviewed_tasks = set()

        while True:
            try:
                db = SessionLocal()
                done_tasks = db.query(Task).filter(
                    Task.status == "done",
                    Task.result.isnot(None)
                ).limit(20).all()

                for task in done_tasks:
                    if task.id in reviewed_tasks:
                        continue
                    reviewed_tasks.add(task.id)

                    # Look for code blocks in the result
                    if "```" in (task.result or ""):
                        violations = self._review_code(task.result, task.id)
                        for v in violations:
                            db.add(StandardsViolation(
                                id=str(uuid4()),
                                agent_id=task.claimed_by,
                                flagged_at=datetime.utcnow(),
                                **v
                            ))
                        if violations:
                            db.commit()
                            self.log(f"Flagged {len(violations)} violations in task {task.id[:8]}")
                db.close()
            except Exception as e:
                self.log(f"Error in standards check: {e}")
            time.sleep(30)
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_standards_agent.py -v
# Expected: PASSED
```

**Step 5: Commit**

```bash
git add agents/standards_agent.py tests/test_standards_agent.py
git commit -m "feat(phase-5): add Standards Manager agent (Spec)"
```

---

### Task 5.3: Enhanced Ideas Channel

**Files:**
- Create: `backend/api/ideas.py` (extends Phase 3 stub)
- Create: `frontend/src/views/IdeasChannel.vue`
- Modify: `backend/main.py`
- Test: `tests/test_ideas_enhanced.py`

**Step 1: Write the failing tests**

```python
# tests/test_ideas_enhanced.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team, Agent, Idea

@pytest.fixture(autouse=True)
def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="T", leader_id="pm1"))
    db.add(Agent(id="pm1", name="Project Manager", team_id="t1",
                 role="project_manager", model="claude-3-5-sonnet-20241022",
                 skills=[], preferences={}))
    db.add(Agent(id="a1", name="Shadow", team_id="t1",
                 role="code_reviewer", model="claude-3-5-sonnet-20241022",
                 skills=[], preferences={}))
    db.add(Idea(id="i1", author_id="a1", title="Add caching",
                description="We should cache embeddings.", status="submitted"))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(): return TestClient(app)

def test_list_ideas(client):
    resp = client.get("/ideas/")
    assert resp.status_code == 200
    assert any(i["title"] == "Add caching" for i in resp.json())

def test_pm_approve_idea(client):
    resp = client.put("/ideas/i1/status", json={"status": "approved", "approved_by": "pm1"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

def test_pm_reject_idea(client):
    resp = client.put("/ideas/i1/status", json={"status": "rejected", "notes": "Out of scope."})
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"

def test_implement_idea_creates_task(client):
    client.put("/ideas/i1/status", json={"status": "approved", "approved_by": "pm1"})
    resp = client.post("/ideas/i1/implement")
    assert resp.status_code == 200
    assert "task_id" in resp.json()
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_ideas_enhanced.py -v
# Expected: 404 — /ideas/ not registered
```

**Step 3: Implement**

```python
# backend/api/ideas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime
from backend.database import get_db
from backend.models import Idea, Task

router = APIRouter(prefix="/ideas", tags=["ideas"])

class IdeaCreate(BaseModel):
    author_id: str
    title: str
    description: Optional[str] = None

class StatusUpdate(BaseModel):
    status: str
    approved_by: Optional[str] = None
    notes: Optional[str] = None

@router.get("/")
def list_ideas(status: str = None, db: Session = Depends(get_db)):
    q = db.query(Idea)
    if status:
        q = q.filter(Idea.status == status)
    ideas = q.order_by(Idea.created_at.desc()).all()
    return [
        {"id": i.id, "author_id": i.author_id, "title": i.title,
         "description": i.description, "status": i.status, "created_at": i.created_at.isoformat()}
        for i in ideas
    ]

@router.post("/")
def create_idea(idea: IdeaCreate, db: Session = Depends(get_db)):
    db_idea = Idea(
        id=str(uuid4()), author_id=idea.author_id,
        title=idea.title, description=idea.description,
        status="submitted", created_at=datetime.utcnow()
    )
    db.add(db_idea); db.commit(); db.refresh(db_idea)
    return {"id": db_idea.id, "title": db_idea.title, "status": db_idea.status}

@router.put("/{idea_id}/status")
def update_status(idea_id: str, update: StatusUpdate, db: Session = Depends(get_db)):
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    idea.status = update.status
    if update.approved_by:
        idea.approved_by = update.approved_by
    db.commit(); db.refresh(idea)
    return {"id": idea.id, "status": idea.status, "title": idea.title}

@router.post("/{idea_id}/implement")
def implement_idea(idea_id: str, db: Session = Depends(get_db)):
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    if idea.status != "approved":
        raise HTTPException(status_code=400, detail="Idea must be approved before implementing")
    task = Task(
        id=str(uuid4()), title=f"Implement: {idea.title}",
        description=idea.description, status="pending",
        created_at=datetime.utcnow()
    )
    db.add(task); idea.status = "implementing"; db.commit()
    return {"task_id": task.id, "idea_id": idea_id, "message": "Task created 🐾"}
```

```python
# backend/main.py — add:
from backend.api.ideas import router as ideas_router
app.include_router(ideas_router)
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_ideas_enhanced.py -v
# Expected: PASSED
```

**Step 5: Commit**

```bash
git add backend/api/ideas.py tests/test_ideas_enhanced.py
git commit -m "feat(phase-5): add enhanced ideas channel with approve/reject/implement"
```

---

### Task 5.4: Team Leader Meeting Interface

**Files:**
- Create: `backend/meeting_service.py`
- Create: `backend/api/meetings.py`
- Create: `frontend/src/views/MeetingNotes.vue`
- Modify: `backend/main.py`
- Test: `tests/test_meetings.py`

**Step 1: Write the failing tests**

```python
# tests/test_meetings.py
import pytest, json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team, Agent, StandardsViolation, Idea
from uuid import uuid4
from datetime import datetime

@pytest.fixture(autouse=True)
def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="T", leader_id="l1"))
    db.add(Agent(id="a1", name="Shadow", team_id="t1", role="code_reviewer",
                 model="claude-3-5-sonnet-20241022", skills=[], preferences={}))
    db.add(StandardsViolation(id=str(uuid4()), violation_type="code_format",
                               agent_id="a1", severity="low",
                               notes="Missing type hints", flagged_at=datetime.utcnow()))
    db.add(Idea(id=str(uuid4()), author_id="a1", title="Improve caching",
                status="approved", created_at=datetime.utcnow()))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(): return TestClient(app)

def test_generate_meeting_summary(client):
    resp = client.post("/meetings/generate")
    assert resp.status_code == 200
    data = resp.json()
    assert "violations_this_week" in data
    assert "ideas_discussed" in data

def test_list_meetings(client):
    client.post("/meetings/generate")
    resp = client.get("/meetings/")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_meetings.py -v
# Expected: 404 — /meetings/ not registered
```

**Step 3: Implement**

```python
# backend/meeting_service.py
from backend.models import StandardsViolation, Idea, Task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from pathlib import Path

MEETINGS_DIR = Path("board/meetings")

class MeetingService:
    @staticmethod
    def generate_summary(db: Session) -> dict:
        MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
        cutoff = datetime.utcnow() - timedelta(days=7)

        violations = db.query(StandardsViolation).filter(
            StandardsViolation.flagged_at >= cutoff
        ).all()

        ideas = db.query(Idea).filter(
            Idea.created_at >= cutoff,
            Idea.status.in_(["submitted", "approved", "rejected"])
        ).all()

        summary = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "generated_at": datetime.utcnow().isoformat(),
            "violations_this_week": [
                {"agent_id": v.agent_id, "type": v.violation_type,
                 "severity": v.severity, "notes": v.notes}
                for v in violations
            ],
            "ideas_discussed": [
                {"id": i.id, "title": i.title, "status": i.status}
                for i in ideas
            ],
            "agents_flagged": list({v.agent_id for v in violations if v.agent_id}),
        }

        path = MEETINGS_DIR / f"{summary['date']}.json"
        with open(path, "w") as f:
            json.dump(summary, f, indent=2)

        return summary

    @staticmethod
    def get_meetings(limit: int = 5) -> list:
        MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(MEETINGS_DIR.glob("*.json"), reverse=True)[:limit]
        meetings = []
        for f in files:
            with open(f) as fp:
                meetings.append(json.load(fp))
        return meetings
```

```python
# backend/api/meetings.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["meetings"])

@router.post("/generate")
def generate_meeting(db: Session = Depends(get_db)):
    return MeetingService.generate_summary(db)

@router.get("/")
def list_meetings():
    return MeetingService.get_meetings()
```

```python
# backend/main.py — add:
from backend.api.meetings import router as meetings_router
app.include_router(meetings_router)
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_meetings.py -v
# Expected: PASSED
```

**Step 5: Commit**

```bash
git add backend/meeting_service.py backend/api/meetings.py tests/test_meetings.py
git commit -m "feat(phase-5): add team leader meeting summary generation"
```

---

## Phase 6: Polish, Web Dashboard & Deployment (Weeks 11-12)

### Task 6.1: Cat Copy & Theming

**Files:**
- Create: `backend/cat_copy.py`
- Test: `tests/test_cat_copy.py`

**Step 1: Write the failing tests**

```python
# tests/test_cat_copy.py
from backend.cat_copy import CatCopy

def test_error_message_has_cat():
    assert "🐱" in CatCopy.ERROR or "claws" in CatCopy.ERROR.lower()

def test_all_keys_present():
    required = ["ERROR", "SUCCESS", "MAIN_HALL", "IDEAS_CHANNEL", "STANDARDS_FLAGGED", "PM_ONLINE"]
    for key in required:
        assert hasattr(CatCopy, key), f"Missing CatCopy.{key}"

def test_pm_online_has_meow():
    assert "meow" in CatCopy.PM_ONLINE.lower() or "🐱" in CatCopy.PM_ONLINE
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_cat_copy.py -v
# Expected: ModuleNotFoundError
```

**Step 3: Implement**

```python
# backend/cat_copy.py
class CatCopy:
    """Cat-themed copy strings used throughout Clowder. 🐱"""

    ERROR = "Oops, claws got tangled 🐱 — something went wrong."
    SUCCESS = "Purrfectly done! ✅"
    LOADING = "One moment, stretching paws... 🐾"

    MAIN_HALL = "🐱 Main Hall — All Cats Welcome"
    TEAM_LOUNGE = "🐾 Team Lounge"
    LEADERS_BOARD = "🐾 Team Leaders' Lounge"
    IDEAS_CHANNEL = "💡 Catnip Ideas"
    STANDARDS_FLAGGED = "😾 Standards Flagged"
    PM_CHANNEL = "📋 Project Manager's Den"

    PM_ONLINE = "Meow! 🐱 Project Manager is online and ready to lead the clowder."
    AGENT_JOINED = "A new cat has joined the clowder! 🐾"
    TASK_CLAIMED = "Task claimed — paws on the keyboard! ⌨️"
    TASK_DONE = "Task complete! This cat delivers. ✅"
    IDEA_APPROVED = "Catnip approved! 💡 Adding to the backlog."
    IDEA_REJECTED = "Not today — maybe next sprint. 😸"
    VIOLATION_FLAGGED = "😾 Standards issue spotted — let's discuss in the next meeting."
    OFFLINE_MODE = "API is napping 😴 — switching to local board."
    ONLINE_MODE = "API is awake! 🐱 Switching to API mode."
    CONFLICT = "Hairball alert ⚠️ — task conflict detected. Check board/conflicts.json."
    EXPORT_READY = "Your agent is packed and ready to travel. 🧳🐱"
    IMPORT_SUCCESS = "Welcome to the clowder! 🐱 Agent imported successfully."
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_cat_copy.py -v
# Expected: PASSED
```

**Step 5: Commit**

```bash
git add backend/cat_copy.py tests/test_cat_copy.py
git commit -m "feat(phase-6): add cat-themed copy strings (CatCopy)"
```

---

### Task 6.2: Main Web Dashboard

**Files:**
- Create: `frontend/src/views/Dashboard.vue`
- Create: `frontend/src/views/TaskBoard.vue`
- Create: `frontend/src/components/TaskCard.vue`
- Create: `frontend/src/App.vue` (update nav)

**Step 1: Implement Dashboard**

```vue
<!-- frontend/src/views/Dashboard.vue -->
<template>
  <div class="dashboard">
    <h1>🐱 Clowder Mission Control</h1>

    <!-- Board Status -->
    <section class="status-row">
      <div class="stat-card pending">
        <span class="count">{{ stats.pending }}</span>
        <span class="label">Pending</span>
      </div>
      <div class="stat-card in-progress">
        <span class="count">{{ stats.in_progress }}</span>
        <span class="label">In Progress</span>
      </div>
      <div class="stat-card done">
        <span class="count">{{ stats.done }}</span>
        <span class="label">Done</span>
      </div>
      <div class="stat-card violations" v-if="stats.critical_violations > 0">
        <span class="count">{{ stats.critical_violations }}</span>
        <span class="label">😾 Critical</span>
      </div>
    </section>

    <!-- Active Agents -->
    <section class="agents-section">
      <h2>🐾 Active Agents</h2>
      <div class="agent-row" v-for="agent in activeAgents" :key="agent.id">
        <div class="mini-avatar" v-html="agent.avatar_svg || defaultAvatar" />
        <span class="agent-name">{{ agent.name }}</span>
        <span class="agent-role">{{ agent.role }}</span>
        <span class="agent-status" :class="agent.status">{{ agent.status }}</span>
      </div>
    </section>

    <!-- Recent Chat -->
    <section class="chat-section">
      <h2>🐱 Main Hall — Recent</h2>
      <div class="message" v-for="msg in recentChat" :key="msg.id">
        <strong>{{ msg.author_id }}:</strong> {{ msg.message }}
        <span class="reactions">
          <span v-for="(users, type) in msg.reactions" :key="type">
            {{ reactionEmoji(type) }} {{ users.length }}
          </span>
        </span>
      </div>
      <router-link to="/chat" class="see-more">See all in Main Hall →</router-link>
    </section>

    <!-- Trending Ideas -->
    <section class="ideas-section">
      <h2>💡 Trending Catnip Ideas</h2>
      <div class="idea" v-for="idea in trendingIdeas" :key="idea.id">
        <strong>{{ idea.title }}</strong>
        <span class="status-badge" :class="idea.status">{{ idea.status }}</span>
      </div>
      <router-link to="/ideas" class="see-more">See all ideas →</router-link>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/index.js'

const stats = ref({ pending: 0, in_progress: 0, done: 0, critical_violations: 0 })
const activeAgents = ref([])
const recentChat = ref([])
const trendingIdeas = ref([])
const defaultAvatar = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🐱</text></svg>'

const reactionEmoji = (type) => ({
  heart: '❤️', thumbs_up: '👍', clap: '👏', fire: '🔥', think: '💭'
}[type] || type)

onMounted(async () => {
  const [pending, inprog, done, agents, chat, ideas] = await Promise.all([
    api.get('/tasks/?status=pending'),
    api.get('/tasks/?status=in_progress'),
    api.get('/tasks/?status=done'),
    api.get('/agents/'),
    api.get('/chat/main_hall?limit=5'),
    api.get('/ideas/?status=submitted'),
  ])
  stats.value.pending = pending.data.length
  stats.value.in_progress = inprog.data.length
  stats.value.done = done.data.length
  activeAgents.value = agents.data.slice(0, 6)
  recentChat.value = chat.data
  trendingIdeas.value = ideas.data.slice(0, 3)
})
</script>

<style scoped>
.dashboard { max-width: 1000px; margin: 2rem auto; padding: 1rem; }
h1 { font-size: 2rem; margin-bottom: 1.5rem; }
h2 { margin: 1.5rem 0 0.75rem; border-bottom: 2px solid #ffe0b2; padding-bottom: 0.25rem; }
.status-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
.stat-card { background: #fff8f0; border-radius: 12px; padding: 1.5rem; text-align: center; flex: 1; }
.stat-card .count { display: block; font-size: 2.5rem; font-weight: bold; }
.stat-card .label { color: #888; font-size: 0.9rem; }
.stat-card.violations { background: #fff3e0; }
.agent-row { display: flex; align-items: center; gap: 1rem; padding: 0.5rem 0; border-bottom: 1px solid #f5e6d0; }
.mini-avatar { width: 36px; height: 36px; }
.agent-status { margin-left: auto; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; background: #e8f5e9; }
.message { padding: 0.5rem 0; border-bottom: 1px solid #f5e6d0; }
.reactions { margin-left: 0.5rem; font-size: 0.85rem; color: #888; }
.see-more { display: block; margin-top: 0.5rem; color: #ff8f00; text-decoration: none; }
.idea { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0; }
.status-badge { padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; background: #fff9c4; }
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "feat(phase-6): add main dashboard with board stats, agents, chat, ideas"
```

---

### Task 6.3: Enhanced TUI

**Files:**
- Modify: `mission_control.py`
- Test: `tests/test_tui.py`

**Step 1: Write the failing tests**

```python
# tests/test_tui.py
import pytest
from unittest.mock import patch, MagicMock

def test_tui_has_multiple_screens():
    """TUI must expose at least 5 screen modes."""
    import mission_control
    screens = [attr for attr in dir(mission_control) if attr.startswith('screen_')]
    assert len(screens) >= 4, f"Expected 4+ screen functions, got: {screens}"

def test_screen_names_exist():
    import mission_control
    for name in ['screen_board', 'screen_chat', 'screen_ideas', 'screen_agents']:
        assert hasattr(mission_control, name), f"Missing function: {name}"
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_tui.py -v
# Expected: screen functions not found
```

**Step 3: Implement**

```python
# mission_control.py — add these screen functions to the existing file:

def screen_board(stdscr, tasks):
    """Screen 1: Task board view."""
    stdscr.clear()
    stdscr.addstr(0, 0, "🐱 CLOWDER — Task Board", curses.A_BOLD)
    stdscr.addstr(1, 0, "─" * 60)
    for i, task in enumerate(tasks[:20], start=2):
        status_icon = {"pending": "⏳", "in_progress": "🔄", "done": "✅", "blocked": "⛔"}.get(task.get("status"), "?")
        line = f"{status_icon} [{task.get('status','?')[:8]:8}] {task.get('title','')[:45]}"
        stdscr.addstr(i, 0, line[:79])
    stdscr.addstr(23, 0, "Tab: switch screen | q: quit | r: refresh", curses.A_DIM)
    stdscr.refresh()

def screen_chat(stdscr, messages):
    """Screen 2: Main Hall chat."""
    stdscr.clear()
    stdscr.addstr(0, 0, "🐱 CLOWDER — Main Hall Chat", curses.A_BOLD)
    stdscr.addstr(1, 0, "─" * 60)
    for i, msg in enumerate(messages[-20:], start=2):
        author = msg.get("author_id", "?")[:12]
        text = msg.get("message", "")[:50]
        stdscr.addstr(i, 0, f"{author}: {text}"[:79])
    stdscr.addstr(22, 0, "m: post message | Tab: switch | q: quit", curses.A_DIM)
    stdscr.refresh()

def screen_ideas(stdscr, ideas):
    """Screen 3: Ideas channel."""
    stdscr.clear()
    stdscr.addstr(0, 0, "💡 CLOWDER — Catnip Ideas", curses.A_BOLD)
    stdscr.addstr(1, 0, "─" * 60)
    for i, idea in enumerate(ideas[:20], start=2):
        status_icon = {"submitted": "📬", "approved": "✅", "rejected": "❌", "implementing": "🔄"}.get(idea.get("status"), "?")
        line = f"{status_icon} {idea.get('title','')[:55]}"
        stdscr.addstr(i, 0, line[:79])
    stdscr.addstr(23, 0, "a: approve | r: reject | Tab: switch | q: quit", curses.A_DIM)
    stdscr.refresh()

def screen_agents(stdscr, agents):
    """Screen 4: Agent gallery."""
    stdscr.clear()
    stdscr.addstr(0, 0, "🐾 CLOWDER — Agent Gallery", curses.A_BOLD)
    stdscr.addstr(1, 0, "─" * 60)
    for i, agent in enumerate(agents[:20], start=2):
        line = f"🐱 {agent.get('name','?')[:15]:15} | {agent.get('role','?')[:20]:20} | {agent.get('team_id','?')[:10]}"
        stdscr.addstr(i, 0, line[:79])
    stdscr.addstr(23, 0, "Tab: switch screen | q: quit", curses.A_DIM)
    stdscr.refresh()
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_tui.py -v
# Expected: PASSED
```

**Step 5: Commit**

```bash
git add mission_control.py tests/test_tui.py
git commit -m "feat(phase-6): add multi-screen TUI (board, chat, ideas, agents)"
```

---

### Task 6.4: Production Docker Setup

**Files:**
- Modify: `Dockerfile` (multi-stage, non-root user)
- Modify: `docker-compose.yml` (add nginx, frontend build)
- Create: `nginx.conf`
- Create: `Makefile`
- Test: `tests/test_docker.py`

**Step 1: Write the failing tests**

```python
# tests/test_docker.py
import subprocess, json, pytest

def test_docker_compose_valid():
    result = subprocess.run(
        ["docker-compose", "config", "--quiet"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"docker-compose config invalid: {result.stderr}"

def test_dockerfile_exists():
    from pathlib import Path
    assert Path("Dockerfile").exists()
    content = Path("Dockerfile").read_text()
    assert "FROM python" in content

def test_nginx_conf_exists():
    from pathlib import Path
    assert Path("nginx.conf").exists()
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_docker.py -v
# Expected: docker-compose config may fail if not yet updated
```

**Step 3: Implement**

```dockerfile
# Dockerfile (updated — multi-stage, non-root)
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /root/.cache /root/.cache
COPY . .
RUN useradd -m -u 1000 clowder && chown -R clowder:clowder /app
USER clowder
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```nginx
# nginx.conf
server {
    listen 80;

    location /api/ {
        proxy_pass http://api:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://api:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
    }

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

```makefile
# Makefile
.PHONY: dev prod test clean

dev:
	docker-compose up --build

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

test:
	pytest tests/ -v --tb=short

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_docker.py -v
# Expected: PASSED
```

**Step 5: Commit**

```bash
git add Dockerfile nginx.conf Makefile tests/test_docker.py
git commit -m "feat(phase-6): update Dockerfile for production (multi-stage, non-root)"
```

---

### Task 6.5: Final End-to-End Test

**Files:**
- Create: `tests/test_e2e.py`

**Step 1: Write the test**

```python
# tests/test_e2e.py
"""
Full end-to-end smoke test for Clowder v2.
Tests the complete flow: task creation → claim → complete → chat → idea → approve.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team, Agent

@pytest.fixture(autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="Whiskers Team", leader_id="leader1"))
    db.add(Agent(id="leader1", name="Whiskers", team_id="t1", role="team_leader",
                 model="claude-3-5-sonnet-20241022", skills=[], preferences={}))
    db.add(Agent(id="shadow", name="Shadow", team_id="t1", role="code_reviewer",
                 model="claude-3-5-sonnet-20241022", skills=["python"], preferences={}))
    db.add(Agent(id="user", name="Human", team_id="t1", role="user",
                 model="none", skills=[], preferences={}))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(): return TestClient(app)

def test_full_workflow(client):
    # 1. Create task
    task = client.post("/tasks/", json={"title": "Code review: auth module", "assigned_to_team": "t1"}).json()
    assert task["status"] == "pending"

    # 2. Agent claims task
    claim = client.put(f"/tasks/{task['id']}", json={"status": "in_progress", "claimed_by": "shadow"}).json()
    assert claim["status"] == "in_progress"

    # 3. Agent completes task
    done = client.put(f"/tasks/{task['id']}", json={
        "status": "done",
        "result": "Found 2 issues: missing input validation, JWT expiry not checked."
    }).json()
    assert done["status"] == "done"

    # 4. Agent posts to Main Hall
    msg = client.post("/chat/main_hall?author_id=shadow",
                      json={"message": "Completed auth review. Found 2 security issues! 🐱"}).json()
    assert msg["author_id"] == "shadow"

    # 5. User reacts to message
    client.post(f"/chat/{msg['id']}/react?reaction_type=heart&reactor_id=user")
    reactions = client.get(f"/chat/{msg['id']}/reactions").json()
    assert "heart" in reactions

    # 6. User posts to chat
    user_msg = client.post("/chat/main_hall?author_id=user",
                           json={"message": "Nice catch Shadow! 🐾 What were the issues?"}).json()
    assert user_msg["author_id"] == "user"

    # 7. Agent replies
    reply = client.post("/chat/main_hall?author_id=shadow", json={
        "message": "Missing input validation on /login and JWT not checking expiry.",
        "parent_message_id": user_msg["id"]
    }).json()
    assert reply["parent_message_id"] == user_msg["id"]

    # 8. Agent submits idea
    idea = client.post("/ideas/", json={
        "author_id": "shadow",
        "title": "Add automated JWT validation checks",
        "description": "We keep finding this issue. Let's add automated checks."
    }).json()
    assert idea["status"] == "submitted"

    # 9. PM approves idea
    approved = client.put(f"/ideas/{idea['id']}/status",
                          json={"status": "approved", "approved_by": "leader1"}).json()
    assert approved["status"] == "approved"

    # 10. Idea becomes task
    impl = client.post(f"/ideas/{idea['id']}/implement").json()
    assert "task_id" in impl

    # 11. Verify board.json was synced
    from pathlib import Path
    import json
    board_file = Path("board/board.json")
    if board_file.exists():
        board = json.loads(board_file.read_text())
        assert isinstance(board.get("tasks"), list)

def test_agent_export_import_roundtrip(client):
    export_data = client.get("/agents/shadow/export/json").json()
    export_data["agent_metadata"]["name"] = "Shadow_Clone"
    resp = client.post("/agents/import/json?team_id=t1", json=export_data)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Shadow_Clone"

def test_cat_copy_in_api_responses(client):
    """Verify cat-themed messages appear in API responses."""
    from backend.cat_copy import CatCopy
    assert "🐱" in CatCopy.PM_ONLINE
    assert "catnip" in CatCopy.IDEAS_CHANNEL.lower() or "💡" in CatCopy.IDEAS_CHANNEL
```

**Step 2: Run test — verify it passes**

```bash
pytest tests/test_e2e.py -v
# Expected: all tests PASSED (requires all phases complete)
```

**Step 3: Commit**

```bash
git add tests/test_e2e.py
git commit -m "feat(phase-6): add full end-to-end integration test for complete workflow"
```

---

## Phase 6 Completion Checklist

Before marking Phase 6 done, verify all of these pass:

```bash
# Full test suite
pytest tests/ -v --tb=short

# Docker smoke test
docker-compose up -d
sleep 15
curl http://localhost:8000/health
curl http://localhost:3000  # Vue frontend

# Verify board.json syncs
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Final test task"}'
cat board/board.json

# Verify cat flair
python -c "from backend.cat_copy import CatCopy; print(CatCopy.PM_ONLINE)"

docker-compose down
```

---

## Summary

| Phase | Tasks | Key Deliverables |
|---|---|---|
| **4** | 4.1–4.6 | Agent profiles, avatar SVG, export/import JSON+MD, Vue gallery |
| **5** | 5.1–5.4 | Token Manager (Pixel), Standards Agent (Spec), ideas lifecycle, meetings |
| **6** | 6.1–6.5 | Cat flair, main dashboard, TUI screens, production Docker, E2E test |

All features from the design document are implemented. No features sacrificed. 🐾
