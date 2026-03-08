import urllib.request
import urllib.error
import logging

from agents.providers.base import BaseProvider

# Import retry logic
try:
    from agents.retry import retry_with_backoff
    _retry_available = True
except ImportError:
    _retry_available = False


logger = logging.getLogger(__name__)


class OllamaProvider(BaseProvider):
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=f"{self.base_url}/v1",
                api_key="ollama",
            )
        return self._client

    def _complete_impl(self, prompt: str, system: str = "", config: dict = None) -> str:
        """Internal implementation (without retry)."""
        if config is None:
            config = {}
        max_tokens = config.get("max_tokens", 4096)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "model" in error_str.lower() and ("not found" in error_str.lower() or "pull" in error_str.lower()):
                raise RuntimeError(
                    f"Ollama model '{self.model}' not found locally. "
                    f"Run: ollama pull {self.model}"
                ) from e
            raise RuntimeError(f"Ollama error: {e}") from e

    def complete(self, prompt: str, system: str = "", config: dict = None) -> str:
        """
        Send a prompt to the model and get a completion.
        
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
        try:
            url = f"{self.base_url}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError):
            return False
