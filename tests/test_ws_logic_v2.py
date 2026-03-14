import pytest
from backend.ws import ConnectionManager
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_connection_manager_broadcast_error():
    manager = ConnectionManager()
    ws1 = AsyncMock()
    ws2 = AsyncMock()

    # Mock send_json to fail for ws1
    ws1.send_json.side_effect = Exception("dead")

    await manager.connect("room", ws1)
    await manager.connect("room", ws2)

    await manager.broadcast("room", {"data": "test"})

    # ws1 should be disconnected
    assert ws1 not in manager._rooms["room"]
    assert ws2 in manager._rooms["room"]
