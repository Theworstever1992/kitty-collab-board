"""
main.py — Kitty Collab Board Web API
FastAPI application serving board state via REST + WebSocket.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Board directory from environment or default
BOARD_DIR = Path(
    os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent.parent / "board")
)

app = FastAPI(
    title="Kitty Collab Board API",
    description="REST + WebSocket API for Clowder multi-agent system",
    version="1.0.0"
)

# CORS - allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Pydantic models for request/response
# ------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    prompt: Optional[str] = None
    role: Optional[str] = None
    priority: str = "normal"
    skills: list[str] = []   # TASK 6021: required skills, e.g. ["python", "react"]


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    role: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    skills: Optional[list[str]] = None


# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------

def load_board() -> dict:
    """Load board.json with file locking."""
    board_file = BOARD_DIR / "board.json"
    if not board_file.exists():
        return {"tasks": []}
    try:
        return json.loads(board_file.read_text(encoding="utf-8"))
    except Exception:
        return {"tasks": []}


def save_board(board: dict):
    """Save board.json with file locking."""
    board_file = BOARD_DIR / "board.json"
    try:
        from filelock import FileLock
        lock = FileLock(str(board_file) + ".lock", timeout=10)
        with lock:
            board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
    except ImportError:
        # No filelock - save without locking
        board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")


def load_agents() -> dict:
    """Load agents.json."""
    agents_file = BOARD_DIR / "agents.json"
    if not agents_file.exists():
        return {}
    try:
        return json.loads(agents_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


# ------------------------------------------------------------------
# REST API Endpoints
# ------------------------------------------------------------------

@app.get("/")
def root():
    """Root — redirects to health."""
    return {"status": "ok", "service": "clowder-api"}


@app.get("/health")
def health_check():
    """
    Docker/K8s health check endpoint. TASK 6014.
    Returns 200 if the API is up and can read the board file.
    Returns 503 if the board directory is inaccessible.
    """
    from fastapi import Response
    import datetime

    board_file = BOARD_DIR / "board.json"
    board_readable = board_file.exists() or BOARD_DIR.exists()

    if not board_readable:
        return Response(
            content='{"status":"unhealthy","reason":"board directory not found"}',
            status_code=503,
            media_type="application/json",
        )

    return {
        "status": "healthy",
        "service": "clowder-api",
        "board_dir": str(BOARD_DIR),
        "checked_at": datetime.datetime.now().isoformat(),
    }


@app.get("/api/board")
def get_board():
    """Get full board state."""
    return load_board()


@app.get("/api/tasks")
def get_tasks(status: Optional[str] = None, role: Optional[str] = None):
    """
    Get all tasks with optional filtering.
    
    - **status**: Filter by status (pending, in_progress, done, blocked)
    - **role**: Filter by role (reasoning, code, research, summarization, general)
    """
    board = load_board()
    tasks = board.get("tasks", [])
    
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    if role:
        tasks = [t for t in tasks if t.get("role") == role]
    
    return {"tasks": tasks, "count": len(tasks)}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    """Get a specific task by ID."""
    board = load_board()
    for task in board.get("tasks", []):
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    """Create a new task."""
    import time
    import datetime
    
    board = load_board()
    
    # Priority mapping
    priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    
    new_task = {
        "id": f"task_{int(time.time())}",
        "title": task.title,
        "description": task.description,
        "prompt": task.prompt or task.description,
        "status": "pending",
        "created_at": datetime.datetime.now().isoformat(),
        "claimed_by": None,
        "result": None,
        "role": task.role,
        "priority": task.priority,
        "priority_order": priority_order.get(task.priority, 2),
        "skills": [s.lower() for s in task.skills],
    }
    
    board["tasks"].append(new_task)
    # Sort by priority
    board["tasks"].sort(key=lambda t: (t.get("priority_order", 2), t.get("created_at", "")))
    save_board(board)
    
    return new_task


@app.put("/api/tasks/{task_id}")
def update_task(task_id: str, task_update: TaskUpdate):
    """Update an existing task."""
    board = load_board()
    
    for task in board.get("tasks", []):
        if task["id"] == task_id:
            # Update only provided fields
            if task_update.title is not None:
                task["title"] = task_update.title
            if task_update.description is not None:
                task["description"] = task_update.description
            if task_update.prompt is not None:
                task["prompt"] = task_update.prompt
            if task_update.role is not None:
                task["role"] = task_update.role
            if task_update.priority is not None:
                task["priority"] = task_update.priority
                priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
                task["priority_order"] = priority_order.get(task_update.priority, 2)
            if task_update.status is not None:
                allowed = {"pending", "in_progress", "done", "blocked"}
                if task_update.status not in allowed:
                    raise HTTPException(status_code=422, detail=f"Invalid status '{task_update.status}'. Must be one of: {sorted(allowed)}")
                task["status"] = task_update.status
            if task_update.skills is not None:
                task["skills"] = [s.lower() for s in task_update.skills]

            save_board(board)
            return task
    
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task."""
    board = load_board()
    
    original_count = len(board.get("tasks", []))
    board["tasks"] = [t for t in board.get("tasks", []) if t["id"] != task_id]
    
    if len(board["tasks"]) == original_count:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    save_board(board)
    return {"deleted": task_id}


@app.get("/api/agents")
def get_agents():
    """Get all agents and their status."""
    agents = load_agents()
    return {"agents": agents, "count": len(agents)}


@app.get("/api/agents/{agent_name}")
def get_agent(agent_name: str):
    """Get a specific agent by name."""
    agents = load_agents()
    if agent_name in agents:
        return {"name": agent_name, **agents[agent_name]}
    raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")


# ------------------------------------------------------------------
# WebSocket for real-time updates
# ------------------------------------------------------------------

class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send message to all connected clients. Dead connections are silently dropped."""
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for c in dead:
            self.disconnect(c)


manager = ConnectionManager()

# Track board.json mtime so we only push on actual changes
_board_last_mtime: float = 0.0


async def board_watcher():
    """
    Background task: polls board.json every 500ms and broadcasts
    to all connected WebSocket clients when the file changes.
    TASK 5001 — real-time push without external dependencies.
    """
    global _board_last_mtime
    board_file = BOARD_DIR / "board.json"
    while True:
        await asyncio.sleep(0.5)
        try:
            if not board_file.exists():
                continue
            mtime = board_file.stat().st_mtime
            if mtime != _board_last_mtime:
                _board_last_mtime = mtime
                board = load_board()
                await manager.broadcast({"type": "board_update", "data": board})
        except Exception:
            pass


@app.on_event("startup")
async def startup():
    asyncio.create_task(board_watcher())


@app.websocket("/api/ws/board")
async def websocket_board(websocket: WebSocket):
    """
    WebSocket endpoint for real-time board updates.
    Sends initial board state on connect, then pushes diffs whenever board.json changes.
    """
    await manager.connect(websocket)
    try:
        board = load_board()
        await websocket.send_json({"type": "board_update", "data": board})
        # Hold the connection open; watcher does the pushing
        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        manager.disconnect(websocket)


@app.websocket("/api/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for log streaming. TASK 5002.

    Client sends a JSON message: {"agent": "claude"} to select which log to tail.
    Streams new lines from logs/<agent>.log as they appear.
    Defaults to tailing all agent logs if no agent specified.
    """
    await websocket.accept()
    agent_name: Optional[str] = None

    # Wait up to 3s for client to specify which agent to tail
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=3.0)
        try:
            msg = json.loads(raw)
            agent_name = msg.get("agent")
        except Exception:
            pass
    except asyncio.TimeoutError:
        pass

    # Determine log file(s) to tail
    log_dir = Path(os.environ.get("CLOWDER_LOG_DIR", BOARD_DIR.parent / "logs"))

    async def tail_file(log_file: Path):
        """Async generator that yields new lines from a log file."""
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                f.seek(0, 2)  # seek to end
                while True:
                    line = f.readline()
                    if line:
                        yield line.rstrip()
                    else:
                        await asyncio.sleep(0.25)
        except Exception:
            return

    async def stream_agent(agent: str):
        log_file = log_dir / f"{agent}.log"
        if not log_file.exists():
            await websocket.send_json({"type": "log_error", "agent": agent, "message": f"Log file not found: {log_file.name}"})
            return
        async for line in tail_file(log_file):
            try:
                await websocket.send_json({"type": "log_line", "agent": agent, "line": line})
            except Exception:
                return

    try:
        await websocket.send_json({"type": "log_connected", "agent": agent_name or "all"})

        if agent_name:
            await stream_agent(agent_name)
        else:
            # Tail all available log files concurrently
            log_files = list(log_dir.glob("*.log")) if log_dir.exists() else []
            if not log_files:
                await websocket.send_json({"type": "log_error", "message": "No log files found"})
                await asyncio.sleep(999999)
            else:
                tasks = [asyncio.create_task(stream_agent(f.stem)) for f in log_files]
                try:
                    await asyncio.gather(*tasks)
                finally:
                    for t in tasks:
                        t.cancel()
    except WebSocketDisconnect:
        pass


# ------------------------------------------------------------------
# Health monitoring endpoints
# ------------------------------------------------------------------

from agents.health_monitor import HealthMonitor

_health_monitor = HealthMonitor()


@app.get("/api/health")
def get_health():
    """
    Get agent health summary.
    Returns current status of all agents and any active alerts.
    """
    return _health_monitor.get_summary()


@app.get("/api/health/alerts/active")
def get_active_alerts():
    """Get all currently active health alerts."""
    alerts = _health_monitor.get_alerts()
    return {"alerts": [a.to_dict() for a in alerts], "count": len(alerts)}


@app.get("/api/health/{agent_name}")
def get_agent_health(agent_name: str):
    """Get health status for a specific agent."""
    from dataclasses import asdict
    healths = _health_monitor.check_agents()
    for h in healths:
        if h.name == agent_name:
            return asdict(h)
    raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")


# ------------------------------------------------------------------
# Run with: uvicorn web.backend.main:app --reload
# ------------------------------------------------------------------
