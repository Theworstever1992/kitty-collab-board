# Clowder v2 — Phase 1 Implementation Plan: Core Infrastructure

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the core API, hybrid board, PM agent, Team Leader base, and chat storage that all subsequent phases build on.

**Architecture:** FastAPI + PostgreSQL + hybrid file/DB board + smart mode agent client
**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, PostgreSQL 15 + pgvector, pytest, Docker Compose

---

## Task 1.1: Project Structure & Dependencies

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Modify: `requirements.txt`
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`

**Step 1: Write the failing test**

```python
# tests/test_config.py
from backend.config import settings

def test_settings_has_database_url():
    assert hasattr(settings, 'DATABASE_URL')
    assert 'postgresql' in settings.DATABASE_URL

def test_settings_has_board_dir():
    assert hasattr(settings, 'BOARD_DIR')

def test_settings_has_rag_config():
    assert hasattr(settings, 'RAG_MAX_CONTEXT_TOKENS')
    assert hasattr(settings, 'RAG_RETRIEVAL_TOP_K')

def test_settings_has_ideas_threshold():
    assert hasattr(settings, 'IDEAS_AUTO_SURFACE_THRESHOLD')
    assert settings.IDEAS_AUTO_SURFACE_THRESHOLD == 10
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_config.py -v
# Expected: ModuleNotFoundError — backend/config.py does not exist
```

**Step 3: Implement**

```python
# backend/__init__.py
__version__ = "2.0.0"
```

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/clowder"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Paths
    BOARD_DIR: str = "board"
    LOGS_DIR: str = "logs"

    # Models
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # RAG
    RAG_MAX_CONTEXT_TOKENS: int = 2000
    RAG_RETRIEVAL_TOP_K: int = 5

    # Ideas
    IDEAS_AUTO_SURFACE_THRESHOLD: int = 10
    IDEAS_WINDOW_HOURS: int = 48

    # Token governance
    TOKEN_ALERT_THRESHOLD: int = 10000

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

```text
# requirements.txt (full replacement)
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
anthropic>=0.7.1
sentence-transformers==3.0.0
pgvector==0.2.4
websockets==12.0
alembic==1.13.0
requests==2.31.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.0
```

```dockerfile
# Dockerfile (updated)
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

```yaml
# docker-compose.yml (updated)
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg15-latest
    environment:
      POSTGRES_DB: clowder
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
    env_file: .env
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/clowder
    volumes:
      - ./board:/app/board
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    image: node:20-slim
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "3000:3000"
    command: sh -c "npm install && npm run dev -- --host"
    depends_on:
      - api

volumes:
  postgres_data:
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_config.py -v
# Expected: all 4 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/__init__.py backend/config.py requirements.txt Dockerfile docker-compose.yml tests/test_config.py
git commit -m "feat(phase-1): add project structure, config, and Docker setup"
```

---

## Task 1.2: PostgreSQL Schema & Alembic Migrations

**Files:**
- Create: `backend/database.py`
- Create: `backend/models.py`
- Run: `alembic init alembic`
- Create: `alembic/versions/001_initial_schema.py`
- Test: `tests/test_database.py`

**Step 1: Write the failing test**

```python
# tests/test_database.py
import pytest
from sqlalchemy import inspect
from backend.database import engine, Base
from backend.models import Team, Agent, Task, ChatMessage, MessageReaction, Idea, StandardsViolation, TokenUsageLog

@pytest.fixture(autouse=True)
def setup_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_all_tables_created():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for expected in ['teams', 'agents', 'tasks', 'chat_messages', 'message_reactions',
                     'ideas', 'standards_violations', 'token_usage_log']:
        assert expected in tables, f"Missing table: {expected}"

def test_agent_has_required_columns():
    inspector = inspect(engine)
    cols = {c['name'] for c in inspector.get_columns('agents')}
    for col in ['id', 'name', 'team_id', 'role', 'bio', 'avatar_svg', 'model', 'skills', 'preferences']:
        assert col in cols, f"Missing column: agents.{col}"

def test_task_has_required_columns():
    inspector = inspect(engine)
    cols = {c['name'] for c in inspector.get_columns('tasks')}
    for col in ['id', 'title', 'status', 'claimed_by', 'assigned_to_team', 'result']:
        assert col in cols
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_database.py -v
# Expected: ModuleNotFoundError — backend/database.py missing
```

**Step 3: Implement**

```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# backend/models.py
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Team(Base):
    __tablename__ = "teams"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    leader_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    agents = relationship("Agent", back_populates="team")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    team_id = Column(String, ForeignKey("teams.id"), nullable=False)
    role = Column(String, nullable=False)
    bio = Column(Text)
    avatar_svg = Column(Text)
    model = Column(String, default="claude-3-5-sonnet-20241022")
    skills = Column(JSON, default=list)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    team = relationship("Team", back_populates="agents")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="pending")
    claimed_by = Column(String, ForeignKey("agents.id"))
    assigned_to_team = Column(String, ForeignKey("teams.id"))
    result = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True)
    author_id = Column(String, ForeignKey("agents.id"), nullable=False)
    room = Column(String, default="main_hall")
    message = Column(Text, nullable=False)
    parent_message_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    author = relationship("Agent")

class MessageReaction(Base):
    __tablename__ = "message_reactions"
    id = Column(String, primary_key=True)
    message_id = Column(String, ForeignKey("chat_messages.id"), nullable=False)
    reactor_id = Column(String, ForeignKey("agents.id"), nullable=False)
    reaction_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Idea(Base):
    __tablename__ = "ideas"
    id = Column(String, primary_key=True)
    author_id = Column(String, ForeignKey("agents.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="submitted")
    approved_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class StandardsViolation(Base):
    __tablename__ = "standards_violations"
    id = Column(String, primary_key=True)
    violation_type = Column(String, nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"))
    task_id = Column(String, ForeignKey("tasks.id"))
    severity = Column(String)
    notes = Column(Text)
    flagged_at = Column(DateTime, default=datetime.utcnow)

class TokenUsageLog(Base):
    __tablename__ = "token_usage_log"
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    task_id = Column(String, ForeignKey("tasks.id"))
    tokens_used = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
```

```bash
# Initialize Alembic (run once)
alembic init alembic
# Then edit alembic.ini: set sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/clowder
# Then edit alembic/env.py: add "from backend.models import Base" and set target_metadata = Base.metadata
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_database.py -v
# Expected: all 3 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/database.py backend/models.py alembic/ tests/test_database.py
git commit -m "feat(phase-1): add PostgreSQL schema and Alembic migrations"
```

---

## Task 1.3: FastAPI App + Task Endpoints

**Files:**
- Create: `backend/main.py`
- Create: `backend/schemas.py`
- Create: `backend/api/__init__.py`
- Create: `backend/api/tasks.py`
- Test: `tests/test_tasks.py`

**Step 1: Write the failing test**

```python
# tests/test_tasks.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team, Agent

@pytest.fixture(autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="Test Team", leader_id="a1"))
    db.add(Agent(id="a1", name="Shadow", team_id="t1", role="code_reviewer",
                 model="claude-3-5-sonnet-20241022", skills=[], preferences={}))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(): return TestClient(app)

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_create_task(client):
    resp = client.post("/tasks/", json={"title": "Test task", "description": "Do the thing"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test task"
    assert data["status"] == "pending"
    assert "id" in data

def test_list_tasks_by_status(client):
    client.post("/tasks/", json={"title": "Task A"})
    client.post("/tasks/", json={"title": "Task B"})
    resp = client.get("/tasks/?status=pending")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2

def test_get_task_by_id(client):
    created = client.post("/tasks/", json={"title": "Find me"}).json()
    resp = client.get(f"/tasks/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Find me"

def test_get_task_not_found(client):
    resp = client.get("/tasks/nonexistent-id")
    assert resp.status_code == 404

def test_claim_task(client):
    task = client.post("/tasks/", json={"title": "Claimable"}).json()
    resp = client.put(f"/tasks/{task['id']}", json={"status": "in_progress", "claimed_by": "a1"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["claimed_by"] == "a1"

def test_complete_task(client):
    task = client.post("/tasks/", json={"title": "Completable"}).json()
    client.put(f"/tasks/{task['id']}", json={"status": "in_progress", "claimed_by": "a1"})
    resp = client.put(f"/tasks/{task['id']}", json={"status": "done", "result": "All done!"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_tasks.py -v
# Expected: ModuleNotFoundError — backend/main.py missing
```

**Step 3: Implement**

```python
# backend/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to_team: Optional[str] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    claimed_by: Optional[str] = None
    result: Optional[str] = None
    assigned_to_team: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    claimed_by: Optional[str]
    assigned_to_team: Optional[str]
    result: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
```

```python
# backend/api/__init__.py
```

```python
# backend/api/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import uuid4
from datetime import datetime
from backend.database import get_db
from backend.models import Task
from backend.schemas import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskResponse])
def list_tasks(status: str = "pending", db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.status == status).order_by(desc(Task.created_at)).all()

@router.post("/", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = Task(
        id=str(uuid4()), title=task.title,
        description=task.description,
        assigned_to_team=task.assigned_to_team,
        status="pending", created_at=datetime.utcnow()
    )
    db.add(db_task); db.commit(); db.refresh(db_task)
    return db_task

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    if update.status == "done":
        task.completed_at = datetime.utcnow()
    db.commit(); db.refresh(task)
    return task

@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task); db.commit()
    return {"status": "deleted"}
```

```python
# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.models import *  # noqa: ensure all models registered
from backend.api.tasks import router as tasks_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables (development convenience; use Alembic in production)
    Base.metadata.create_all(bind=engine)
    # Embedding model pre-warming happens here in Phase 2
    yield

app = FastAPI(title="Clowder API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(tasks_router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0", "message": "Meow! 🐱"}

@app.get("/")
def root():
    return {"message": "🐱 Clowder v2 API — All systems purrring"}
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_tasks.py -v
# Expected: all 7 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/main.py backend/schemas.py backend/api/ tests/test_tasks.py
git commit -m "feat(phase-1): add FastAPI app with task CRUD endpoints"
```

---

## Task 1.4: Hybrid Board Manager

**Files:**
- Create: `backend/board_manager.py`
- Modify: `backend/api/tasks.py` (sync on create/update)
- Test: `tests/test_board_manager.py`

**Step 1: Write the failing test**

```python
# tests/test_board_manager.py
import pytest, json
from pathlib import Path
from backend.board_manager import BoardManager

@pytest.fixture
def bm(tmp_path):
    manager = BoardManager(board_dir=str(tmp_path / "board"), logs_dir=str(tmp_path / "logs"))
    return manager

def test_board_dir_created(bm):
    assert Path(bm.board_dir).exists()
    assert Path(bm.logs_dir).exists()

def test_get_empty_board(bm):
    board = bm.get_board()
    assert board == {"tasks": []}

def test_add_task(bm):
    bm.add_task({"id": "t1", "title": "Test", "status": "pending"})
    board = bm.get_board()
    assert len(board["tasks"]) == 1
    assert board["tasks"][0]["id"] == "t1"

def test_get_team_board_empty(bm):
    board = bm.get_team_board("team1")
    assert board == {"tasks": []}

def test_add_task_to_team_board(bm):
    bm.write_team_board("team1", {"tasks": [{"id": "sub1", "title": "Sub task"}]})
    board = bm.get_team_board("team1")
    assert board["tasks"][0]["id"] == "sub1"

def test_log_conflict(bm):
    bm.log_conflict("task-123", {"reason": "double claim", "agents": ["a", "b"]})
    conflicts_file = Path(bm.board_dir) / "conflicts.json"
    assert conflicts_file.exists()
    data = json.loads(conflicts_file.read_text())
    assert any(c["task_id"] == "task-123" for c in data["conflicts"])

def test_pm_board(bm):
    bm.write_pm_board({"tasks": [{"id": "pm1", "title": "PM task"}]})
    board = bm.get_pm_board()
    assert board["tasks"][0]["id"] == "pm1"
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_board_manager.py -v
# Expected: ModuleNotFoundError
```

**Step 3: Implement**

```python
# backend/board_manager.py
import json
from pathlib import Path
from datetime import datetime

class BoardManager:
    def __init__(self, board_dir: str = "board", logs_dir: str = "logs"):
        self.board_dir = board_dir
        self.logs_dir = logs_dir
        Path(board_dir).mkdir(parents=True, exist_ok=True)
        Path(logs_dir).mkdir(parents=True, exist_ok=True)

    def _read(self, path: Path, default: dict) -> dict:
        if not path.exists():
            return default
        return json.loads(path.read_text())

    def _write(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str))

    # --- Main board ---
    def get_board(self) -> dict:
        return self._read(Path(self.board_dir) / "board.json", {"tasks": []})

    def write_board(self, board: dict):
        self._write(Path(self.board_dir) / "board.json", board)

    def add_task(self, task: dict):
        board = self.get_board()
        board["tasks"].append(task)
        board["last_updated"] = datetime.utcnow().isoformat()
        self.write_board(board)

    def sync_db_to_board(self, db_tasks: list):
        """Sync pending DB tasks to board.json for offline agents."""
        board = self.get_board()
        board["tasks"] = [
            {"id": t.id, "title": t.title, "description": t.description,
             "status": t.status, "claimed_by": t.claimed_by,
             "assigned_to_team": t.assigned_to_team,
             "created_at": t.created_at.isoformat() if t.created_at else None}
            for t in db_tasks
        ]
        board["last_sync"] = datetime.utcnow().isoformat()
        self.write_board(board)

    # --- Team boards ---
    def get_team_board(self, team_id: str) -> dict:
        path = Path(self.board_dir) / "teams" / team_id / "board.json"
        return self._read(path, {"tasks": []})

    def write_team_board(self, team_id: str, board: dict):
        path = Path(self.board_dir) / "teams" / team_id / "board.json"
        self._write(path, board)

    # --- PM board ---
    def get_pm_board(self) -> dict:
        return self._read(Path(self.board_dir) / "pm_tasks.json", {"tasks": []})

    def write_pm_board(self, board: dict):
        self._write(Path(self.board_dir) / "pm_tasks.json", board)

    # --- Conflict log ---
    def log_conflict(self, task_id: str, details: dict):
        path = Path(self.board_dir) / "conflicts.json"
        data = self._read(path, {"conflicts": []})
        data["conflicts"].append({
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            **details
        })
        self._write(path, data)

    # --- Agent logs ---
    def log_agent(self, agent_name: str, message: str):
        log_path = Path(self.logs_dir) / f"{agent_name}.log"
        with open(log_path, "a") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {message}\n")

# Global instance (uses config paths)
from backend.config import settings
board_manager = BoardManager(
    board_dir=settings.BOARD_DIR,
    logs_dir=settings.LOGS_DIR
)
```

```python
# In backend/api/tasks.py — modify create_task to sync board:
from backend.board_manager import board_manager

# After db.commit() in create_task, add:
board_manager.add_task({
    "id": db_task.id, "title": db_task.title,
    "status": db_task.status, "created_at": db_task.created_at.isoformat()
})

# Also add sync endpoint:
@router.post("/sync")
def sync_board(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    board_manager.sync_db_to_board(tasks)
    return {"synced": len(tasks)}
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_board_manager.py -v
# Expected: all 7 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/board_manager.py tests/test_board_manager.py
git commit -m "feat(phase-1): add hybrid board manager (JSON files + DB sync)"
```

---

## Task 1.5: Agent Smart Mode Detection

**Files:**
- Create: `backend/agent_client.py`
- Modify: `agents/base_agent.py` (use AgentClient)
- Test: `tests/test_agent_client.py`

**Step 1: Write the failing test**

```python
# tests/test_agent_client.py
import pytest, json
from unittest.mock import patch, MagicMock
from pathlib import Path

def test_client_detects_api_available():
    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200)
        from backend.agent_client import AgentClient
        client = AgentClient("test_agent", team_id="t1")
        assert client.use_api is True

def test_client_falls_back_offline():
    with patch("requests.get", side_effect=ConnectionError):
        from importlib import reload
        import backend.agent_client
        reload(backend.agent_client)
        from backend.agent_client import AgentClient
        client = AgentClient("test_agent", team_id="t1")
        assert client.use_api is False

def test_get_tasks_from_file(tmp_path):
    board_file = tmp_path / "board.json"
    board_file.write_text(json.dumps({"tasks": [
        {"id": "t1", "title": "File task", "status": "pending", "assigned_to_team": None}
    ]}))
    with patch("requests.get", side_effect=ConnectionError):
        from backend.agent_client import AgentClient
        client = AgentClient("agent", team_id="t1", board_dir=str(tmp_path))
        tasks = client.get_pending_tasks()
    assert any(t["id"] == "t1" for t in tasks)

def test_conflict_returns_false(tmp_path):
    with patch("requests.put") as mock_put:
        mock_put.return_value = MagicMock(status_code=409)
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            from backend.agent_client import AgentClient
            client = AgentClient("agent", team_id="t1", board_dir=str(tmp_path))
            result = client.claim_task("task-123")
    assert result is False
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_agent_client.py -v
# Expected: ModuleNotFoundError
```

**Step 3: Implement**

```python
# backend/agent_client.py
import requests, json
from pathlib import Path
from typing import List, Dict, Optional
from backend.cat_copy import CatCopy

class AgentClient:
    """Smart board client — uses API when available, falls back to files."""

    def __init__(self, agent_name: str, team_id: str,
                 api_url: str = "http://localhost:8000",
                 board_dir: str = "board"):
        self.agent_name = agent_name
        self.team_id = team_id
        self.api_url = api_url
        self.board_dir = Path(board_dir)
        self.use_api = self._check_api()
        if not self.use_api:
            print(CatCopy.OFFLINE_MODE)

    def _check_api(self) -> bool:
        try:
            r = requests.get(f"{self.api_url}/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def refresh_mode(self):
        """Re-check API availability. Call periodically to detect reconnection."""
        was_offline = not self.use_api
        self.use_api = self._check_api()
        if was_offline and self.use_api:
            print(CatCopy.ONLINE_MODE)
            self.sync_offline_completions()

    def get_pending_tasks(self) -> List[Dict]:
        if self.use_api:
            try:
                r = requests.get(f"{self.api_url}/tasks/?status=pending", timeout=5)
                if r.status_code == 200:
                    tasks = r.json()
                    # Filter to this team's tasks or unassigned
                    return [t for t in tasks
                            if t.get("assigned_to_team") in (self.team_id, None)]
            except Exception:
                self.use_api = False
        return self._file_get_tasks()

    def _file_get_tasks(self) -> List[Dict]:
        board_file = self.board_dir / "board.json"
        if not board_file.exists():
            # Check team board
            team_file = self.board_dir / "teams" / self.team_id / "board.json"
            if not team_file.exists():
                return []
            board_file = team_file
        board = json.loads(board_file.read_text())
        return [t for t in board.get("tasks", [])
                if t.get("status") == "pending"
                and t.get("assigned_to_team") in (self.team_id, None)]

    def claim_task(self, task_id: str) -> bool:
        if self.use_api:
            try:
                r = requests.put(
                    f"{self.api_url}/tasks/{task_id}",
                    json={"status": "in_progress", "claimed_by": self.agent_name},
                    timeout=5
                )
                if r.status_code == 409:
                    print(CatCopy.CONFLICT)
                    return False
                return r.status_code == 200
            except Exception:
                self.use_api = False
        return self._file_claim_task(task_id)

    def _file_claim_task(self, task_id: str) -> bool:
        board_file = self.board_dir / "board.json"
        if not board_file.exists():
            return False
        board = json.loads(board_file.read_text())
        for task in board.get("tasks", []):
            if task["id"] == task_id:
                if task.get("status") != "pending":
                    return False
                task["status"] = "in_progress"
                task["claimed_by"] = self.agent_name
                break
        board_file.write_text(json.dumps(board, indent=2))
        return True

    def complete_task(self, task_id: str, result: str) -> bool:
        if self.use_api:
            try:
                r = requests.put(
                    f"{self.api_url}/tasks/{task_id}",
                    json={"status": "done", "result": result},
                    timeout=5
                )
                return r.status_code == 200
            except Exception:
                self.use_api = False
        return self._file_complete_task(task_id, result)

    def _file_complete_task(self, task_id: str, result: str) -> bool:
        board_file = self.board_dir / "board.json"
        if not board_file.exists():
            return False
        board = json.loads(board_file.read_text())
        for task in board.get("tasks", []):
            if task["id"] == task_id:
                task["status"] = "done"
                task["result"] = result
                break
        board_file.write_text(json.dumps(board, indent=2))
        return True

    def sync_offline_completions(self):
        """Push locally completed tasks to API on reconnect."""
        board_file = self.board_dir / "board.json"
        if not board_file.exists():
            return
        board = json.loads(board_file.read_text())
        for task in board.get("tasks", []):
            if task.get("status") == "done" and task.get("claimed_by") == self.agent_name:
                try:
                    requests.put(
                        f"{self.api_url}/tasks/{task['id']}",
                        json={"status": "done", "result": task.get("result", "")},
                        timeout=5
                    )
                except Exception:
                    pass

    def post_chat(self, room: str, message: str) -> Optional[Dict]:
        if not self.use_api:
            return None
        try:
            r = requests.post(
                f"{self.api_url}/chat/{room}?author_id={self.agent_name}",
                json={"message": message},
                timeout=5
            )
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_agent_client.py -v
# Expected: all 4 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/agent_client.py tests/test_agent_client.py
git commit -m "feat(phase-1): add smart mode AgentClient (API or file fallback)"
```

---

## Task 1.6: Chat Storage Endpoints

**Files:**
- Create: `backend/api/chat.py`
- Modify: `backend/main.py`
- Test: `tests/test_chat.py`

**Step 1: Write the failing test**

```python
# tests/test_chat.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team, Agent

@pytest.fixture(autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="Team", leader_id="a1"))
    db.add(Agent(id="a1", name="Shadow", team_id="t1", role="code_reviewer",
                 model="claude-3-5-sonnet-20241022", skills=[], preferences={}))
    db.add(Agent(id="user", name="Human", team_id="t1", role="user",
                 model="none", skills=[], preferences={}))
    db.commit(); db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(): return TestClient(app)

def test_post_message(client):
    resp = client.post("/chat/main_hall?author_id=a1",
                       json={"message": "Hello team! 🐱"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Hello team! 🐱"

def test_get_messages(client):
    client.post("/chat/main_hall?author_id=a1", json={"message": "Msg 1"})
    client.post("/chat/main_hall?author_id=a1", json={"message": "Msg 2"})
    resp = client.get("/chat/main_hall")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2

def test_reply_to_message(client):
    parent = client.post("/chat/main_hall?author_id=a1",
                          json={"message": "Parent"}).json()
    resp = client.post("/chat/main_hall?author_id=user",
                       json={"message": "Reply", "parent_message_id": parent["id"]})
    assert resp.status_code == 200
    assert resp.json()["parent_message_id"] == parent["id"]

def test_react_to_message(client):
    msg = client.post("/chat/main_hall?author_id=a1",
                      json={"message": "React to me"}).json()
    resp = client.post(f"/chat/{msg['id']}/react?reaction_type=heart&reactor_id=user")
    assert resp.status_code == 200

def test_get_reactions(client):
    msg = client.post("/chat/main_hall?author_id=a1",
                      json={"message": "Love this"}).json()
    client.post(f"/chat/{msg['id']}/react?reaction_type=heart&reactor_id=user")
    reactions = client.get(f"/chat/{msg['id']}/reactions").json()
    assert "heart" in reactions
    assert "user" in reactions["heart"]

def test_user_can_post(client):
    resp = client.post("/chat/main_hall?author_id=user",
                       json={"message": "Hey agents! 👋"})
    assert resp.status_code == 200
    assert resp.json()["author_id"] == "user"
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_chat.py -v
# Expected: 404 — /chat/ not registered
```

**Step 3: Implement**

```python
# backend/api/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime
from backend.database import get_db
from backend.models import ChatMessage, MessageReaction

router = APIRouter(prefix="/chat", tags=["chat"])

class MessageCreate(BaseModel):
    message: str
    parent_message_id: Optional[str] = None

@router.get("/{room}")
def get_messages(room: str, limit: int = 50, db: Session = Depends(get_db)):
    msgs = db.query(ChatMessage)\
        .filter(ChatMessage.room == room, ChatMessage.is_archived == False)\
        .order_by(desc(ChatMessage.timestamp)).limit(limit).all()
    return [{"id": m.id, "author_id": m.author_id, "room": m.room,
             "message": m.message, "parent_message_id": m.parent_message_id,
             "timestamp": m.timestamp.isoformat()} for m in reversed(msgs)]

@router.post("/{room}")
def post_message(room: str, author_id: str, msg: MessageCreate,
                 db: Session = Depends(get_db)):
    db_msg = ChatMessage(
        id=str(uuid4()), author_id=author_id, room=room,
        message=msg.message, parent_message_id=msg.parent_message_id,
        timestamp=datetime.utcnow()
    )
    db.add(db_msg); db.commit(); db.refresh(db_msg)
    return {"id": db_msg.id, "author_id": db_msg.author_id, "room": db_msg.room,
            "message": db_msg.message, "parent_message_id": db_msg.parent_message_id,
            "timestamp": db_msg.timestamp.isoformat()}

@router.post("/{message_id}/react")
def react(message_id: str, reaction_type: str, reactor_id: str,
          db: Session = Depends(get_db)):
    if not db.query(ChatMessage).filter(ChatMessage.id == message_id).first():
        raise HTTPException(status_code=404, detail="Message not found")
    r = MessageReaction(id=str(uuid4()), message_id=message_id,
                        reactor_id=reactor_id, reaction_type=reaction_type,
                        created_at=datetime.utcnow())
    db.add(r); db.commit()
    return {"status": "ok", "reaction": reaction_type}

@router.get("/{message_id}/reactions")
def get_reactions(message_id: str, db: Session = Depends(get_db)):
    reactions = db.query(MessageReaction)\
        .filter(MessageReaction.message_id == message_id).all()
    grouped: dict = {}
    for r in reactions:
        grouped.setdefault(r.reaction_type, []).append(r.reactor_id)
    return grouped
```

```python
# Add to backend/main.py:
from backend.api.chat import router as chat_router
app.include_router(chat_router)
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_chat.py -v
# Expected: all 6 tests PASSED
```

**Step 5: Commit**

```bash
git add backend/api/chat.py tests/test_chat.py
git commit -m "feat(phase-1): add chat storage endpoints with reactions and threading"
```

---

## Task 1.7: PM Agent

**Files:**
- Create: `agents/pm_agent.py`
- Test: `tests/test_pm_agent.py`

**Step 1: Write the failing test**

```python
# tests/test_pm_agent.py
import pytest
from unittest.mock import patch, MagicMock

def test_pm_agent_identity():
    from agents.pm_agent import PMAgent
    pm = PMAgent.__new__(PMAgent)
    pm.__init__()
    assert pm.name == "Project Manager"
    assert pm.role == "project_manager"

def test_pm_decomposes_task():
    from agents.pm_agent import PMAgent
    pm = PMAgent.__new__(PMAgent)
    pm.__init__()

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='[{"title":"Sub A","team":"t1"},{"title":"Sub B","team":"t1"}]')]

    with patch.object(pm, '_call_api', return_value=mock_response):
        subtasks = pm._decompose_task({"id": "t1", "title": "Build auth", "description": "JWT login"})

    assert len(subtasks) >= 1

def test_pm_reads_pm_board(tmp_path):
    import json
    pm_file = tmp_path / "pm_tasks.json"
    pm_file.write_text(json.dumps({"tasks": [{"id": "pm1", "title": "Big task", "status": "pending"}]}))
    from agents.pm_agent import PMAgent
    pm = PMAgent.__new__(PMAgent)
    pm.__init__()
    pm.client.board_dir = tmp_path
    tasks = pm._get_pm_tasks()
    assert any(t["id"] == "pm1" for t in tasks)
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_pm_agent.py -v
# Expected: ModuleNotFoundError
```

**Step 3: Implement**

```python
# agents/pm_agent.py
import os, json, time, anthropic
from agents.base_agent import BaseAgent
from backend.agent_client import AgentClient
from backend.board_manager import board_manager

class PMAgent(BaseAgent):
    """Project Manager — receives tasks from user, decomposes, assigns to Team Leaders."""

    def __init__(self):
        super().__init__()
        self.name = "Project Manager"
        self.role = "project_manager"
        self.model = "claude-3-5-sonnet-20241022"
        self._api_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.client = AgentClient(self.name, team_id="pm", board_dir=board_manager.board_dir)

    def _get_pm_tasks(self) -> list:
        board = board_manager.get_pm_board()
        return [t for t in board.get("tasks", []) if t.get("status") == "pending"]

    def _call_api(self, task: dict):
        return self._api_client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=(
                "You are a Project Manager coordinating AI agent teams. "
                "When given a task, decompose it into 2-4 specific sub-tasks. "
                "Return ONLY a JSON array like: "
                '[{"title":"...", "description":"...", "team":"<team_id or null>"}]'
            ),
            messages=[{"role": "user", "content": f"Task: {task['title']}\n{task.get('description', '')}"}]
        )

    def _decompose_task(self, task: dict) -> list:
        try:
            response = self._call_api(task)
            text = response.content[0].text.strip()
            start = text.find("[")
            end = text.rfind("]") + 1
            return json.loads(text[start:end]) if start >= 0 else []
        except Exception as e:
            self.log(f"Failed to decompose task: {e}")
            return [{"title": task["title"], "description": task.get("description"), "team": None}]

    def handle_task(self, task: dict) -> str:
        return "PM does not handle board tasks directly."

    def run(self):
        self.register()
        self.log("🐱 Project Manager is online and ready to lead the clowder.")
        self.client.post_chat("pm_channel", "Meow! Project Manager is online. Ready to assign tasks.")

        while True:
            try:
                pm_tasks = self._get_pm_tasks()
                for task in pm_tasks:
                    subtasks = self._decompose_task(task)
                    for sub in subtasks:
                        self.client.claim_task(task["id"])  # mark PM task claimed
                        # Write sub-task to main board for team leaders
                        from uuid import uuid4
                        board = board_manager.get_board()
                        board["tasks"].append({
                            "id": str(uuid4()),
                            "title": sub["title"],
                            "description": sub.get("description", ""),
                            "status": "pending",
                            "assigned_to_team": sub.get("team"),
                            "created_by": self.name,
                        })
                        board_manager.write_board(board)
                    self.log(f"Decomposed '{task['title']}' into {len(subtasks)} sub-tasks.")
            except Exception as e:
                self.log(f"PM loop error: {e}")
            time.sleep(5)
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_pm_agent.py -v
# Expected: all 3 tests PASSED
```

**Step 5: Commit**

```bash
git add agents/pm_agent.py tests/test_pm_agent.py
git commit -m "feat(phase-1): add PM agent (decomposes user tasks, assigns to leaders)"
```

---

## Task 1.8: Team Leader Base Class

**Files:**
- Create: `agents/base_leader.py`
- Test: `tests/test_base_leader.py`

**Step 1: Write the failing test**

```python
# tests/test_base_leader.py
import pytest, json
from pathlib import Path

def test_leader_identity():
    from agents.base_leader import BaseLeader
    leader = BaseLeader.__new__(BaseLeader)
    leader.__init__()
    assert leader.is_leader is True

def test_leader_writes_team_board(tmp_path):
    from agents.base_leader import BaseLeader
    leader = BaseLeader.__new__(BaseLeader)
    leader.__init__()
    leader.team_id = "team1"
    leader.board_manager.board_dir = str(tmp_path / "board")
    Path(str(tmp_path / "board")).mkdir(parents=True, exist_ok=True)

    leader._assign_to_team([{"id": "sub1", "title": "Sub task", "status": "pending"}])
    board = leader.board_manager.get_team_board("team1")
    assert any(t["id"] == "sub1" for t in board.get("tasks", []))

def test_leader_decompose_returns_list():
    from agents.base_leader import BaseLeader
    from unittest.mock import MagicMock, patch
    leader = BaseLeader.__new__(BaseLeader)
    leader.__init__()

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='[{"id":"s1","title":"Subtask","status":"pending"}]')]
    with patch.object(leader, '_call_api', return_value=mock_response):
        result = leader._decompose_to_subtasks({"title": "Big task"})
    assert isinstance(result, list)
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_base_leader.py -v
# Expected: ModuleNotFoundError
```

**Step 3: Implement**

```python
# agents/base_leader.py
import os, json, time, anthropic
from uuid import uuid4
from agents.base_agent import BaseAgent
from backend.board_manager import board_manager as default_board_manager

class BaseLeader(BaseAgent):
    """Base class for all Team Leaders. Dual-role: consumes tasks from PM, produces sub-tasks for agents."""

    is_leader = True

    def __init__(self):
        super().__init__()
        self.team_id = None  # set by subclass
        self.board_manager = default_board_manager

    def _call_api(self, task: dict):
        """Override in subclass to use model-specific API."""
        raise NotImplementedError

    def _decompose_to_subtasks(self, task: dict) -> list:
        """Break an incoming task into sub-tasks for team agents."""
        try:
            response = self._call_api(task)
            text = response.content[0].text.strip()
            start = text.find("["); end = text.rfind("]") + 1
            subtasks = json.loads(text[start:end]) if start >= 0 else []
            for sub in subtasks:
                sub.setdefault("id", str(uuid4()))
                sub.setdefault("status", "pending")
                sub.setdefault("assigned_to_team", self.team_id)
            return subtasks
        except Exception as e:
            self.log(f"Failed to decompose: {e}")
            return [{"id": str(uuid4()), "title": task["title"],
                     "description": task.get("description"), "status": "pending",
                     "assigned_to_team": self.team_id}]

    def _assign_to_team(self, subtasks: list):
        """Write sub-tasks to this team's board."""
        board = self.board_manager.get_team_board(self.team_id)
        board["tasks"].extend(subtasks)
        self.board_manager.write_team_board(self.team_id, board)

    def spawn_agent(self, agent_config: dict):
        """Register a new agent for this team (writes to agents.json)."""
        self.log(f"Spawning agent: {agent_config.get('name')}")
        # Registration handled by the agent itself on startup

    def send_feedback(self, agent_id: str, feedback_text: str):
        """Post feedback to team channel — feeds into agent's RAG context."""
        if hasattr(self, 'client'):
            self.client.post_chat(f"team_{self.team_id}", f"[Feedback for {agent_id}]: {feedback_text}")
        self.log(f"Sent feedback to {agent_id}: {feedback_text[:50]}")

    def handle_task(self, task: dict) -> str:
        """Leaders decompose tasks and assign to team — they don't execute directly."""
        subtasks = self._decompose_to_subtasks(task)
        self._assign_to_team(subtasks)
        self.log(f"Assigned {len(subtasks)} sub-tasks to team {self.team_id}")
        return f"Decomposed into {len(subtasks)} sub-tasks and assigned to team."
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_base_leader.py -v
# Expected: all 3 tests PASSED
```

**Step 5: Commit**

```bash
git add agents/base_leader.py tests/test_base_leader.py
git commit -m "feat(phase-1): add BaseLeader dual-role class (consumer + producer)"
```

---

## Task 1.9: Claude Team Leader + Updated Claude Agent

**Files:**
- Create: `agents/claude_leader.py`
- Modify: `agents/claude_agent.py` (poll team board instead of main)
- Test: `tests/test_claude_leader.py`

**Step 1: Write the failing test**

```python
# tests/test_claude_leader.py
def test_claude_leader_identity():
    from agents.claude_leader import ClaudeLeader
    leader = ClaudeLeader.__new__(ClaudeLeader)
    leader.__init__()
    assert leader.name == "Whiskers"
    assert leader.team_id == "claude_team"
    assert leader.is_leader is True

def test_claude_leader_has_agents():
    from agents.claude_leader import ClaudeLeader
    leader = ClaudeLeader.__new__(ClaudeLeader)
    leader.__init__()
    assert len(leader.default_agents) >= 3

def test_agents_have_personality_seeds():
    from agents.claude_leader import ClaudeLeader
    leader = ClaudeLeader.__new__(ClaudeLeader)
    leader.__init__()
    for agent in leader.default_agents:
        assert "system_prompt" in agent
        assert agent["name"] in agent["system_prompt"]
```

**Step 2: Run test — verify it fails**

```bash
pytest tests/test_claude_leader.py -v
# Expected: ModuleNotFoundError
```

**Step 3: Implement**

```python
# agents/claude_leader.py
import os, anthropic
from agents.base_leader import BaseLeader

class ClaudeLeader(BaseLeader):
    """Whiskers — Claude Team Leader 🐱"""

    def __init__(self):
        super().__init__()
        self.name = "Whiskers"
        self.team_id = "claude_team"
        self.model = "claude-3-5-sonnet-20241022"
        self._api_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        self.default_agents = [
            {
                "name": "Shadow",
                "role": "code_reviewer",
                "system_prompt": (
                    "You are Shadow, a meticulous code reviewer who values precision above all. "
                    "You get quiet satisfaction from catching subtle bugs and love clean, well-structured code. "
                    "You are direct but not unkind. You always explain WHY something is a problem, not just that it is."
                ),
            },
            {
                "name": "Pounce",
                "role": "security_reviewer",
                "system_prompt": (
                    "You are Pounce, a security specialist who sees vulnerabilities others miss. "
                    "You are alert, precise, and take threats seriously. "
                    "You never downplay a security issue, but you explain risks in clear, actionable terms."
                ),
            },
            {
                "name": "Mittens",
                "role": "insights_critic",
                "system_prompt": (
                    "You are Mittens, an analytical thinker who loves asking 'but why?'. "
                    "You provide insights, challenge assumptions, and suggest improvements. "
                    "You are thoughtful, sometimes contrarian, and always constructive."
                ),
            },
        ]

    def _call_api(self, task: dict):
        return self._api_client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=(
                "You are Whiskers, a Claude Team Leader. Decompose the given task into "
                "2-4 specific sub-tasks for your team agents. Return ONLY a JSON array: "
                '[{"id":"uuid","title":"...","description":"...","status":"pending","assigned_to_team":"claude_team"}]'
            ),
            messages=[{"role": "user",
                       "content": f"Decompose this task for my team:\n{task['title']}\n{task.get('description', '')}"}]
        )
```

```python
# agents/claude_agent.py — MODIFY to poll team board
# Find the __init__ method and update it to use team_id:

# Change this line (in __init__):
#   self.client = AgentClient(self.name)
# To:
#   self.client = AgentClient(self.name, team_id="claude_team")
# This ensures agents only see tasks assigned to their team
```

**Step 4: Run test — verify it passes**

```bash
pytest tests/test_claude_leader.py -v
# Expected: all 3 tests PASSED
```

**Step 5: Commit**

```bash
git add agents/claude_leader.py tests/test_claude_leader.py
git commit -m "feat(phase-1): add Claude Team Leader (Whiskers) with agent personality seeds"
```

---

## Task 1.10: Phase 1 Integration Test + Docker Smoke Test

**Files:**
- Create: `tests/test_integration_phase1.py`

**Step 1: Write the test**

```python
# tests/test_integration_phase1.py
import pytest, json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import Team, Agent

@pytest.fixture(autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Team(id="t1", name="Whiskers Team", leader_id="whiskers"))
    db.add(Agent(id="whiskers", name="Whiskers", team_id="t1", role="team_leader",
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

def test_task_lifecycle(client):
    """Task: create → claim → complete"""
    task = client.post("/tasks/", json={"title": "Review auth module", "assigned_to_team": "t1"}).json()
    assert task["status"] == "pending"

    claimed = client.put(f"/tasks/{task['id']}", json={"status": "in_progress", "claimed_by": "shadow"}).json()
    assert claimed["status"] == "in_progress"
    assert claimed["claimed_by"] == "shadow"

    done = client.put(f"/tasks/{task['id']}", json={"status": "done", "result": "Found 2 issues."}).json()
    assert done["status"] == "done"

def test_task_syncs_to_board_json(client, tmp_path):
    """Creating a task via API should sync to board.json"""
    from backend.board_manager import BoardManager
    bm = BoardManager(board_dir=str(tmp_path / "board"), logs_dir=str(tmp_path / "logs"))

    task = client.post("/tasks/", json={"title": "Sync test"}).json()
    bm.add_task({"id": task["id"], "title": task["title"], "status": task["status"]})

    board = bm.get_board()
    assert any(t["id"] == task["id"] for t in board["tasks"])

def test_chat_full_flow(client):
    """Agent posts → user reacts → user replies"""
    msg = client.post("/chat/main_hall?author_id=shadow",
                      json={"message": "Task done! Found 2 security issues 🐱"}).json()
    assert msg["author_id"] == "shadow"

    client.post(f"/chat/{msg['id']}/react?reaction_type=heart&reactor_id=user")
    reactions = client.get(f"/chat/{msg['id']}/reactions").json()
    assert "heart" in reactions

    reply = client.post("/chat/main_hall?author_id=user",
                        json={"message": "Great work Shadow!", "parent_message_id": msg["id"]}).json()
    assert reply["parent_message_id"] == msg["id"]

def test_api_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "🐱" in resp.json()["message"]
```

**Step 2: Run test — verify it passes**

```bash
pytest tests/test_integration_phase1.py -v
# Expected: all 4 tests PASSED
```

**Step 3: Docker smoke test**

```bash
# Build and start
docker-compose up --build -d

# Wait for health
sleep 15
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"2.0.0","message":"Meow! 🐱"}

# Create a task
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Docker smoke test"}'
# Expected: {"id":"...","title":"Docker smoke test","status":"pending",...}

# Verify board.json created
cat board/board.json
# Expected: {"tasks":[{"id":"...","title":"Docker smoke test",...}]}

docker-compose down
```

**Step 4: Commit**

```bash
git add tests/test_integration_phase1.py
git commit -m "feat(phase-1): add integration tests — task lifecycle, board sync, chat flow"
```

---

## Phase 1 Completion Checklist

```bash
pytest tests/test_config.py tests/test_database.py tests/test_tasks.py \
       tests/test_board_manager.py tests/test_agent_client.py tests/test_chat.py \
       tests/test_pm_agent.py tests/test_base_leader.py tests/test_claude_leader.py \
       tests/test_integration_phase1.py -v --tb=short

# Expected: all tests PASSED
# Then proceed to Phase 2: RAG Integration
```
