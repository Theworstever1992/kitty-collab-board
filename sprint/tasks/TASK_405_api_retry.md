# TASK 405 — API Retry with Exponential Backoff

**Assigned:** Qwen
**Status:** ✅ done
**Completed:** 2026-03-07
**Completed by:** Kimi
**Started:** 2026-03-06
**Phase:** 5 — Reliability (Sprint 2)

## Description

Add retry logic with exponential backoff to provider API calls.
Transient failures should retry before marking task blocked.

## Implementation Notes

Kimi completed the API retry implementation:

**Created `agents/retry.py`:**
- `is_transient_error()` — classifies errors as transient/permanent
- `retry_with_backoff()` — decorator with exponential backoff
- `RetryableProvider` mixin class for easy integration
- Supports: 1s, 2s, 4s, 8s, 16s delays (max 5 retries)
- Detects rate limits, timeouts, network errors (retriable)
- Detects auth failures, permission errors (non-retriable)

**Updated all providers:**
- `anthropic_provider.py` — retry wrapper on `complete()`
- `openai_compat.py` — retry wrapper on `complete()`
- `gemini.py` — retry wrapper on `complete()`
- `ollama.py` — retry wrapper on `complete()`

**Created `tests/unit/test_retry.py`:**
- Tests for error classification
- Tests for retry behavior
- Tests for callback functionality

## Requirements

- [x] Retry decorator or wrapper in providers
- [ ] Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 5 retries)
- [ ] Only retry transient errors:
  - RateLimitError
  - Timeout
  - Network errors
- [ ] Don't retry permanent errors (auth failure, invalid request)
- [ ] Log retry attempts

## Acceptance Criteria

- [ ] Transient failures retry automatically
- [ ] Backoff increases exponentially
- [ ] Task marked blocked only after all retries exhausted
- [ ] Permanent errors fail immediately (no retry)

## Review

_Claude reviews here_
