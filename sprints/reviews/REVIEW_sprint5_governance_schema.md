# REVIEW: Sprint 5 — Governance Schema
**Reviewer:** Qwen agent
**Date:** 2026-03-12
**File reviewed:** `backend/models.py`

---

## 1. Full Model Inventory

| Class | Table | Primary Key | Key Fields |
|---|---|---|---|
| `Task` | `tasks` | `id` (String 64) | `status`, `team_id`, `priority`, `claimed_by`, `completed_at`, `created_at` |
| `Agent` | `agents` | `name` (String 128) | `role`, `model`, `team`, `status`, `last_seen`, `hired_at`, `fired_at` |
| `ChatMessage` | `chat_messages` | `id` (String 64) | `channel`, `sender`, `type`, `thread_id`, `timestamp`, `embedding` |
| `TokenUsage` | `token_usage` | `id` (int autoincrement) | `agent`, `model`, `input_tokens`, `output_tokens`, `cost_usd`, `logged_at` |
| `Team` | `teams` | `id` (String 64) | `name`, `leader_id`, `created_at` |
| `TaskHistory` | `task_history` | `id` (int autoincrement) | `task_id`, `status_change`, `changed_by`, `timestamp` |
| `TaskEmbedding` | `task_embeddings` | `id` (int autoincrement) | `task_id`, `embedding`, `summary_text`, `created_at` |
| `ContextItem` | `context_items` | `id` (int autoincrement) | `source_type`, `source_id`, `content`, `embedding`, `tags`, `created_at` |
| `MessageReaction` | `message_reactions` | `id` (int autoincrement) | `message_id`, `reactor_id`, `reaction_type`, `created_at` |
| `TrendingDiscussion` | `trending_discussions` | `id` (int autoincrement) | `message_id`, `current_score`, `window_start`, `created_at` |
| `Idea` | `ideas` | `id` (int autoincrement) | `author_id`, `title`, `status`, `approved_by`, `source_message_id`, `created_at` |
| `IdeaVote` | `idea_votes` | `id` (int autoincrement) | `idea_id`, `voter_id`, `created_at` |
| `StandardsViolation` | `standards_violations` | `id` (int autoincrement) | `violation_type`, `agent_id`, `task_id`, `severity`, `notes`, `flagged_at` |
| `AgentExport` | `agent_exports` | `id` (int autoincrement) | `agent_id`, `export_format`, `content`, `created_at` |
| `RetrievalLog` | `retrieval_logs` | `id` (int autoincrement) | `agent_id`, `query_text`, `results_returned`, `timestamp` |
| `LeaderMeeting` | `leader_meetings` | `id` (int autoincrement) | `agenda`, `participants`, `decisions`, `created_at` |

---

## 2. `Idea.approved_by` Field Issue

### Current State

```python
class Idea(Base):
    ...
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(128))
```

**Issue confirmed:** `Idea` has only `approved_by` and no separate `rejected_by` field. The `status` column can hold `"rejected"` but there is no field to record *who* performed the rejection. The `approved_by` column is semantically misleading when `status = "rejected"`.

### Recommendation

Two options, in order of preference:

**Option A — Rename to `reviewed_by` (preferred):**
```python
reviewed_by: Mapped[Optional[str]] = mapped_column(String(128))
reviewer_note: Mapped[Optional[str]] = mapped_column(Text)
```
- `reviewed_by` is reviewer-neutral; it records whoever set the final status regardless of outcome.
- `reviewer_note` captures the reason for rejection or conditions for approval.
- Requires an Alembic migration to rename the column (see section 4).

**Option B — Add `rejected_by` alongside `approved_by`:**
```python
approved_by: Mapped[Optional[str]] = mapped_column(String(128))
rejected_by: Mapped[Optional[str]] = mapped_column(String(128))
reviewer_note: Mapped[Optional[str]] = mapped_column(Text)
```
- Non-breaking addition (no rename migration needed), but leaves two nullable columns with at most one populated per row — awkward to query.

**Recommendation: Option A.** The rename is a one-migration cost paid once; the cleaner schema pays dividends forever. The API layer should also update any `approved_by` references in `backend/api/ideas.py`.

---

## 3. Missing Indexes — Governance Query Recommendations

### `StandardsViolation` — repeat offender queries

Current indexes on `standards_violations`:
- `violation_type` (index=True)
- `agent_id` (index=True)  ✅ Already present

The `agent_id` index is already in place. No action needed for repeat-offender queries like:

```sql
SELECT agent_id, COUNT(*) AS violations
FROM standards_violations
GROUP BY agent_id
ORDER BY violations DESC;
```

**Additional recommendation:** A composite index on `(agent_id, flagged_at)` would accelerate time-windowed repeat-offender queries (e.g., violations in the last 30 days). This is not yet present.

```python
# Recommended addition to StandardsViolation:
__table_args__ = (
    Index("ix_sv_agent_flagged", "agent_id", "flagged_at"),
)
```

### `TokenUsage` — per-agent token reports

Current indexes on `token_usage`:
- `agent` (index=True)  ✅ Already present

The `agent` index covers basic per-agent aggregation queries:

```sql
SELECT agent, SUM(input_tokens), SUM(output_tokens), SUM(cost_usd)
FROM token_usage
GROUP BY agent;
```

**Additional recommendation:** A composite index on `(agent, logged_at)` would accelerate time-bounded efficiency queries (daily/weekly cost reports). Not yet present.

```python
# Recommended addition to TokenUsage:
__table_args__ = (
    Index("ix_tu_agent_logged", "agent", "logged_at"),
)
```

### `TaskHistory` — audit trail queries

`task_history` has an index on `task_id` but no index on `changed_by`. Governance queries for "all changes made by agent X" will do a full table scan.

**Recommendation:** Add `index=True` to `changed_by`:

```python
changed_by: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
```

---

## 4. Alembic Migration Note — `create_tables()` Behavior

`create_tables()` in `backend/database.py` calls `Base.metadata.create_all`. This is **additive only**:

- New tables (e.g., `leader_meetings`) are created automatically on next startup.
- New columns added to existing models are **NOT** applied to an already-created table. SQLAlchemy does not diff existing schemas.
- Column renames (e.g., `approved_by` → `reviewed_by`) are **NOT** applied.

**Implication for `LeaderMeeting`:** The new `leader_meetings` table will be created automatically on next server startup in a fresh database. No Alembic migration is needed for this sprint if the database has not yet been provisioned.

**Implication for the `Idea.approved_by` rename:** This change requires an explicit Alembic migration:

```bash
alembic revision --autogenerate -m "rename idea approved_by to reviewed_by, add reviewer_note"
alembic upgrade head
```

Until Alembic is configured (no `alembic.ini` exists in the repo yet), the rename must be applied manually via raw SQL on any existing database:

```sql
ALTER TABLE ideas RENAME COLUMN approved_by TO reviewed_by;
ALTER TABLE ideas ADD COLUMN reviewer_note TEXT;
```

---

## 5. DateTime Timezone Consistency Audit

All `DateTime` columns across all models were inspected. **All use `DateTime(timezone=True)`** consistently. No timezone-naive DateTime columns found.

Summary by model:

| Model | Column | timezone=True |
|---|---|---|
| Task | `completed_at`, `created_at` | Yes |
| Agent | `last_seen`, `started_at`, `hired_at`, `fired_at` | Yes |
| ChatMessage | `timestamp` | Yes |
| TokenUsage | `logged_at` | Yes |
| Team | `created_at` | Yes |
| TaskHistory | `timestamp` | Yes |
| TaskEmbedding | `created_at` | Yes |
| ContextItem | `created_at` | Yes |
| MessageReaction | `created_at` | Yes |
| TrendingDiscussion | `window_start`, `created_at` | Yes |
| Idea | `created_at` | Yes |
| IdeaVote | `created_at` | Yes |
| StandardsViolation | `flagged_at` | Yes |
| AgentExport | `created_at` | Yes |
| RetrievalLog | `timestamp` | Yes |
| LeaderMeeting | `created_at` | Yes |

No issues found. The schema is timezone-consistent throughout.

---

## 6. Changes Made This Sprint

- **Added `LeaderMeeting` model** to `backend/models.py` (after `RetrievalLog`, before end of file). Table: `leader_meetings`. Fields: `id`, `agenda` (JSON), `participants` (JSON), `decisions` (JSON), `created_at` (DateTime with timezone).
- **No other models were modified.** The `approved_by` rename is recommended but deferred pending Alembic setup.
