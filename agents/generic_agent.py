"""
generic_agent.py — Kitty Collab Board
Generic agent class that works with any provider.
Replaces per-model agent files for new deployments.
"""

import os
from typing import Any

from agents.base_agent import BaseAgent
from agents.providers.base import BaseProvider, ProviderError
from agents.prompts import get_system_prompt


class GenericAgent(BaseAgent):
    """
    A generic agent that accepts any provider instance.
    
    This agent works with any BaseProvider implementation (Anthropic,
    OpenAI-compat, Ollama, Gemini, etc.) without provider-specific code.
    
    Configuration is passed via agent_config dict from agents.yaml.
    """

    def __init__(self, agent_config: dict, provider: BaseProvider):
        """
        Initialize the generic agent.
        
        Args:
            agent_config: Agent configuration from agents.yaml
                         Must include: name, model, provider, role
            provider: Instantiated provider (BaseProvider subclass)
        """
        self.config = agent_config
        self.provider = provider
        
        name = agent_config.get('name', 'generic')
        model = agent_config.get('model', 'unknown')
        role = agent_config.get('role', 'general')
        
        super().__init__(name=name, model=model, role=role)
        
        # Get system prompt from config or use role default
        self.system_prompt = agent_config.get(
            'system_prompt',
            get_system_prompt(role)
        )
        
        # Provider-specific config for API calls
        self.provider_config = {
            'max_tokens': agent_config.get('max_tokens', 4096),
            'temperature': agent_config.get('temperature', 0.7),
        }

    def handle_task(self, task: dict) -> str:
        """
        Handle a task using the configured provider.
        
        Args:
            task: Task dict with 'prompt' or 'description' field
        
        Returns:
            Provider's response text
        
        Notes:
            - ProviderError is caught by BaseAgent.run() and marks task blocked
            - This method should not raise exceptions
        """
        prompt = task.get('prompt', task.get('description', ''))
        if not prompt:
            return "No prompt provided in task."
        
        self.log(f"Handling task: {task.get('title', 'unknown')}")
        self.log(f"Using provider: {self.provider.__class__.__name__}")
        
        # Check if provider is available
        if not self.provider.is_available():
            self.log("Provider not available — check API key and dependencies", "WARN")
            return (
                f"Provider unavailable: {self.provider.__class__.__name__}. "
                "Check API key and dependencies."
            )
        
        try:
            result = self.provider.complete(
                prompt=prompt,
                system=self.system_prompt,
                config=self.provider_config,
            )
            self.log(f"Task complete. Response length: {len(result)} chars.")
            return result
        except ProviderError as e:
            self.log(f"Provider error: {e}", "ERROR")
            raise  # Re-raise so BaseAgent.run() can mark as blocked

    def __repr__(self) -> str:
        return f"GenericAgent(name={self.name!r}, model={self.model!r}, role={self.role!r})"


# Main entry point for running as standalone agent
if __name__ == "__main__":
    import sys
    
    # Try to load config and run
    try:
        from agents.config import load_agents_config, build_agent
        
        # Parse --agent <name> flag or positional arg
        agent_name = None
        args = sys.argv[1:]
        if '--agent' in args:
            idx = args.index('--agent')
            if idx + 1 < len(args):
                agent_name = args[idx + 1]
        elif args and not args[0].startswith('--'):
            agent_name = args[0]
        
        agents = load_agents_config()
        
        if agent_name:
            # Find specific agent by name
            agent_config = next(
                (a for a in agents if a['name'] == agent_name),
                None
            )
            if not agent_config:
                print(f"Agent not found: {agent_name}")
                sys.exit(1)
        else:
            # Use first agent in config
            agent_config = agents[0]
            print(f"No agent specified, using: {agent_config['name']}")
        
        print(f"Starting agent: {agent_config['name']}")
        agent = build_agent(agent_config)
        agent.run()
        
    except FileNotFoundError as e:
        print(f"Config error: {e}")
        print("Run 'python wake_up.py' or create agents.yaml")
        sys.exit(1)
    except ImportError as e:
        print(f"Import error: {e}")
        print("Run: pip install pyyaml")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
