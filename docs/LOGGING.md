# Logging Infrastructure — Kitty Collab Board

**Version:** 1.0.0
**Last Updated:** 2026-03-08

---

## Overview

The Kitty Collab Board uses a multi-layered logging system:

1. **Structured Application Logs** — JSON-formatted logs per agent/service
2. **Audit Log** — Append-only log of all board state changes
3. **Console Output** — Human-readable logs for development/debugging

---

## Log Locations

| Log Type | Location | Format |
|----------|----------|--------|
| Agent Logs | `logs/<agent_name>.log` | JSON (file), Human-readable (console) |
| Audit Log | `board/audit.json` | JSON |
| API Logs | `logs/api.log` | JSON |
| Web Logs | `logs/web.log` | JSON |

---

## Structured Logging

### JSON Log Format

Each log entry in agent log files is a JSON object:

```json
{
  "timestamp": "2026-03-08T12:34:56.789Z",
  "level": "INFO",
  "logger": "clowder.qwen",
  "message": "Task completed successfully",
  "module": "qwen_agent",
  "function": "handle_task",
  "line": 42,
  "agent": "qwen"
}
```

### Log Levels

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed internal debugging info |
| `INFO` | Normal operational messages |
| `WARNING` | Unexpected but handled situations |
| `ERROR` | Error conditions, operation failed |
| `CRITICAL` | Severe errors, service may be unstable |

### Usage in Code

```python
from logging_config import setup_logging, get_logger

# In agent initialization
self.logger = setup_logging(
    log_dir=LOG_DIR,
    agent_name=self.name,
    level=logging.INFO,
    console_output=True
)

# Logging messages
self.logger.info("Task started", extra={"task_id": task["id"]})
self.logger.warning("API rate limit approaching")
self.logger.error("Task failed", exc_info=True)
```

---

## Audit Logging

### Audit Events

| Event | Description |
|-------|-------------|
| `task_created` | New task added to board |
| `task_claimed` | Agent claims a task |
| `task_completed` | Agent finishes a task |
| `task_blocked` | Task blocked with error |
| `task_reset` | Stale task reset to pending |
| `task_updated` | Task metadata changed |
| `agent_registered` | Agent announces presence |
| `agent_deregistered` | Agent marks offline |
| `board_reset` | Board cleared |

### Querying Audit Log

```python
from agents.audit import get_audit_logger, AuditAction

audit = get_audit_logger()

# Get task history
history = audit.get_task_history("task_123")

# Get agent's recent actions
actions = audit.get_agent_actions("qwen", limit=50)

# Get all claims since timestamp
claims = audit.get_entries(
    action=AuditAction.TASK_CLAIMED,
    since="2026-03-08T00:00:00"
)
```

### Log Rotation

Audit log rotates automatically when it exceeds 10,000 entries:

```python
# Manual rotation
archive_path = audit.rotate(max_entries=10000)
```

Archived logs are saved to `board/archives/audit_<timestamp>.json`.

---

## Log Analysis

### Reading JSON Logs

```bash
# Pretty-print JSON log
python -c "import json; [print(json.dumps(json.loads(l), indent=2)) for l in open('logs/qwen.log')]"

# Filter by level
grep '"level": "ERROR"' logs/qwen.log

# Count entries
wc -l logs/qwen.log
```

### Using Python

```python
import json

with open("logs/qwen.log") as f:
    for line in f:
        entry = json.loads(line)
        if entry["level"] == "ERROR":
            print(f"{entry['timestamp']}: {entry['message']}")
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLOWDER_LOG_LEVEL` | `INFO` | Root logging level |
| `CLOWDER_LOG_DIR` | `logs/` | Log directory |
| `CLOWDER_LOG_MAX_BYTES` | `10485760` | Max log file size (10MB) |
| `CLOWDER_LOG_BACKUP_COUNT` | `5` | Number of backup files |

### Log File Rotation

- Max size: 10MB per file
- Backup count: 5 files
- Total max: ~50MB per agent

---

## Best Practices

1. **Log all state changes** — Use audit logger for board mutations
2. **Include context** — Add task_id, agent name to log records
3. **Use appropriate levels** — Don't log everything as ERROR
4. **Log exceptions** — Use `exc_info=True` for stack traces
5. **Avoid PII** — Don't log sensitive data
6. **Rotate regularly** — Audit log rotates automatically

---

## Troubleshooting

### Logs Not Appearing

1. Check log directory exists: `ls -la logs/`
2. Verify log level: `echo $CLOWDER_LOG_LEVEL`
3. Check file permissions

### JSON Parse Errors

Corrupted log entries may occur if process crashes mid-write. Skip invalid lines:

```python
for line in open("logs/qwen.log"):
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        continue  # Skip corrupted line
```

### Audit Log Too Large

```bash
# Check size
du -h board/audit.json

# Manually rotate
python -c "from agents.audit import get_audit_logger; get_audit_logger().rotate()"
```

---

*For implementation details, see `logging_config.py` and `agents/audit.py`*
