import pytest
import httpx
from agents.token_manager_agent import TokenManagerAgent

@pytest.mark.asyncio
async def test_token_manager_run_once(respx_mock):
    api_base = "http://test-api"
    agent = TokenManagerAgent(api_base)

    # Mock token report endpoint
    respx_mock.get(f"{api_base}/api/v2/governance/token-report").mock(
        return_value=httpx.Response(200, json=[
            {
                "agent": "cat1",
                "total_cost_usd": 0.05,
                "total_input": 1000,
                "total_output": 2000,
                "request_count": 5
            }
        ])
    )

    # Mock chat post endpoint
    respx_mock.post(f"{api_base}/api/v2/chat/manager").mock(
        return_value=httpx.Response(200, json={"id": "m1"})
    )

    result = await agent.run_once()
    assert result["agents_reported"] == 1
    assert result["posted"] is True

@pytest.mark.asyncio
async def test_token_manager_run_once_empty(respx_mock):
    api_base = "http://test-api"
    agent = TokenManagerAgent(api_base)

    respx_mock.get(f"{api_base}/api/v2/governance/token-report").mock(
        return_value=httpx.Response(200, json=[])
    )
    respx_mock.post(f"{api_base}/api/v2/chat/manager").mock(
        return_value=httpx.Response(200, json={"id": "m2"})
    )

    result = await agent.run_once()
    assert result["agents_reported"] == 0
