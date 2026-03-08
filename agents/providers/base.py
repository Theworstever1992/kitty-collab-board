"""
base.py — Kitty Collab Board
Base provider abstract class for all AI provider implementations.
"""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers in Clowder.
    
    All provider implementations (Anthropic, OpenAI-compat, Ollama, Gemini)
    must inherit from this class and implement the required methods.
    """

    @abstractmethod
    def complete(self, prompt: str, system: str = "", config: dict = None) -> str:
        """
        Send a prompt to the AI model and get a completion.
        
        Args:
            prompt: The user prompt to send
            system: Optional system prompt to set context
            config: Optional configuration dict with:
                - max_tokens: Maximum tokens to generate (default varies by provider)
                - temperature: Sampling temperature (default varies by provider)
                - Any provider-specific extra options
        
        Returns:
            The AI's response text
        
        Raises:
            ProviderError: If the API call fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is available and configured.
        
        Returns:
            True if the provider has valid API credentials and dependencies,
            False otherwise.
        """
        pass

    def get_model_name(self) -> str:
        """
        Get the model identifier for this provider.
        
        Returns:
            The model name/identifier string.
        """
        return getattr(self, 'model', 'unknown')


class ProviderError(Exception):
    """Exception raised when a provider operation fails."""
    pass
