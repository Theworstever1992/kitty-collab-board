import pytest
from agents.standards_manager_agent import StandardsManagerAgent

def test_standards_agent_init():
    agent = StandardsManagerAgent(api_base="http://localhost")
    assert agent.agent_name == "standards-manager"

def test_standards_agent_scan():
    agent = StandardsManagerAgent(api_base="http://localhost")
    # Test bare except rule
    violations = agent._scan("try:\n    pass\nexcept:\n    pass")
    assert any(v["rule"] == "bare_except" for v in violations)

    # Test missing type hints
    violations = agent._scan("def foo(x):\n    pass")
    assert any(v["rule"] == "no_type_hints" for v in violations)

    # Test TODO
    violations = agent._scan("# TODO: fix this")
    assert any(v["rule"] == "todo_left_in_result" for v in violations)
