import pytest
import httpx
from agents.standards_manager_agent import StandardsManagerAgent

@pytest.mark.asyncio
async def test_standards_manager_run_once(respx_mock):
    api_base = "http://test-api"
    agent = StandardsManagerAgent(api_base)

    # Mock GET tasks
    respx_mock.get(f"{api_base}/api/tasks?status=done").mock(
        return_value=httpx.Response(200, json=[
            {
                "id": "t1",
                "assigned_to": "cat1",
                "result": "def foo():\n  pass" # Missing return type
            }
        ])
    )

    # Mock POST violation
    respx_mock.post(f"{api_base}/api/v2/governance/violations").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    # Mock POST chat summary
    respx_mock.post(f"{api_base}/api/v2/chat/main-hall").mock(
        return_value=httpx.Response(200, json={"id": "m1"})
    )

    result = await agent.run_once()
    assert result["scanned"] == 1
    assert result["violations_found"] >= 1

@pytest.mark.asyncio
async def test_standards_manager_clean(respx_mock):
    api_base = "http://test-api"
    agent = StandardsManagerAgent(api_base)

    respx_mock.get(f"{api_base}/api/tasks?status=done").mock(
        return_value=httpx.Response(200, json=[
            {
                "id": "t2",
                "assigned_to": "cat2",
                "result": "def foo() -> None:\n  \"\"\"Doc\"\"\"\n  pass"
            }
        ])
    )
    respx_mock.post(f"{api_base}/api/v2/chat/main-hall").mock(
        return_value=httpx.Response(200, json={"id": "m2"})
    )

    result = await agent.run_once()
    assert result["scanned"] == 1
    assert result["violations_found"] == 0
