# Testing Guide

## Test Organization

Tests are organized by component in `tests/`:
- `test_board.py` — Board operations
- `test_agent.py` — Agent functionality
- `test_providers.py` — Provider integrations
- `test_dependencies.py` — Task dependencies
- `test_recurring.py` — Recurring tasks
- `test_multiboard.py` — Multi-board support
- `unit/` — Unit tests for specific modules

## Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_board.py -v

# Run specific test
pytest tests/test_board.py::TestClaimTask::test_claim_task -v

# Show coverage
pytest --cov=agents --cov=web

# Stop on first failure
pytest -x
```

## Coverage

Target: 80%+ coverage of critical paths

Key areas:
- Board operations (claim, complete, handoff)
- Agent lifecycle (register, heartbeat, deregister)
- Dependency resolution
- Task recurrence
- Performance (startup, latency, memory)
- Multi-board isolation

## CI/CD Testing

GitHub Actions runs:
1. Linting (black, flake8, eslint)
2. Unit tests (pytest)
3. Integration tests
4. Coverage report

All must pass before merge.

## Performance Testing

Use `agents/profiler.py`:
```python
from agents.profiler import PerformanceProfiler
profiler = PerformanceProfiler("agent")
elapsed, result = profiler.profile_startup(startup_func)
print(profiler.report())
```

Targets:
- Startup: <2s
- Claim latency: <100ms
- Memory: <200MB
- Board size: <10MB
