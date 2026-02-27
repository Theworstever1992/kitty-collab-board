"""
claude_agent.py — Kitty Collab Board
Claude (Anthropic) agent wrapper.
"""

import os
from agents.base_agent import BaseAgent

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeAgent(BaseAgent):
    """Claude agent — lead reasoning and planning."""

    def __init__(self, api_key: str = None):
        super().__init__(
            name="claude", model="claude-3-5-sonnet-20241022", role="reasoning"
        )
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.client = None
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def handle_task(self, task: dict) -> str:
        self.log(f"Handling task: {task.get('title', 'unknown')}")
        prompt = task.get("prompt", task.get("description", ""))
        if not prompt:
            return "No prompt provided."

        if not self.client:
            self.log(
                "Anthropic client not available — check ANTHROPIC_API_KEY.", "WARN"
            )
            return "Claude unavailable (no API key)."

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        result = message.content[0].text
        self.log(f"Task complete. Response length: {len(result)} chars.")
        return result


if __name__ == "__main__":
    agent = ClaudeAgent()
    agent.run()
