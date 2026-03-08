import os
import logging
import functools

from agents.providers.base import BaseProvider

try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False

# Import retry logic
try:
    from agents.retry import retry_with_backoff
    _retry_available = True
except ImportError:
    _retry_available = False


logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def _complete_impl(self, prompt: str, system: str = "", config: dict = None) -> str:
        """Internal implementation of complete (without retry)."""
        if config is None:
            config = {}
        max_tokens = config.get("max_tokens", 4096)

        try:
            client = self._get_client()
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except anthropic.APIError as e:
            raise RuntimeError(f"Anthropic API error: {e}") from e

    def complete(self, prompt: str, system: str = "", config: dict = None) -> str:
        """
        Send a prompt to the AI model and get a completion.
        
        TASK 405: Includes automatic retry with exponential backoff for transient errors.
        """
        # Apply retry wrapper dynamically
        if _retry_available:
            retry_wrapper = retry_with_backoff(
                max_retries=5,
                base_delay=1.0,
                logger=logger,
            )
            return retry_wrapper(self._complete_impl)(prompt, system, config)
        else:
            # Fallback without retry
            return self._complete_impl(prompt, system, config)

    def is_available(self) -> bool:
        if not _anthropic_available:
            return False
        if not self.api_key:
            return False
        return True
