# Clowder v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Clowder v2 (Kitty Collab Board) — a hierarchical multi-agent collaboration system with RAG context retrieval, social chat, agent profiles, and governance.

**Architecture:** 
- FastAPI backend with REST API + WebSocket for real-time chat
- PostgreSQL (pgvector) for context storage and RAG
- Hybrid data layer: local files for fast task polling, database for context/history
- Containerized via Docker Compose
- Agents use smart mode switching (API or file fallback)

**Tech Stack:** 
- Backend: FastAPI, PostgreSQL 15+ (pgvector), SQLAlchemy, Anthropic SDK, sentence-transformers
- Frontend: React/Vue (dashboard), Python curses (TUI), WebSocket client
- Deployment: Docker Compose, Python 3.11+

---

## Phase 1: Core API + Hybrid Board (Weeks 1-2)

### Task 1.1: Project Structure & Dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`

**Step 1: Update requirements.txt**

```text
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
python-dotenv==1.0.0
anthropic==0.7.1
sentence-transformers==2.2.2
pgvector==0.2.4
websockets==12.0
pydantic-settings==2.1.0
alembic==1.13.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.0
requests==2.31.0
```

**Step 2: Create backend config file**

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/clowder"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    BOARD_DIR: str = "board"
    LOGS_DIR: str = "logs"
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_MAX_CONTEXT_TOKENS: int = 2000
    RAG_RETRIEVAL_TOP_K: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Step 3: Create backend __init__.py**

```python
# backend/__init__.py
__version__ = "2.0.0"
```

**Step 4: Update docker-compose.yml**

```yaml
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
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/clowder
      API_HOST: 0.0.0.0
      API_PORT: 8000
    volumes:
      - ./board:/app/board
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
```

**Step 5: Commit** → `git add backend/ Dockerfile docker-compose.yml && git commit -m "feat(phase-1): add project structure and dependencies"`

---

### Task 1.2-1.7: [Core Database, API, Board Integration, Chat, Tests]

*(Full detailed steps for tasks 1.2 through 1.7 follow the same format as above)*

**Quick summary of Phase 1 tasks:**
- 1.2: PostgreSQL schema + migrations (models, alembic)
- 1.3: FastAPI server (main.py, schemas.py, task endpoints)
- 1.4: Hybrid board manager (JSON files + DB sync)
- 1.5: Agent smart mode detection (API or file fallback)
- 1.6: Basic chat API (messages, reactions)
- 1.7: Tests + Docker setup

**Phase 1 Deliverable:** Working API with task board, chat, and hybrid file+database storage. Agents can work offline using board.json or online via API.

---

## Phase 2: RAG Integration (Weeks 3-4)

### Task 2.1: Embedding Service Setup

**Files:**
- Create: `backend/embeddings.py`
- Create: `backend/models.py` (add embedding columns)
- Create: `alembic/versions/002_add_embeddings.py`

### Task 2.2: Context Retrieval Pipeline

**Files:**
- Create: `backend/rag_service.py`
- Create: `backend/api/rag.py`

### Task 2.3: Prompt Injection

**Files:**
- Modify: `backend/api/tasks.py` (inject context into task prompts)

### Task 2.4: Mid-Task Retrieval API

**Files:**
- Create: `backend/api/context.py` (agent request more context)

### Task 2.5: Tests & Refinement

**Files:**
- Create: `tests/test_rag.py`

---

## Phase 3: Profiles & Portability (Weeks 5-6)

### Task 3.1: Agent Profile Schema & Endpoints

**Files:**
- Create: `backend/api/agents.py`
- Modify: `backend/models.py` (profile fields)

### Task 3.2: Avatar Support (SVG)

**Files:**
- Create: `backend/storage.py` (store avatars)

### Task 3.3: Export/Import Agents

**Files:**
- Create: `backend/api/exports.py`

### Task 3.4: Web UI Profile Pages

**Files:**
- Create: `frontend/pages/AgentProfile.vue`
- Create: `frontend/pages/AgentGallery.vue`

### Task 3.5: Tests

**Files:**
- Create: `tests/test_profiles.py`

---

## Phase 4: Chat & Social (Weeks 7-8)

### Task 4.1: WebSocket Server for Real-Time Chat

**Files:**
- Modify: `backend/main.py` (add WebSocket endpoint)

### Task 4.2: Threading & Replies

**Files:**
- Modify: `backend/models.py` (parent_message_id)
- Modify: `backend/api/chat.py` (thread endpoints)

### Task 4.3: Reactions System

**Files:**
- (Already in Phase 1, enhance in Phase 4)
- Create: `backend/api/reactions.py` (advanced reactions)

### Task 4.4: Chat Archiving & Search

**Files:**
- Create: `backend/api/chat_search.py`

### Task 4.5: Trending Discussions

**Files:**
- Create: `backend/api/trending.py`

### Task 4.6: WebSocket Frontend

**Files:**
- Create: `frontend/components/ChatRoom.vue`
- Create: `frontend/components/MessageThread.vue`

### Task 4.7: Tests

**Files:**
- Create: `tests/test_chat.py`

---

## Phase 5: Governance & Escalation (Weeks 9-10)

### Task 5.1: Token Manager Agent

**Files:**
- Create: `agents/token_manager_agent.py`
- Create: `backend/api/governance.py`

### Task 5.2: Code Format/Standards Agent

**Files:**
- Create: `agents/standards_manager_agent.py`

### Task 5.3: Standards Violations Tracking

**Files:**
- Modify: `backend/models.py` (violations table)
- Create: `backend/api/standards.py`

### Task 5.4: Ideas Channel & Escalation

**Files:**
- Create: `backend/api/ideas.py`
- Modify: `backend/models.py` (ideas table)

### Task 5.5: Team Leader Meetings Interface

**Files:**
- Create: `frontend/pages/TeamLeaderMeeting.vue`

### Task 5.6: Tests

**Files:**
- Create: `tests/test_governance.py`

---

## Phase 6: Polish & Deployment (Weeks 11-12)

### Task 6.1: Web Dashboard (React/Vue)

**Files:**
- Create: `frontend/pages/Dashboard.vue`
- Create: `frontend/pages/TaskBoard.vue`
- Create: `frontend/pages/TeamView.vue`
- Create: `frontend/components/AgentCard.vue`
- Create: `frontend/components/TaskCard.vue`

### Task 6.2: Enhanced TUI

**Files:**
- Modify: `mission_control.py` (add chat, ideas, profiles)

### Task 6.3: Cat Flair & Theming

**Files:**
- Modify: All UI files (add 🐱 emojis, cat-themed colors)
- Create: `frontend/theme.css` (cat-friendly color scheme)

### Task 6.4: Documentation

**Files:**
- Create: `ARCHITECTURE.md`
- Create: `DEVELOPER_SETUP.md`
- Create: `API_REFERENCE.md`
- Create: `USER_GUIDE.md`

### Task 6.5: Agent Onboarding Flow

**Files:**
- Create: `agents/onboarding.py` (help agents register, create profiles)

### Task 6.6: Final Integration & Smoke Tests

**Files:**
- Create: `tests/test_integration.py` (end-to-end tests)

### Task 6.7: Deployment & Documentation

**Files:**
- Update: `Dockerfile` (production-ready)
- Update: `docker-compose.yml` (production settings)
- Create: `DEPLOYMENT.md`

---

## Execution Recommendation

**Plan complete and saved to `docs/plans/2026-03-08-clowder-v2-implementation.md`.**

Two execution options:

**1. Subagent-Driven (this session)**
- I dispatch fresh subagent per task
- Code review between tasks
- Fast iteration, immediate feedback
- Better for catching issues early

**2. Parallel Session (separate)**
- Open new session with executing-plans skill
- Batch multiple tasks per session
- Useful for independent work
- Better for focused, long sessions

---

**Which approach would you prefer?**

1. **Subagent-Driven** — Use `superpowers:subagent-driven-development` to dispatch agents per task
2. **Parallel Session** — Start fresh session with `superpowers:executing-plans`
3. **Hybrid** — Some tasks subagent-driven, some in parallel sessions
4. **Manual** — I provide guidance, you implement tasks