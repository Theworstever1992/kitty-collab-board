import pytest
import httpx
from agents.standards_manager_agent import StandardsManagerAgent

@pytest.mark.asyncio
async def test_standards_manager_run_once_no_tasks(respx_mock):
    api_base = "http://localhost:9000"
    agent = StandardsManagerAgent(api_base)

    respx_mock.get(f"{api_base}/api/tasks?status=done").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx_mock.post(f"{api_base}/api/v2/chat/main-hall").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    result = await agent.run_once()
    assert result["scanned"] == 0
    assert result["violations_found"] == 0

@pytest.mark.asyncio
async def test_standards_manager_run_once_with_violations(respx_mock):
    api_base = "http://localhost:9000"
    agent = StandardsManagerAgent(api_base)

    tasks = [
        {"id": "t1", "assigned_to": "alice", "result": "def foo():\n    pass"}, # no type hint
        {"id": "t2", "assigned_to": "bob", "result": "try:\n    pass\nexcept:\n    pass"}, # bare except
    ]

    respx_mock.get(f"{api_base}/api/tasks?status=done").mock(
        return_value=httpx.Response(200, json=tasks)
    )
    respx_mock.post(f"{api_base}/api/v2/governance/violations").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    respx_mock.post(f"{api_base}/api/v2/chat/main-hall").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    result = await agent.run_once()
    assert result["scanned"] == 2
    assert result["violations_found"] == 2
