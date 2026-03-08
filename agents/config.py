"""
config.py — Kitty Collab Board
Configuration loader for agents.yaml.
Loads agent configurations and instantiates providers.
"""

import os
from pathlib import Path
from typing import Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from agents.providers.base import BaseProvider, ProviderError
from agents.providers.anthropic_provider import AnthropicProvider
from agents.providers.openai_compat import OpenAICompatProvider
from agents.providers.ollama import OllamaProvider
from agents.providers.gemini import GeminiProvider


def load_agents_config(path: str = "agents.yaml") -> list[dict]:
    """
    Load agent configurations from YAML file.
    
    Args:
        path: Path to the agents.yaml file
    
    Returns:
        List of agent configuration dictionaries
    
    Raises:
        FileNotFoundError: If the config file doesn't exist
        ValueError: If YAML is invalid or missing required fields
    """
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML not installed. Run: pip install pyyaml")
    
    config_path = Path(path)
    if not config_path.exists():
        # Try relative to this file's parent (project root)
        config_path = Path(__file__).parent.parent / "agents.yaml"
        if not config_path.exists():
            raise FileNotFoundError(
                f"Agent config not found: {path} or {config_path}"
            )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}")
    
    if not isinstance(data, dict) or 'agents' not in data:
        raise ValueError(
            f"Invalid agents.yaml format: expected 'agents:' key at root"
        )
    
    agents = data.get('agents', [])
    if not isinstance(agents, list):
        raise ValueError("'agents' must be a list of agent configurations")
    
    # Validate required fields
    required_fields = ['name', 'model', 'provider', 'role']
    for i, agent in enumerate(agents):
        missing = [f for f in required_fields if f not in agent]
        if missing:
            raise ValueError(
                f"Agent {i} ({agent.get('name', 'unknown')}) missing fields: {missing}"
            )
    
    return agents


def build_provider(agent_config: dict) -> BaseProvider:
    """
    Instantiate the correct provider from an agent config.
    
    Args:
        agent_config: Agent configuration dict from agents.yaml
    
    Returns:
        Instantiated provider
    
    Raises:
        ValueError: If provider name is unknown
        ProviderError: If provider cannot be initialized
    """
    provider_name = agent_config.get('provider', '')
    model = agent_config.get('model', '')
    api_key_env = agent_config.get('api_key_env')
    base_url = agent_config.get('base_url')
    
    # Map provider name to provider class
    provider_map = {
        'anthropic': AnthropicProvider,
        'openai_compat': OpenAICompatProvider,
        'ollama': OllamaProvider,
        'gemini': GeminiProvider,
    }
    
    if provider_name not in provider_map:
        valid = ', '.join(provider_map.keys())
        raise ValueError(
            f"Unknown provider: '{provider_name}'. Valid options: {valid}"
        )
    
    provider_class = provider_map[provider_name]
    
    # Build kwargs for provider constructor
    kwargs = {'model': model}
    
    if api_key_env:
        kwargs['api_key_env'] = api_key_env
    
    if base_url:
        kwargs['base_url'] = base_url
    
    try:
        return provider_class(**kwargs)
    except Exception as e:
        raise ProviderError(f"Failed to initialize {provider_name}: {e}")


def build_agent(agent_config: dict) -> Any:
    """
    Build a fully configured GenericAgent from one YAML entry.
    
    Args:
        agent_config: Agent configuration dict from agents.yaml
    
    Returns:
        Instantiated GenericAgent
    
    Raises:
        ImportError: If GenericAgent not available
        ValueError: If config is invalid
    """
    # Import here to avoid circular dependency
    from agents.generic_agent import GenericAgent
    
    provider = build_provider(agent_config)
    return GenericAgent(agent_config, provider)
