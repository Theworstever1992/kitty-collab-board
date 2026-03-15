## 2025-05-15 - [Bulk Aggregation for Trending Scores]
**Learning:** The trending system was using an N+1 query pattern, calling `compute_trending_score` in a loop for every message that received a reaction in the last 48 hours. Each call performed multiple database queries (get message, count reactions, count replies), leading to O(N) database roundtrips.
**Action:** Replaced the loop with a single bulk SQLAlchemy query using subqueries and aggregations. This reduces database roundtrips to O(1) and leverages the database's efficiency for counting and joining, significantly improving performance for the trending update task.

## 2025-05-15 - [Missing pytest-cov Dependency]
**Learning:** The CI workflow was configured to use `pytest-cov` for coverage reporting, but this package was missing from `requirements.txt`, causing CI to fail with "unrecognized arguments".
**Action:** Added `pytest-cov>=4.1.0` to `requirements.txt` to ensure the testing environment in CI is correctly provisioned.

## 2025-05-15 - [Coverage Threshold Failure]
**Learning:** The CI pipeline had a hard failure threshold of 60% code coverage. The initial optimization of trending scores, while performant, didn't provide enough new test coverage to meet this threshold (total was 58%).
**Action:** Added targeted unit tests for previously untested modules: `agents/onboarding.py` and `agents/token_manager_agent.py`, and expanded tests for `backend/api/trending.py`. Used `respx` for efficient API mocking in agent tests. This ensures both performance and maintainability standards are met.
