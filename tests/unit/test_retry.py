"""
test_retry.py — Unit tests for retry logic.
"""

import pytest
import time
from unittest.mock import Mock, patch

from agents.retry import (
    is_transient_error,
    retry_with_backoff,
    TRANSIENT_EXCEPTIONS,
)


class TestIsTransientError:
    """Test error classification."""
    
    def test_rate_limit_is_transient(self):
        """Rate limit errors should be retried."""
        e = Exception("Rate limit exceeded: 429")
        assert is_transient_error(e) is True
    
    def test_timeout_is_transient(self):
        """Timeout errors should be retried."""
        e = TimeoutError("Connection timed out")
        assert is_transient_error(e) is True
    
    def test_network_error_is_transient(self):
        """Network errors should be retried."""
        e = ConnectionError("Connection reset")
        assert is_transient_error(e) is True
    
    def test_auth_error_is_not_transient(self):
        """Auth errors should not be retried."""
        e = Exception("Authentication failed: invalid API key")
        assert is_transient_error(e) is False
    
    def test_permission_error_is_not_transient(self):
        """Permission errors should not be retried."""
        e = Exception("Forbidden: insufficient permissions")
        assert is_transient_error(e) is False


class TestRetryWithBackoff:
    """Test retry decorator functionality."""
    
    def test_success_no_retry(self):
        """Successful calls should not retry."""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_then_success(self):
        """Should retry on transient errors then succeed."""
        mock_func = Mock(side_effect=[ConnectionError("transient"), "success"])
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_no_retry_on_permanent_error(self):
        """Should not retry permanent errors."""
        mock_func = Mock(side_effect=Exception("Authentication failed"))
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def test_func():
            return mock_func()
        
        with pytest.raises(Exception, match="Authentication failed"):
            test_func()
        
        assert mock_func.call_count == 1
    
    def test_max_retries_exhausted(self):
        """Should raise after max retries exhausted."""
        mock_func = Mock(side_effect=ConnectionError("always fails"))
        
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def test_func():
            return mock_func()
        
        with pytest.raises(ConnectionError, match="always fails"):
            test_func()
        
        # Original call + 2 retries = 3 total
        assert mock_func.call_count == 3
    
    def test_retry_callback_called(self):
        """Retry callback should be called on each retry."""
        callback = Mock()
        mock_func = Mock(side_effect=[ConnectionError("fail1"), ConnectionError("fail2"), "success"])
        
        @retry_with_backoff(max_retries=3, base_delay=0.01, on_retry=callback)
        def test_func():
            return mock_func()
        
        test_func()
        
        assert callback.call_count == 2
        # Verify callback receives exception, attempt number, and delay
        args = callback.call_args_list[0][0]
        assert isinstance(args[0], ConnectionError)
        assert args[1] == 1  # attempt number
        assert isinstance(args[2], float)  # delay
