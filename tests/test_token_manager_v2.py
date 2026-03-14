import pytest
from agents.token_manager_agent import TokenManagerAgent

def test_token_manager_agent_init():
    agent = TokenManagerAgent(api_base="http://localhost")
    assert agent.agent_name == "token-manager"
