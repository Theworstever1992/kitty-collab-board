"""
qwen_agent.py — Kitty Collab Board
Qwen (Alibaba/OpenAI-compatible) agent wrapper.
"""

import os
from agents.base_agent import BaseAgent

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class QwenAgent(BaseAgent):
    """Qwen agent — code generation and analysis."""

    def __init__(self, api_key: str = None, base_url: str = None):
        super().__init__(name="qwen", model="qwen-plus", role="code")
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = None
        if OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def handle_task(self, task: dict) -> str:
        self.log(f"Handling task: {task.get('title', 'unknown')}")
        prompt = task.get("prompt", task.get("description", ""))
        if not prompt:
            return "No prompt provided."

        if not self.client:
            self.log("Qwen client not available — check DASHSCOPE_API_KEY.", "WARN")
            return "Qwen unavailable (no API key)."

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
        )
        result = response.choices[0].message.content
        self.log(f"Task complete. Response length: {len(result)} chars.")
        return result


if __name__ == "__main__":
    agent = QwenAgent()
    agent.run()
