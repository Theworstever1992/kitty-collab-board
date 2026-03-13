"""
models.py — Kitty Collab Board v2
SQLAlchemy ORM models mirroring the file-based board schema.

Field names match board.json / agents.json for compatibility with meow.py.
pgvector column added to ChatMessage for RAG (Phase 2, nullable until then).
"""

import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

try:
    from pgvector.sqlalchemy import Vector
    _PGVECTOR = True
except ImportError:
    _PGVECTOR = False


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    role: Mapped[Optional[str]] = mapped_column(String(64))
    team_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium")
    priority_order: Mapped[int] = mapped_column(Integer, default=2)
    skills: Mapped[Optional[list]] = mapped_column(JSON)
    blocked_by: Mapped[Optional[list]] = mapped_column(JSON)
    claimed_by: Mapped[Optional[str]] = mapped_column(String(128))
    claimed_at: Mapped[Optional[str]] = mapped_column(String(64))
    result: Mapped[Optional[str]] = mapped_column(Text)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    __table_args__ = (
        # Index on status + team_id for fast task filtering
    )


class Agent(Base):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(128), primary_key=True)
    role: Mapped[str] = mapped_column(String(64), default="general")
    model: Mapped[str] = mapped_column(String(128), default="unknown")
    team: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="online")
    last_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    avatar_svg: Mapped[Optional[str]] = mapped_column(Text)  # max 50KB enforced at API layer
    skills: Mapped[Optional[list]] = mapped_column(JSON)
    personality_seed: Mapped[Optional[str]] = mapped_column(Text)
    hired_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    fired_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    fire_reason: Mapped[Optional[str]] = mapped_column(Text)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    channel: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(32), default="chat")
    thread_id: Mapped[Optional[str]] = mapped_column(String(64))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    # pgvector embedding — populated by Phase 2 RAG pipeline (nullable until then)
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(384) if _PGVECTOR else JSON,  # 384 dims for all-MiniLM-L6-v2
        nullable=True,
    )


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Optional[float]] = mapped_column()
    logged_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    leader_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # RAG config: what context to retrieve for this team's agents
    rag_config: Mapped[Optional[dict]] = mapped_column(JSON)


class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    status_change: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TaskEmbedding(Base):
    __tablename__ = "task_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(384) if _PGVECTOR else JSON,  # 384 dims for all-MiniLM-L6-v2
        nullable=True,
    )
    summary_text: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ContextItem(Base):
    __tablename__ = "context_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_id: Mapped[Optional[str]] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(384) if _PGVECTOR else JSON,  # 384 dims for all-MiniLM-L6-v2
        nullable=True,
    )
    tags: Mapped[Optional[list]] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MessageReaction(Base):
    __tablename__ = "message_reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    reactor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    reaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class TrendingDiscussion(Base):
    __tablename__ = "trending_discussions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    current_score: Mapped[float] = mapped_column(Float, nullable=False)
    window_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    author_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(128))
    source_message_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class IdeaVote(Base):
    __tablename__ = "idea_votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    idea_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    voter_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StandardsViolation(Base):
    __tablename__ = "standards_violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    violation_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    task_id: Mapped[Optional[str]] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    flagged_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AgentExport(Base):
    __tablename__ = "agent_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    export_format: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text)
    results_returned: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class LeaderMeeting(Base):
    __tablename__ = "leader_meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agenda: Mapped[Optional[list]] = mapped_column(JSON)
    participants: Mapped[Optional[list]] = mapped_column(JSON)
    decisions: Mapped[Optional[list]] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
