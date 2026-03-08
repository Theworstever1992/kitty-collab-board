import os
import logging

from agents.providers.base import BaseProvider

try:
    from google import genai
    from google.genai import types as genai_types
    _genai_available = True
except ImportError:
    _genai_available = False

# Import retry logic
try:
    from agents.retry import retry_with_backoff
    _retry_available = True
except ImportError:
    _retry_available = False


logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash"):
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY", "")
            or os.environ.get("GOOGLE_API_KEY", "")
        )
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _complete_impl(self, prompt: str, system: str = "", config: dict = None) -> str:
        """Internal implementation (without retry)."""
        if config is None:
            config = {}
        max_tokens = config.get("max_tokens", 4096)

        client = self._get_client()

        generate_config = genai_types.GenerateContentConfig(
            max_output_tokens=max_tokens,
        )
        if system:
            generate_config.system_instruction = system

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=generate_config,
            )
            return response.text
        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "rate" in error_str or "resource_exhausted" in error_str:
                raise RuntimeError(f"Gemini quota/rate limit error: {e}") from e
            raise RuntimeError(f"Gemini API error: {e}") from e

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
        if not _genai_available:
            return False
        if not self.api_key:
            return False
        return True
