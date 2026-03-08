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
# Analytics Endpoints - TASK 6031, 6032, 6033, 6034
# ------------------------------------------------------------------

from agents.metrics import get_metrics_collector, MetricsCollector


@app.get("/api/analytics/summary")
def get_analytics_summary():
    """Get system-wide analytics summary."""
    collector = get_metrics_collector()
    summary = collector.get_system_summary()
    return {
        "timestamp": summary.timestamp,
        "total_tasks": summary.total_tasks,
        "pending_tasks": summary.pending_tasks,
        "in_progress_tasks": summary.in_progress_tasks,
        "done_tasks": summary.done_tasks,
        "blocked_tasks": summary.blocked_tasks,
        "total_agents": summary.total_agents,
        "online_agents": summary.online_agents,
        "avg_completion_time_seconds": summary.avg_task_completion_time_seconds,
        "tasks_completed_today": summary.tasks_completed_today,
        "tasks_completed_this_week": summary.tasks_completed_this_week,
        "tasks_completed_this_month": summary.tasks_completed_this_month,
    }


@app.get("/api/analytics/completion-trend")
def get_completion_trend(days: int = 7):
    """Get task completion trend over specified days."""
    collector = get_metrics_collector()
    trend = collector.get_completion_trend(days)
    return {"days": days, "trend": trend}


@app.get("/api/analytics/agent-leaderboard")
def get_agent_leaderboard(metric: str = "tasks_completed"):
    """Get agent ranking by specified metric."""
    collector = get_metrics_collector()
    valid_metrics = ["tasks_completed", "tasks_claimed", "success_rate", "total_result_chars"]
    if metric not in valid_metrics:
        raise HTTPException(status_code=422, detail=f"Invalid metric. Must be one of: {valid_metrics}")
    leaderboard = collector.get_agent_leaderboard(metric)
    return {"metric": metric, "leaderboard": leaderboard}


@app.get("/api/analytics/agents")
def get_all_agent_metrics():
    """Get metrics for all agents."""
    collector = get_metrics_collector()
    agents = collector.get_all_agent_metrics()
    from dataclasses import asdict
    return {"agents": [asdict(a) for a in agents]}


@app.get("/api/analytics/tasks/{task_id}")
def get_task_metrics(task_id: str):
    """Get metrics for a specific task."""
    collector = get_metrics_collector()
    metrics = collector.get_task_metrics(task_id)
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found in metrics")
    from dataclasses import asdict
    return asdict(metrics)


@app.get("/api/analytics/export/csv")
def export_metrics_csv():
    """Export task metrics to CSV format."""
    import tempfile
    from fastapi.responses import FileResponse

    collector = get_metrics_collector()
    
    # Create temp file
    fd, path = tempfile.mkstemp(suffix=".csv", prefix="clowder_metrics_")
    output_path = Path(path)
    
    collector.export_csv(output_path)
    
    return FileResponse(
        path=output_path,
        media_type="text/csv",
        filename="clowder_metrics.csv",
    )


@app.get("/api/analytics/export/json")
def export_metrics_json():
    """Export all metrics to JSON format."""
    from agents.metrics import MetricsCollector
    collector = get_metrics_collector()
    data = collector._load_metrics()
    return data


# ------------------------------------------------------------------
# Recurring Tasks Endpoints - TASK 6024
# ------------------------------------------------------------------

from agents.recurring import get_recurring_manager, RecurrenceType


class RecurringTaskCreate(BaseModel):
    title: str
    description: str
    prompt: str
    recurrence_type: str  # daily, weekly, monthly, custom
    interval: int = 1
    hour: int = 9
    day_of_week: int = 0
    day_of_month: int = 1
    role: Optional[str] = None
    priority: str = "normal"
    skills: list[str] = []


@app.get("/api/recurring")
def get_recurring_tasks():
    """Get all recurring tasks."""
    manager = get_recurring_manager()
    tasks = manager.list_recurring_tasks(enabled_only=False)
    from dataclasses import asdict
    return {"tasks": [asdict(t) for t in tasks]}


@app.post("/api/recurring", status_code=201)
def create_recurring_task(task: RecurringTaskCreate):
    """Create a new recurring task."""
    manager = get_recurring_manager()
    task_id = manager.add_recurring_task(
        title=task.title,
        description=task.description,
        prompt=task.prompt,
        recurrence_type=task.recurrence_type,
        interval=task.interval,
        hour=task.hour,
        day_of_week=task.day_of_week,
        day_of_month=task.day_of_month,
        role=task.role,
        priority=task.priority,
        skills=task.skills,
    )
    return {"id": task_id, "status": "created"}


@app.delete("/api/recurring/{task_id}")
def delete_recurring_task(task_id: str):
    """Delete a recurring task."""
    manager = get_recurring_manager()
    manager.delete_recurring_task(task_id)
    return {"deleted": task_id}


@app.post("/api/recurring/{task_id}/enable")
def enable_recurring_task(task_id: str):
    """Enable a recurring task."""
    manager = get_recurring_manager()
    manager.enable_recurring_task(task_id)
    return {"status": "enabled"}


@app.post("/api/recurring/{task_id}/disable")
def disable_recurring_task(task_id: str):
    """Disable a recurring task."""
    manager = get_recurring_manager()
    manager.disable_recurring_task(task_id)
    return {"status": "disabled"}


# ------------------------------------------------------------------
# Multi-Board Endpoints - TASK 6025
# ------------------------------------------------------------------

from agents.multiboard import get_multiboard_manager


@app.get("/api/boards")
def get_boards():
    """Get list of all boards."""
    manager = get_multiboard_manager()
    boards = manager.list_boards()
    from dataclasses import asdict
    return {"boards": [asdict(b) for b in boards]}


@app.post("/api/boards", status_code=201)
def create_board(name: str, description: str = ""):
    """Create a new board."""
    manager = get_multiboard_manager()
    try:
        board_name = manager.create_board(name, description)
        return {"name": board_name, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/boards/{board_name}/switch")
def switch_to_board(board_name: str):
    """Switch the active board."""
    manager = get_multiboard_manager()
    try:
        manager.switch_board(board_name)
        return {"status": "switched", "board": board_name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/boards/{board_name}")
def delete_board(board_name: str):
    """Delete a board."""
    manager = get_multiboard_manager()
    try:
        if manager.delete_board(board_name):
            return {"deleted": board_name}
        raise HTTPException(status_code=404, detail=f"Board {board_name} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/boards/active")
def get_active_board():
    """Get the currently active board."""
    manager = get_multiboard_manager()
    board = manager.get_active_board()
    if board:
        from dataclasses import asdict
        return asdict(board)
    return {"message": "No active board"}


# ------------------------------------------------------------------
# Task Dependencies Endpoints - TASK 6022
# ------------------------------------------------------------------

from agents.dependencies import get_dependency_manager


class DependencyCreate(BaseModel):
    task_id: str
    blocked_by: str


@app.get("/api/tasks/{task_id}/dependencies")
def get_task_dependencies(task_id: str):
    """Get dependencies for a task."""
    manager = get_dependency_manager()
    deps = manager.get_dependencies(task_id)
    return {"task_id": task_id, "blocked_by": deps}


@app.post("/api/tasks/{task_id}/dependencies")
def add_task_dependency(task_id: str, dep: DependencyCreate):
    """Add a dependency: task_id is blocked by blocked_by."""
    manager = get_dependency_manager()
    if dep.task_id != task_id:
        raise HTTPException(status_code=400, detail="task_id in URL must match body")
    manager.add_dependency(task_id, dep.blocked_by)
    return {"status": "added", "task_id": task_id, "blocked_by": dep.blocked_by}


@app.delete("/api/tasks/{task_id}/dependencies/{blocked_by}")
def remove_task_dependency(task_id: str, blocked_by: str):
    """Remove a dependency."""
    manager = get_dependency_manager()
    manager.remove_dependency(task_id, blocked_by)
    return {"status": "removed", "task_id": task_id, "blocked_by": blocked_by}


@app.get("/api/tasks/{task_id}/blocking")
def get_blocking_tasks(task_id: str):
    """Get tasks that are blocking this task."""
    manager = get_dependency_manager()
    board = load_board()
    blocking = manager.get_blocking_tasks(task_id, board.get("tasks", []))
    return {"task_id": task_id, "blocking": blocking}


@app.get("/api/tasks/ready")
def get_ready_tasks():
    """Get tasks that are ready to be claimed (not blocked)."""
    manager = get_dependency_manager()
    board = load_board()
    ready = manager.get_ready_tasks(board.get("tasks", []))
    return {"ready_tasks": ready}


# ------------------------------------------------------------------
# Run with: uvicorn web.backend.main:app --reload
# ------------------------------------------------------------------
