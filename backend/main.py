"""
backend/main.py — Kitty Collab Board v2
FastAPI application for the online backend (PostgreSQL + pgvector).

Replaces web_chat.py when the v2 stack is running.
web_chat.py continues to work unchanged for the file-based offline mode.

Start:
    uvicorn backend.main:app --host 0.0.0.0 --port 9000 --reload

Health check (used by AgentClient._probe_api):
    GET /api/health → {"status": "ok"}
"""

import datetime
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, update

from backend.config import DEBUG
from backend.database import SessionLocal, create_tables
from backend.models import Agent, ChatMessage, MessageReaction, Task, Team, TokenUsage
from backend.api.channels import router as channels_router
from backend.api.context import router as context_router
from backend.api.tasks_v2 import router as tasks_v2_router
from backend.api.trending import router as trending_router
from backend.api.ideas import router as ideas_router
from backend.api.agents import router as agents_v2_router
from backend.api.exports import router as exports_router
from backend.api.governance import router as governance_router
from backend.api.standards import router as standards_router
from backend.ws import manager


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, load embedding model."""
    await create_tables()
    from backend.embeddings import init_embedding_service
    from backend.config import EMBEDDING_MODEL
    init_embedding_service(EMBEDDING_MODEL)
    print(f"[v2] EmbeddingService loaded: {EMBEDDING_MODEL}")
    yield
    # Shutdown: nothing to clean up yet


app = FastAPI(
    title="Kitty Collab Board v2",
    version="2.0.0-phase1",
    lifespan=lifespan,
    debug=DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels_router)
app.include_router(context_router)
app.include_router(tasks_v2_router)
app.include_router(trending_router)
app.include_router(ideas_router)
app.include_router(agents_v2_router)
app.include_router(exports_router)
app.include_router(governance_router)
app.include_router(standards_router)


# ── WebSocket ──────────────────────────────────────────────────────────────────

async def _msg_reactions(db, message_id: str) -> dict:
    """Return reaction map {emoji: [reactor, ...]} for a message."""
    rows = (
        await db.execute(
            select(MessageReaction).where(MessageReaction.message_id == message_id)
        )
    ).scalars().all()
    result: dict[str, list[str]] = {}
    for r in rows:
        result.setdefault(r.reaction_type, []).append(r.reactor_id)
    return result


async def _msg_reply_count(db, message_id: str) -> int:
    """Return the number of threaded replies for a message."""
    from sqlalchemy import func as sqlfunc
    row = (
        await db.execute(
            select(sqlfunc.count(ChatMessage.id)).where(
                ChatMessage.thread_id == message_id
            )
        )
    ).scalar_one()
    return row or 0


async def _msg_dict_full(db, m: ChatMessage) -> dict:
    """Return a ChatMessage dict enriched with reactions and reply_count."""
    return {
        **_msg_dict(m),
        "reactions": await _msg_reactions(db, m.id),
        "reply_count": await _msg_reply_count(db, m.id),
    }


@app.websocket("/ws/{room}")
async def websocket_endpoint(room: str, ws: WebSocket):
    """
    Room-based WebSocket endpoint implementing the v2 WS contract.

    On connect:
      - Sends a ``connected`` ack frame with the last 20 persisted messages
        (enriched with reactions and reply counts).
      - Broadcasts a ``presence`` frame to the room.

    Supported client→server frame types:
      ``auth``      — acknowledged, no-op (token ignored in v2).
      ``message``   — persisted and broadcast as ``{type: "message", data: {...}}``.
      ``react``     — stored in DB; updated reaction map broadcast.
      ``unreact``   — removed from DB; updated reaction map broadcast.
      ``typing``    — relayed to all *other* clients in the room.
      ``ping``      — answered with ``pong``.
    """
    agent_name = "unknown"
    await manager.connect(room, ws)

    async with SessionLocal() as db:
        q = (
            select(ChatMessage)
            .where(ChatMessage.channel == room)
            .order_by(ChatMessage.timestamp.desc())
            .limit(20)
        )
        rows = (await db.execute(q)).scalars().all()
        recent = [await _msg_dict_full(db, m) for m in reversed(rows)]

    await ws.send_json({"type": "connected", "room": room, "agent": agent_name, "recent_messages": recent})

    try:
        while True:
            data = await ws.receive_json()
            frame_type = data.get("type", "message")

            if frame_type == "auth":
                agent_name = data.get("agent", agent_name) or agent_name
                # Broadcast presence to the room
                await manager.broadcast(room, {"type": "presence", "room": room, "agent": agent_name, "status": "online"})

            elif frame_type == "message":
                async with SessionLocal() as db:
                    msg = ChatMessage(
                        id=uuid.uuid4().hex[:8],
                        channel=room,
                        sender=data.get("sender", agent_name),
                        content=data.get("content", ""),
                        type=data.get("message_type", "chat"),
                        thread_id=data.get("thread_id"),
                    )
                    db.add(msg)
                    await db.commit()
                    await db.refresh(msg)
                    enriched = await _msg_dict_full(db, msg)
                # Notify thread parent of new reply count
                if msg.thread_id:
                    async with SessionLocal() as db:
                        reply_count = await _msg_reply_count(db, msg.thread_id)
                    await manager.broadcast(room, {
                        "type": "thread_reply",
                        "room": room,
                        "parent_id": msg.thread_id,
                        "reply_count": reply_count,
                        "latest_reply": enriched,
                    })
                await manager.broadcast(room, {"type": "message", "room": room, "data": enriched})

            elif frame_type in ("react", "unreact"):
                message_id = data.get("message_id", "")
                reactor = data.get("reactor", agent_name)
                reaction = data.get("reaction", "")
                if message_id and reaction:
                    async with SessionLocal() as db:
                        if frame_type == "react":
                            existing = (
                                await db.execute(
                                    select(MessageReaction).where(
                                        MessageReaction.message_id == message_id,
                                        MessageReaction.reactor_id == reactor,
                                        MessageReaction.reaction_type == reaction,
                                    )
                                )
                            ).scalar_one_or_none()
                            if not existing:
                                db.add(MessageReaction(
                                    message_id=message_id,
                                    reactor_id=reactor,
                                    reaction_type=reaction,
                                ))
                                await db.commit()
                        else:  # unreact
                            existing = (
                                await db.execute(
                                    select(MessageReaction).where(
                                        MessageReaction.message_id == message_id,
                                        MessageReaction.reactor_id == reactor,
                                        MessageReaction.reaction_type == reaction,
                                    )
                                )
                            ).scalar_one_or_none()
                            if existing:
                                await db.delete(existing)
                                await db.commit()
                        reactions = await _msg_reactions(db, message_id)
                    await manager.broadcast(room, {
                        "type": "reaction",
                        "room": room,
                        "message_id": message_id,
                        "reactions": reactions,
                    })

            elif frame_type == "typing":
                # Relay to everyone in the room (including sender — client ignores own)
                await manager.broadcast(room, {
                    "type": "typing",
                    "room": room,
                    "agent": data.get("agent", agent_name),
                    "is_typing": data.get("is_typing", False),
                })

            elif frame_type == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(room, ws)
        # Notify room of offline presence
        await manager.broadcast(room, {"type": "presence", "room": room, "agent": agent_name, "status": "offline"})


# ── Pydantic request models ────────────────────────────────────────────────────

class ClaimRequest(BaseModel):
    agent_name: str
    claimed_at: str

class CompleteRequest(BaseModel):
    agent_name: str
    result: str
    completed_at: str | None = None

class PostMessageRequest(BaseModel):
    content: str
    sender: str
    type: str = "chat"
    thread_id: str | None = None
    metadata: dict | None = None

class RegisterAgentRequest(BaseModel):
    name: str
    role: str = "general"
    team: str | None = None
    model: str = "unknown"

class LogTokensRequest(BaseModel):
    agent: str
    input_tokens: int
    output_tokens: int
    model: str

class RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5

class ConflictRequest(BaseModel):
    task_id: str
    local_agent: str
    remote_agent: str | None = None
    local_result: str = ""
    remote_status: str | None = None

class CreateTeamRequest(BaseModel):
    name: str
    leader_id: str | None = None

class PostChatRequest(BaseModel):
    sender: str
    content: str
    type: str = "chat"
    thread_id: str | None = None

class V2RAGSearchRequest(BaseModel):
    query: str
    top_k: int = 5


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0-phase1"}


# ── Tasks ─────────────────────────────────────────────────────────────────────

@app.get("/api/tasks")
async def get_tasks(team_id: str | None = None):
    async with SessionLocal() as db:
        q = select(Task)
        if team_id:
            q = q.where(Task.team_id == team_id)
        rows = (await db.execute(q)).scalars().all()
        return [_task_dict(t) for t in rows]


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    async with SessionLocal() as db:
        task = await db.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return _task_dict(task)


@app.post("/api/tasks/{task_id}/claim")
async def claim_task(task_id: str, req: ClaimRequest):
    """First-claim-wins: UPDATE WHERE status='pending', check rowcount."""
    async with SessionLocal() as db:
        result = await db.execute(
            update(Task)
            .where(Task.id == task_id, Task.status == "pending")
            .values(
                status="claimed",
                claimed_by=req.agent_name,
                claimed_at=req.claimed_at,
            )
        )
        await db.commit()
        claimed = result.rowcount == 1

        # After claiming the task, inject RAG context
        if claimed:
            try:
                from backend.rag_service import query_context
                from backend.embeddings import get_embedding_service
                task = await db.get(Task, task_id)
                if task:
                    svc = get_embedding_service()
                    context_items = await query_context(
                        session=db,
                        query_text=task.title or "",
                        encode_fn=svc.encode,
                        top_k=5,
                        agent_id=req.agent_name,
                    )
                    if context_items:
                        context_block = "\n\n---\n**Relevant context from past work:**\n"
                        for item in context_items:
                            context_block += f"- {item['content'][:200]}\n"
                        # Append to description (don't overwrite)
                        task.description = (task.description or "") + context_block
                        await db.commit()
            except Exception:
                pass  # RAG injection is best-effort, never blocks task claim

        return {"claimed": claimed}


@app.post("/api/tasks/{task_id}/complete")
async def complete_task(task_id: str, req: CompleteRequest):
    async with SessionLocal() as db:
        result = await db.execute(
            update(Task)
            .where(Task.id == task_id, Task.claimed_by == req.agent_name)
            .values(
                status="done",
                result=req.result,
                completed_at=datetime.datetime.now(),
            )
        )
        await db.commit()
        ok = result.rowcount == 1

        # After completing the task, seed result into RAG context
        if ok:
            try:
                from backend.rag_service import seed_from_task
                from backend.embeddings import get_embedding_service
                task = await db.get(Task, task_id)
                svc = get_embedding_service()
                await seed_from_task(
                    session=db,
                    task_id=task_id,
                    task_title=task.title if task else "",
                    result_text=req.result or "",
                    encode_fn=svc.encode,
                )
            except Exception:
                pass  # Seeding is best-effort, never blocks completion

        return {"ok": ok}


# ── Messages ──────────────────────────────────────────────────────────────────

@app.get("/api/channels/{channel}/messages")
async def read_messages(channel: str, limit: int = 20, type: str | None = None):
    async with SessionLocal() as db:
        q = select(ChatMessage).where(ChatMessage.channel == channel)
        if type:
            q = q.where(ChatMessage.type == type)
        q = q.order_by(ChatMessage.timestamp.desc()).limit(limit)
        rows = (await db.execute(q)).scalars().all()
        return [_msg_dict(m) for m in reversed(rows)]


@app.post("/api/channels/{channel}/messages")
async def post_message(channel: str, req: PostMessageRequest):
    async with SessionLocal() as db:
        msg = ChatMessage(
            id=uuid.uuid4().hex[:8],
            channel=channel,
            sender=req.sender,
            content=req.content,
            type=req.type,
            thread_id=req.thread_id,
            metadata_=req.metadata,
        )
        db.add(msg)
        await db.commit()
        return {"id": msg.id}


# ── Agents ────────────────────────────────────────────────────────────────────

@app.post("/api/agents/register")
async def register_agent(req: RegisterAgentRequest):
    async with SessionLocal() as db:
        existing = await db.get(Agent, req.name)
        if existing:
            existing.role = req.role
            existing.model = req.model
            existing.team = req.team
            existing.status = "online"
            existing.last_seen = datetime.datetime.now()
        else:
            db.add(Agent(
                name=req.name,
                role=req.role,
                model=req.model,
                team=req.team,
                started_at=datetime.datetime.now(),
            ))
        await db.commit()
    return {"ok": True}


@app.post("/api/agents/{name}/heartbeat")
async def heartbeat(name: str):
    async with SessionLocal() as db:
        agent = await db.get(Agent, name)
        if agent:
            agent.last_seen = datetime.datetime.now()
            await db.commit()
    return {"ok": True}


@app.get("/api/agents/{name}/profile")
async def get_agent_profile(name: str):
    async with SessionLocal() as db:
        agent = await db.get(Agent, name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {
            "name": agent.name,
            "role": agent.role,
            "model": agent.model,
            "team": agent.team,
            "status": agent.status,
            "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
        }


# ── Tokens ────────────────────────────────────────────────────────────────────

# Token rates in USD per 1M tokens (input, output)
_TOKEN_RATES: dict[str, tuple[float, float]] = {
    "claude-opus-4-6": (15.00, 75.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5-20251001": (0.25, 1.25),
    "gpt-4o": (5.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
}

@app.post("/api/tokens/log")
async def log_tokens(req: LogTokensRequest):
    rates = _TOKEN_RATES.get(req.model, (0.0, 0.0))
    cost = (req.input_tokens * rates[0] + req.output_tokens * rates[1]) / 1_000_000
    async with SessionLocal() as db:
        db.add(TokenUsage(
            agent=req.agent,
            model=req.model,
            input_tokens=req.input_tokens,
            output_tokens=req.output_tokens,
            cost_usd=cost,
        ))
        await db.commit()
    return {"agent": req.agent, "cost_usd": cost}


@app.get("/api/tokens/{agent}/budget")
@app.get("/api/v2/tokens/{agent}/budget")
async def check_budget(agent: str):
    async with SessionLocal() as db:
        rows = (await db.execute(
            select(TokenUsage).where(TokenUsage.agent == agent)
        )).scalars().all()
        total_input = sum(r.input_tokens or 0 for r in rows)
        total_output = sum(r.output_tokens or 0 for r in rows)
        total_cost = sum(r.cost_usd or 0.0 for r in rows)
    return {
        "agent": agent,
        "total_cost_usd": total_cost,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "ok": True,
    }


# ── RAG (Phase 1: stub; Phase 2: real embeddings) ─────────────────────────────

@app.post("/api/rag/search")
async def rag_search(req: RAGSearchRequest):
    """Phase 1 stub — returns empty results. Phase 2 adds pgvector similarity search."""
    return []


# ── Conflicts ─────────────────────────────────────────────────────────────────

_conflicts: list[dict] = []  # In-memory for Phase 1; Phase 2 moves this to DB

@app.post("/api/conflicts")
async def log_conflict(req: ConflictRequest):
    _conflicts.append({
        **req.model_dump(),
        "logged_at": datetime.datetime.now().isoformat(),
    })
    return {"ok": True}

@app.get("/api/conflicts")
async def get_conflicts():
    return _conflicts


# ── v2 Teams ──────────────────────────────────────────────────────────────────

@app.post("/api/v2/teams")
async def v2_create_team(req: CreateTeamRequest):
    async with SessionLocal() as db:
        team = Team(
            id=uuid.uuid4().hex[:16],
            name=req.name,
            leader_id=req.leader_id,
        )
        db.add(team)
        await db.commit()
        return _team_dict(team)


@app.get("/api/v2/teams")
async def v2_list_teams():
    async with SessionLocal() as db:
        rows = (await db.execute(select(Team))).scalars().all()
        return [_team_dict(t) for t in rows]


@app.get("/api/v2/teams/{team_id}")
async def v2_get_team(team_id: str):
    async with SessionLocal() as db:
        team = await db.get(Team, team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return _team_dict(team)


# ── v2 Chat ───────────────────────────────────────────────────────────────────

@app.post("/api/v2/chat/{room}")
async def v2_post_chat(room: str, req: PostChatRequest):
    async with SessionLocal() as db:
        msg = ChatMessage(
            id=uuid.uuid4().hex[:8],
            channel=room,
            sender=req.sender,
            content=req.content,
            type=req.type,
            thread_id=req.thread_id,
        )
        db.add(msg)
        await db.commit()
        return {"id": msg.id}


@app.get("/api/v2/chat/{room}")
async def v2_get_chat(room: str, limit: int = 50):
    async with SessionLocal() as db:
        q = (
            select(ChatMessage)
            .where(ChatMessage.channel == room)
            .order_by(ChatMessage.timestamp.desc())
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        return [_msg_dict(m) for m in reversed(rows)]


# ── v2 Agent Heartbeat ────────────────────────────────────────────────────────

@app.post("/api/v2/agents/{name}/heartbeat")
async def v2_heartbeat(name: str):
    async with SessionLocal() as db:
        agent = await db.get(Agent, name)
        if agent:
            agent.last_seen = datetime.datetime.now()
            await db.commit()
    return {"ok": True, "agent": name, "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}


# ── v2 RAG stub ───────────────────────────────────────────────────────────────

@app.post("/api/v2/rag/search")
async def v2_rag_search(req: V2RAGSearchRequest):
    """Phase 2 placeholder — returns empty results until pgvector pipeline is active."""
    return {"results": [], "note": "RAG active in Phase 2"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _task_dict(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "role": t.role,
        "team_id": t.team_id,
        "priority": t.priority,
        "priority_order": t.priority_order,
        "skills": t.skills,
        "blocked_by": t.blocked_by,
        "claimed_by": t.claimed_by,
        "claimed_at": t.claimed_at,
        "result": t.result,
        "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }

def _team_dict(t: Team) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "leader_id": t.leader_id,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }

def _msg_dict(m: ChatMessage) -> dict:
    return {
        "id": m.id,
        "channel": m.channel,
        "sender": m.sender,
        "content": m.content,
        "type": m.type,
        "thread_id": m.thread_id,
        "metadata": m.metadata_,
        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
    }
