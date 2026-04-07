#!/usr/bin/env python3
"""
Web UI Chat Server — Kitty Collab Board

This is HOW YOU CHAT with the AI agents.
Your messages are saved as JSON files.
Agents read and respond in real-time.

Access: http://localhost:8080
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from agents.channels import get_channel, get_or_create_channel, list_channels
from agents.atomic import atomic_read, atomic_write

# Configuration
BOARD_DIR = Path(__file__).parent / "board"
CHANNELS_DIR = BOARD_DIR / "channels"

app = FastAPI(title="Kitty Collab Board Chat")

# CORS — allow all origins for local/LAN development only.
# In production, replace allow_origins=["*"] with an explicit list of trusted origins.
# Note: allow_credentials MUST be False when allow_origins=["*"] — combining both
# is a security misconfiguration (browsers will reject such responses and it opens
# credential-theft attack vectors).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Static Files & Web UI
# ------------------------------------------------------------------

@app.get("/")
async def root():
    """Serve the Web UI."""
    ui_file = Path(__file__).parent / "ui.html"
    if ui_file.exists():
        return FileResponse(str(ui_file))
    return HTMLResponse("<h1>🐱 Kitty Collab Board</h1><p>Web UI not found. Run: python3 wake_up_all.py</p>")


@app.get("/api/channels")
async def get_channels():
    """List all channels."""
    return {"channels": list_channels()}


@app.get("/api/messages/{channel_name}")
async def get_messages(channel_name: str, limit: int = 50):
    """Get messages from a channel."""
    channel = get_channel(channel_name)
    if not channel:
        return {"error": "Channel not found"}
    
    messages = channel.read(limit=limit, reverse=True)
    return {"messages": messages}


# ------------------------------------------------------------------
# WebSocket for Real-Time Chat
# ------------------------------------------------------------------

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.subscriptions: dict[WebSocket, set] = {}  # connection -> set of channels
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
    
    def subscribe(self, websocket: WebSocket, channel: str):
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(channel)
    
    async def send_to_channel(self, channel: str, message: dict):
        """Send message to all clients subscribed to a channel."""
        dead = []
        for connection in self.subscriptions:
            if channel in self.subscriptions[connection]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead.append(connection)
        for d in dead:
            self.disconnect(d)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    
    Client messages:
    - {"type": "subscribe", "channel": "general"}
    - {"type": "message", "channel": "general", "sender": "human", "content": "Hello"}
    
    Server messages:
    - {"type": "message", "channel": "general", "data": {...}}
    - {"type": "joined", "channel": "general"}
    """
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "subscribe":
                # Subscribe to a channel
                channel_name = data.get("channel")
                if channel_name:
                    manager.subscribe(websocket, channel_name)
                    
                    # Send recent messages
                    channel = get_channel(channel_name)
                    if channel:
                        messages = channel.read(limit=50)
                        for msg in messages:
                            await websocket.send_json({
                                "type": "message",
                                "channel": channel_name,
                                "data": msg,
                            })
                    
                    await websocket.send_json({
                        "type": "joined",
                        "channel": channel_name,
                    })
            
            elif msg_type == "message":
                # Post a message to channel
                channel_name = data.get("channel")
                sender = data.get("sender", "unknown")
                content = data.get("content", "")
                msg_type = data.get("message_type", "chat")
                
                if channel_name and content:
                    channel = get_channel(channel_name)
                    if channel:
                        # Post to channel (saves as JSON file)
                        msg_id = channel.post(
                            content=content,
                            sender=sender,
                            message_type=msg_type,
                        )
                        
                        # Broadcast to all subscribers
                        await manager.send_to_channel(channel_name, {
                            "type": "message",
                            "channel": channel_name,
                            "data": {
                                "id": msg_id,
                                "sender": sender,
                                "content": content,
                                "timestamp": datetime.now().isoformat(),
                                "type": msg_type,
                            },
                        })
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ------------------------------------------------------------------
# Agent Status
# ------------------------------------------------------------------

@app.get("/api/agents")
async def get_agents():
    """Get all registered agents."""
    agents_file = BOARD_DIR / "agents.json"
    if agents_file.exists():
        return {"agents": atomic_read(agents_file, {})}
    return {"agents": {}}


@app.post("/api/agents/register")
async def register_agent(name: str, role: str = "agent", team: str = None):
    """Register an agent on the board."""
    agents_file = BOARD_DIR / "agents.json"
    agents = atomic_read(agents_file, {})
    
    agents[name] = {
        "name": name,
        "role": role,
        "team": team,
        "status": "online",
        "last_seen": datetime.now().isoformat(),
    }
    
    atomic_write(agents_file, agents)
    
    # Post to assembly channel
    assembly = get_or_create_channel("assembly")
    assembly.post(
        content=f"🟢 **{name}** online. Role: {role}. Team: {team or 'none'}.",
        sender=name,
        message_type="update",
    )
    
    return {"status": "registered", "agent": agents[name]}


# ------------------------------------------------------------------
# Run with: python3 -m uvicorn web_chat:app --reload --port 8080
# ------------------------------------------------------------------
