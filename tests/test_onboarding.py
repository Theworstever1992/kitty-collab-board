import pytest
import httpx
from agents.onboarding import pick_default_avatar, onboard_agent

def test_pick_default_avatar():
    assert pick_default_avatar("agent1") in ["tabby", "tuxedo", "calico"]
    assert pick_default_avatar("agent2") in ["tabby", "tuxedo", "calico"]
    # Determinism
    assert pick_default_avatar("same_name") == pick_default_avatar("same_name")

@pytest.mark.asyncio
async def test_onboard_agent_success(respx_mock):
    api_base = "http://localhost:9000"
    name = "new_kitty"
    role = "coder"

    # Mock Step 1: Register
    respx_mock.post(f"{api_base}/api/agents/register").mock(
        return_value=httpx.Response(200, json={"status": "registered", "name": name})
    )

    # Mock Step 2: Set profile
    respx_mock.patch(f"{api_base}/api/v2/agents/{name}/profile").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )

    # Mock Step 3: Post intro message
    respx_mock.post(f"{api_base}/api/v2/chat/main-hall").mock(
        return_value=httpx.Response(200, json={"status": "sent"})
    )

    result = await onboard_agent(api_base, name, role, bio="Meow!")

    assert result["status"] == "registered"
    assert result["name"] == name

@pytest.mark.asyncio
async def test_onboard_agent_no_bio(respx_mock):
    api_base = "http://localhost:9000"
    name = "minimal_kitty"
    role = "tester"

    respx_mock.post(f"{api_base}/api/agents/register").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    respx_mock.patch(f"{api_base}/api/v2/agents/{name}/profile").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    respx_mock.post(f"{api_base}/api/v2/chat/main-hall").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )

    result = await onboard_agent(api_base, name, role)
    assert result["ok"] is True
