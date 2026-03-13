"""
server.py — Kitty Collab Board Collab Server
Real-time synchronization server with Watchdog + WebSocket.

Monitors the board/ directory for file changes and broadcasts
updates to connected WebSocket clients instantly.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Set

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

from agents.atomic import atomic_read


# Configuration
BOARD_DIR = Path(
    os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent / "board")
)
CHANNELS_DIR = BOARD_DIR / "channels"
AGENTS_DIR = BOARD_DIR / "agents"

HOST = os.environ.get("CLOWDER_SERVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("CLOWDER_SERVER_PORT", "8765"))


class BoardEventHandler(FileSystemEventHandler):
    """
    Watchdog event handler for board file changes.
    
    Broadcasts file changes to all connected WebSocket clients.
    """
    
    def __init__(self, server: "CollabServer"):
        self.server = server
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        # Only care about JSON files in channels or agents
        if path.suffix == ".json" and not path.name.startswith("."):
            self._broadcast_file(path, "created")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        # Only care about JSON files
        if path.suffix == ".json" and not path.name.startswith("."):
            self._broadcast_file(path, "modified")
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        if path.suffix == ".json":
            self.server.broadcast({
                "type": "deleted",
                "path": str(path.relative_to(BOARD_DIR)),
                "timestamp": datetime.now().isoformat(),
            })
    
    def _broadcast_file(self, path: Path, event_type: str):
        """Read file and broadcast content."""
        try:
            # Skip temp files
            if path.suffix == ".tmp":
                return
            
            content = atomic_read(path)
            if content is None:
                return
            
            self.server.broadcast({
                "type": event_type,
                "path": str(path.relative_to(BOARD_DIR)),
                "content": content,
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            self.server.logger(f"Error reading file {path}: {e}", "ERROR")


class CollabServer:
    """
    Collab Server with Watchdog + WebSocket.
    
    Passively observes the board/ directory and broadcasts
    changes to connected clients in real-time.
    """
    
    def __init__(self, host: str = HOST, port: int = PORT):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.observer: Optional[Observer] = None
        self._running = False
        self._logger = print
    
    def logger(self, message: str, level: str = "INFO"):
        """Log a message."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._logger(f"[{ts}] [{level}] {message}")
    
    def set_logger(self, logger_func):
        """Set custom logger function."""
        self._logger = logger_func
    
    def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients.
        
        Dead connections are silently removed.
        """
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        dead_clients = set()
        
        for client in self.clients:
            try:
                # Use asyncio.create_task for non-blocking send
                asyncio.create_task(client.send(message_json))
            except Exception:
                dead_clients.add(client)
        
        # Remove dead clients
        self.clients -= dead_clients
    
    async def handle_client(self, websocket: WebSocketServerProtocol):
        """
        Handle a WebSocket client connection.
        
        Sends initial state, then pushes updates.
        """
        # Register client
        self.clients.add(websocket)
        self.logger(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            # Send initial state
            await self._send_initial_state(websocket)
            
            # Keep connection alive
            async for message in websocket:
                # Handle incoming messages (optional)
                try:
                    data = json.loads(message)
                    await self._handle_incoming_message(websocket, data)
                except json.JSONDecodeError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger("Client disconnected")
        finally:
            self.clients.discard(websocket)
            self.logger(f"Client removed. Total clients: {len(self.clients)}")
    
    async def _send_initial_state(self, websocket: WebSocketServerProtocol):
        """Send initial board state to new client."""
        # Load channels registry
        channels_registry = atomic_read(
            BOARD_DIR / ".channels.json",
            {"channels": {}}
        )
        
        # Load agents
        agents = atomic_read(BOARD_DIR / "agents.json", {})
        
        # Load context metrics
        context_metrics = atomic_read(
            BOARD_DIR / ".context_metrics.json",
            {"total": {}}
        )
        
        # Send initial state
        await websocket.send(json.dumps({
            "type": "initial_state",
            "channels": list(channels_registry.get("channels", {}).values()),
            "agents": agents,
            "context": context_metrics.get("total", {}),
            "timestamp": datetime.now().isoformat(),
        }))
    
    async def _handle_incoming_message(
        self,
        websocket: WebSocketServerProtocol,
        data: dict,
    ):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        
        if msg_type == "ping":
            await websocket.send(json.dumps({"type": "pong"}))
        
        elif msg_type == "subscribe":
            # Subscribe to specific channel
            channel = data.get("channel")
            if channel:
                await websocket.send(json.dumps({
                    "type": "subscribed",
                    "channel": channel,
                }))
        
        elif msg_type == "get_channel":
            # Get channel messages
            from agents.channels import get_channel
            channel = data.get("channel")
            limit = data.get("limit", 50)
            
            ch = get_channel(channel)
            if ch:
                messages = ch.read(limit=limit)
                await websocket.send(json.dumps({
                    "type": "channel_messages",
                    "channel": channel,
                    "messages": messages,
                }))
    
    def start_watching(self):
        """Start watching the board directory."""
        if not WATCHDOG_AVAILABLE:
            self.logger("Watchdog not available. Install with: pip install watchdog", "WARNING")
            return
        
        event_handler = BoardEventHandler(self)
        self.observer = Observer()
        
        # Watch channels directory
        if CHANNELS_DIR.exists():
            self.observer.schedule(event_handler, str(CHANNELS_DIR), recursive=True)
            self.logger(f"Watching channels: {CHANNELS_DIR}")
        
        # Watch agents directory
        if AGENTS_DIR.exists():
            self.observer.schedule(event_handler, str(AGENTS_DIR), recursive=False)
            self.logger(f"Watching agents: {AGENTS_DIR}")
        
        # Watch board root for .channels.json, etc.
        self.observer.schedule(event_handler, str(BOARD_DIR), recursive=False)
        self.logger(f"Watching board root: {BOARD_DIR}")
        
        self.observer.start()
        self._running = True
        self.logger("Watchdog started")
    
    def stop_watching(self):
        """Stop watching the board directory."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self._running = False
            self.logger("Watchdog stopped")
    
    async def run_server(self):
        """Run the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            self.logger("WebSockets not available. Install with: pip install websockets", "ERROR")
            return
        
        self.start_watching()
        
        try:
            async with websockets.serve(
                self.handle_client,
                self.host,
                self.port,
            ):
                self.logger(f"Collab Server running on ws://{self.host}:{self.port}")
                self.logger("Press Ctrl+C to stop")
                
                # Keep running
                await asyncio.Future()
                
        except KeyboardInterrupt:
            self.logger("Shutting down...")
        finally:
            self.stop_watching()
    
    def run(self):
        """Run the server (blocking)."""
        try:
            asyncio.run(self.run_server())
        except KeyboardInterrupt:
            self.logger("Server stopped")


def main():
    """Main entry point."""
    print(r"""
  /\_____/\
 /  o   o  \    🐱 Kitty Collab Server
( ==  ^  == )
 )         (
(           ))
   \     //
    \___//
""")
    
    # Ensure directories exist
    BOARD_DIR.mkdir(parents=True, exist_ok=True)
    CHANNELS_DIR.mkdir(parents=True, exist_ok=True)
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create and run server
    server = CollabServer()
    
    print(f"\n📡 Starting Collab Server...")
    print(f"   Host: {server.host}")
    print(f"   Port: {server.port}")
    print(f"   Board: {BOARD_DIR}")
    print(f"\n📢 WebSocket: ws://{server.host}:{server.port}")
    print(f"📁 Watching: {CHANNELS_DIR}, {AGENTS_DIR}")
    print(f"\nPress Ctrl+C to stop\n")
    
    server.run()


if __name__ == "__main__":
    main()
