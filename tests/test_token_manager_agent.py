import pytest
import httpx
from agents.token_manager_agent import TokenManagerAgent

@pytest.mark.asyncio
async def test_token_manager_run_once_empty(respx_mock):
    api_base = "http://localhost:9000"
    agent = TokenManagerAgent(api_base)

    respx_mock.get(f"{api_base}/api/v2/governance/token-report").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx_mock.post(f"{api_base}/api/v2/chat/manager").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    result = await agent.run_once()
    assert result["agents_reported"] == 0

@pytest.mark.asyncio
async def test_token_manager_run_once_with_data(respx_mock):
    api_base = "http://localhost:9000"
    agent = TokenManagerAgent(api_base)

    data = [
        {"agent": "claude", "total_cost_usd": 0.05, "total_input": 1000, "total_output": 500, "request_count": 10},
        {"agent": "gpt", "total_cost_usd": 0.01, "total_input": 200, "total_output": 100, "request_count": 2},
    ]

    respx_mock.get(f"{api_base}/api/v2/governance/token-report").mock(
        return_value=httpx.Response(200, json=data)
    )
    respx_mock.post(f"{api_base}/api/v2/chat/manager").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    result = await agent.run_once()
    assert result["agents_reported"] == 2
