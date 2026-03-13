"""
ws.py — Clowder v2 WebSocket Connection Manager
Room-based real-time messaging. Replaces the v1 WebSocket in server.py.
"""

from fastapi import WebSocket


class ConnectionManager:
    """
    Manages active WebSocket connections grouped by room.

    Rooms map to chat channels. Clients in the same room receive
    broadcast messages. Dead connections are silently removed on
    send failure so one stale client never blocks others.
    """

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket) -> None:
        """Accept a WebSocket connection and register it in the given room."""
        await ws.accept()
        self._rooms.setdefault(room, set()).add(ws)

    def disconnect(self, room: str, ws: WebSocket) -> None:
        """Remove a WebSocket from the room. No-op if the connection is not present."""
        room_set = self._rooms.get(room)
        if room_set:
            room_set.discard(ws)
            # Clean up the room entry if it is now empty
            if not room_set:
                del self._rooms[room]

    async def broadcast(self, room: str, message: dict) -> None:
        """
        Send JSON to every connection in the room.

        If a send fails (e.g. the client disconnected between the check
        and the send), the dead connection is removed and iteration
        continues so that other clients still receive the message.
        """
        dead: list[WebSocket] = []
        for ws in list(self._rooms.get(room, set())):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(room, ws)


# Module-level singleton — imported by main.py
manager = ConnectionManager()
