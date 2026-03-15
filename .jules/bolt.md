## 2025-05-15 - [Bulk Aggregation for Trending Scores]
**Learning:** The trending system was using an N+1 query pattern, calling `compute_trending_score` in a loop for every message that received a reaction in the last 48 hours. Each call performed multiple database queries (get message, count reactions, count replies), leading to O(N) database roundtrips.
**Action:** Replaced the loop with a single bulk SQLAlchemy query using subqueries and aggregations. This reduces database roundtrips to O(1) and leverages the database's efficiency for counting and joining, significantly improving performance for the trending update task.

## 2025-05-15 - [Missing pytest-cov Dependency]
**Learning:** The CI workflow was configured to use `pytest-cov` for coverage reporting, but this package was missing from `requirements.txt`, causing CI to fail with "unrecognized arguments".
**Action:** Added `pytest-cov>=4.1.0` to `requirements.txt` to ensure the testing environment in CI is correctly provisioned.

## 2025-05-15 - [Coverage Threshold Failure]
**Learning:** The CI pipeline had a hard failure threshold of 60% code coverage. The initial optimization of trending scores, while performant, didn't provide enough new test coverage to meet this threshold (total was 58%).
**Action:** Added targeted unit tests for previously untested modules: `agents/onboarding.py` and `agents/token_manager_agent.py`, and expanded tests for `backend/api/trending.py`. Used `respx` for efficient API mocking in agent tests. This ensures both performance and maintainability standards are met.

## 2025-05-15 - [Refinement of Bulk Queries]
**Learning:** While JOINs with subqueries work for bulk aggregations, **scalar subqueries** in the select list are often cleaner and more idiomatic in SQLAlchemy for "count" operations on related tables. They are also easier to read and maintain.
**Action:** Refactored the trending score bulk query to use scalar subqueries for reaction and reply counts.

## 2025-05-15 - [Test Coverage for Agents and APIs]
**Learning:** Reaching coverage thresholds in a multi-component system requires testing both the REST endpoints (FastAPI) and the autonomous agents that consume them. `respx` is invaluable for testing agents without running a full server.
**Action:** Added unit tests for the Ideas API and the Standards Manager agent, pushing project coverage significantly higher.
