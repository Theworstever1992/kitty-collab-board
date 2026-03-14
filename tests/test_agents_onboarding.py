import pytest
import httpx
from agents.onboarding import onboard_agent, pick_default_avatar

@pytest.mark.asyncio
async def test_pick_default_avatar():
    assert pick_default_avatar("test-agent") in ["tabby", "tuxedo", "calico"]
    # Determinism
    assert pick_default_avatar("a") == pick_default_avatar("a")

@pytest.mark.asyncio
async def test_onboard_agent_mock(respx_mock):
    api_base = "http://test-api"
    name = "new-cat"
    role = "coder"

    # Mock Step 1: Register
    respx_mock.post(f"{api_base}/api/agents/register").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    # Mock Step 2: Profile
    respx_mock.patch(f"{api_base}/api/v2/agents/{name}/profile").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    # Mock Step 3: Intro Chat
    respx_mock.post(f"{api_base}/api/v2/chat/main-hall").mock(
        return_value=httpx.Response(200, json={"id": "msg-123"})
    )

    result = await onboard_agent(api_base, name, role, bio="Hello", skills=["python"])
    assert result == {"ok": True}
