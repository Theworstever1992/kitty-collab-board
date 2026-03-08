"""
openai_compat.py — Kitty Collab Board
OpenAI-compatible provider supporting Qwen, OpenAI, Together, Groq, etc.
"""

import os
import logging
from typing import Optional

from agents.providers.base import BaseProvider, ProviderError

try:
    from openai import OpenAI, APIError, RateLimitError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Import retry logic
try:
    from agents.retry import retry_with_backoff
    _retry_available = True
except ImportError:
    _retry_available = False


logger = logging.getLogger(__name__)


class OpenAICompatProvider(BaseProvider):
    """
    OpenAI-compatible provider using the official OpenAI SDK.
    
    Supports any OpenAI-compatible endpoint:
    - OpenAI (api.openai.com)
    - Qwen/DashScope (dashscope.aliyuncs.com)
    - Together AI
    - Groq
    - Local models via OpenAI-compatible servers
    
    Configuration via environment variables or constructor args.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o",
        api_key_env: Optional[str] = None,
    ):
        """
        Initialize the OpenAI-compatible provider.
        
        Args:
            api_key: API key directly (optional, will check env vars)
            base_url: Base URL for the API endpoint
            model: Default model identifier to use
            api_key_env: Environment variable name for API key
                        (default: tries OPENAI_API_KEY, then DASHSCOPE_API_KEY)
        """
        self.model = model
        self.base_url = base_url
        
        # Determine API key
        if api_key:
            self.api_key = api_key
        elif api_key_env:
            self.api_key = os.environ.get(api_key_env, "")
        else:
            # Try common env var names
            self.api_key = (
                os.environ.get("OPENAI_API_KEY", "") or
                os.environ.get("DASHSCOPE_API_KEY", "")
            )
        
        self.client = None
        if OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=base_url)

    def _complete_impl(self, prompt: str, system: str = "", config: dict = None) -> str:
        """Internal implementation (without retry)."""
        if not self.client:
            raise ProviderError(
                "OpenAICompatProvider not available — check API key and openai package"
            )
        
        config = config or {}
        max_tokens = config.get("max_tokens", 4096)
        temperature = config.get("temperature", 0.7)
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            raise ProviderError(f"Rate limit exceeded: {e}")
        except APIError as e:
            raise ProviderError(f"API error: {e}")
        except Exception as e:
            raise ProviderError(f"Unexpected error: {e}")

    def complete(self, prompt: str, system: str = "", config: dict = None) -> str:
        """
        Send a prompt to the model and get a completion.
        
        TASK 405: Includes automatic retry with exponential backoff for transient errors.
        
        Args:
            prompt: User prompt
            system: Optional system prompt
            config: Optional config with max_tokens, temperature
        
        Returns:
            Model response text
        
        Raises:
            ProviderError: If API call fails
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
        """
        Check if provider is available.
        
        Returns:
            True if SDK is installed and API key is set
        """
        return OPENAI_AVAILABLE and bool(self.api_key)
