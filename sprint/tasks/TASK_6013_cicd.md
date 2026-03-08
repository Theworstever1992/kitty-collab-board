# TASK 6013 — CI/CD Pipeline (GitHub Actions)

**Sprint:** 6 | **Phase:** 9 (Deployment) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Summary

Created `.github/workflows/test.yml` — a GitHub Actions workflow that runs the full test suite on every push and PR to `main`, across Python 3.11 and 3.12.

## Implementation

### Workflow: `.github/workflows/test.yml`

```yaml
on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: python wake_up.py
        env:
          ANTHROPIC_API_KEY: dummy-for-tests
      - run: pytest tests/ -v --tb=short
        env:
          ANTHROPIC_API_KEY: dummy-for-tests
          DASHSCOPE_API_KEY: dummy-for-tests
          CLOWDER_BOARD_DIR: /tmp/clowder-test-board
          CLOWDER_LOG_DIR: /tmp/clowder-test-logs
```

### Key decisions

- `wake_up.py` runs before tests to ensure `board/` directory exists (tests need it)
- Dummy API keys prevent SDK auth failures during unit tests — no real calls made
- `CLOWDER_BOARD_DIR` points to `/tmp` so tests don't write to project directory
- Matrix across 3.11 and 3.12 catches syntax/compatibility regressions

## Files Created

- `.github/workflows/test.yml`

## Notes

- Separate Docker publish workflow already exists (`.github/workflows/docker-publish.yml`)
- No deploy step added — single-machine deployment, not CD target yet
