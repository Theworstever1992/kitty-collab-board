"""
test_providers.py — Kitty Collab Board
Tests for provider implementations with mocks.
"""

import os
import pytest

from agents.providers.base import BaseProvider, ProviderError


class TestBaseProvider:
    """Tests for BaseProvider abstract class."""
    
    def test_base_provider_is_abstract(self):
        """Test that BaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProvider()
    
    def test_provider_error_exception(self):
        """Test ProviderError exception."""
        error = ProviderError("Test error")
        assert str(error) == "Test error"


class TestOpenAICompatProvider:
    """Tests for OpenAICompatProvider."""
    
    def test_provider_initialization(self):
        """Test OpenAICompatProvider initializes correctly."""
        from agents.providers.openai_compat import OpenAICompatProvider
        
        provider = OpenAICompatProvider(
            api_key="test-key",
            base_url="https://test.api/v1",
            model="test-model"
        )
        
        assert provider.model == "test-model"
        assert provider.base_url == "https://test.api/v1"
        assert provider.api_key == "test-key"
    
    def test_provider_reads_env_key(self):
        """Test provider reads API key from environment."""
        from agents.providers.openai_compat import OpenAICompatProvider
        
        os.environ["TEST_API_KEY"] = "env-key"
        provider = OpenAICompatProvider(api_key_env="TEST_API_KEY")
        
        assert provider.api_key == "env-key"
        os.environ.pop("TEST_API_KEY")
    
    def test_provider_is_available_with_key(self):
        """Test is_available() returns True with valid key."""
        from agents.providers.openai_compat import OpenAICompatProvider
        
        provider = OpenAICompatProvider(api_key="test-key")
        assert provider.is_available() is True
    
    def test_provider_is_available_without_key(self):
        """Test is_available() returns False without key."""
        from agents.providers.openai_compat import OpenAICompatProvider
        
        provider = OpenAICompatProvider(api_key="")
        assert provider.is_available() is False
    
    def test_complete_raises_error_without_client(self):
        """Test complete() raises ProviderError when client unavailable."""
        from agents.providers.openai_compat import OpenAICompatProvider
        
        provider = OpenAICompatProvider(api_key="")
        
        with pytest.raises(ProviderError):
            provider.complete("test prompt")


class TestMockProvider:
    """Tests using mock provider (from conftest)."""
    
    def test_mock_provider_complete(self, mock_provider):
        """Test mock provider returns response."""
        provider = mock_provider()
        result = provider.complete("Hello, world!")
        
        assert "Hello, world!" in result
        assert provider.call_count == 1
    
    def test_mock_provider_available(self, mock_provider):
        """Test mock provider reports available."""
        provider = mock_provider()
        assert provider.is_available() is True
    
    def test_failing_mock_provider(self, failing_mock_provider):
        """Test failing mock provider raises errors."""
        provider = failing_mock_provider(error_message="Always fails")
        
        with pytest.raises(RuntimeError, match="Always fails"):
            provider.complete("test")
        
        assert provider.is_available() is False


class TestProviderConfig:
    """Tests for provider configuration loading."""
    
    def test_config_loader_build_provider(self):
        """Test build_provider() creates correct provider."""
        from agents.config import build_provider
        from agents.providers.openai_compat import OpenAICompatProvider
        
        config = {
            "provider": "openai_compat",
            "model": "test-model",
            "api_key_env": "DASHSCOPE_API_KEY"
        }
        
        provider = build_provider(config)
        assert isinstance(provider, OpenAICompatProvider)
    
    def test_config_loader_unknown_provider(self):
        """Test build_provider() raises error for unknown provider."""
        from agents.config import build_provider
        
        config = {
            "provider": "unknown_provider",
            "model": "test-model"
        }
        
        with pytest.raises(ValueError, match="Unknown provider"):
            build_provider(config)
