# Kitty Collab Board — Troubleshooting Guide

---

## Board Issues

### Tasks stuck in `in_progress`

An agent claimed a task but crashed before completing it.

**Fix:**
```bash
# Open Mission Control
python meow.py mc

# Or reset the task manually
python -c "
import json
from pathlib import Path

board_file = Path('board/board.json')
board = json.loads(board_file.read_text())
for t in board['tasks']:
    if t['status'] == 'in_progress':
        print(t['id'], t['title'], 'claimed by', t.get('claimed_by'))
        # Uncomment to reset:
        # t['status'] = 'pending'
        # t['claimed_by'] = None
board_file.write_text(json.dumps(board, indent=2))
"
```

If the claiming agent is no longer running, it's safe to reset the task to `pending`.

### `board.json` is corrupted / invalid JSON

```bash
python -c "import json; json.load(open('board/board.json'))"
```

If this raises `json.JSONDecodeError`:

```bash
# Option 1: Restore a backup from archive
python -c "
import json
from pathlib import Path
# board.json is corrupted — create a clean one
board_file = Path('board/board.json')
board_file.write_text(json.dumps({'tasks': []}, indent=2))
print('Reset board.json to empty board')
"

# Option 2: Re-initialize everything
python wake_up.py
```

Note: re-initializing loses in-progress tasks but doesn't delete logs.

### Board file locked / stuck lock

If a process crashed while holding the filelock:

```bash
rm board/board.json.lock
rm board/agents.json.lock
```

Lock files are only used as advisory locks — deleting them is safe if no agent is running.

---

## Agent Issues

### Agent not picking up tasks

1. **Check agent is running**: `python meow.py` shows `last_seen`. If > 5 minutes ago, the agent is likely stopped.
2. **Check role mismatch**: Task has `role: code` but agent has `role: general`. Only matching roles claim tasks.
3. **Check skills mismatch**: Task requires `skills: ["react"]` but agent has no skills (or different skills). Check `board/agents.json` for agent's declared skills.
4. **Check task is actually `pending`**: `python meow.py status` shows task counts. A task might already be `in_progress` by another agent.

```bash
# Check agent registration
python -c "import json; print(json.dumps(json.load(open('board/agents.json')), indent=2))"

# Check pending tasks
python -c "
import json
board = json.load(open('board/board.json'))
for t in board['tasks']:
    if t['status'] == 'pending':
        print(t['id'], '|', t.get('role'), '|', t.get('skills'), '|', t['title'])
"
```

### Agent crashes immediately on startup

Check for missing API keys:
```bash
python -c "import os; print(os.environ.get('ANTHROPIC_API_KEY', 'MISSING'))"
python -c "import os; print(os.environ.get('DASHSCOPE_API_KEY', 'MISSING'))"
```

Check `logs/<agent_name>.log` for the stack trace:
```bash
tail -50 logs/claude.log
```

### Agent keeps marking tasks `blocked`

The agent is failing to process tasks. Common causes:
- API rate limiting (check for 429 errors in logs)
- API key invalid or expired
- Network connectivity issues

```bash
grep "ERROR" logs/claude.log | tail -20
grep "blocked" logs/claude.log | tail -10
```

For rate limiting, the retry logic in `agents/retry.py` should handle transient errors. If tasks keep blocking, the issue is likely a bad API key.

### Agent won't register

```bash
# Check board directory exists and is writable
ls -la board/
touch board/test_write && rm board/test_write && echo "Writable"

# Check CLOWDER_BOARD_DIR if set
echo $CLOWDER_BOARD_DIR
```

---

## API Issues

### API won't start — port in use

```bash
# Find what's on port 8000
lsof -i :8000
# Kill it (replace <PID>)
kill <PID>

# Or start on a different port
uvicorn web.backend.main:app --port 8001
```

### API returns 503 on `/health`

The board directory is missing or inaccessible.

```bash
python wake_up.py  # creates board/ and logs/
```

### API health check passes but frontend can't connect

Check CORS — the frontend must be on `http://localhost:3000` or `http://127.0.0.1:3000`. The API only allows those origins by default.

```bash
# If running frontend on a different port, update CORS in web/backend/main.py:
# allow_origins=["http://localhost:YOUR_PORT"]
```

### WebSocket board updates stop coming

The board watcher polls every 500ms. If it stops:
1. Check the API is still running
2. Reload the frontend page (reconnects WebSocket)
3. Check `board.json` is not locked by a crashed process (delete `.lock` file)

---

## Docker Issues

### Agent containers exit immediately

Check logs:
```bash
docker-compose logs claude-agent
```

Common cause: API health check failing, so agent won't start. Check:
```bash
docker-compose logs api
curl http://localhost:8000/health
```

If the API is unhealthy, `board/` directory may not be mounted:
```bash
docker-compose ps
# Check that volumes are mounted
docker inspect clowder_api_1 | grep Mounts -A 20
```

### `board.json` not visible from host

Check volume mount in `docker-compose.yml`:
```yaml
volumes:
  - ./board:/app/board
```

The `./board` path is relative to `docker-compose.yml`. Run `docker-compose up` from the project root.

### API container health check keeps failing

```bash
docker-compose logs api | tail -20
# Look for startup errors

# Test health check manually inside container
docker exec clowder_api_1 python -c "
import urllib.request
try:
    urllib.request.urlopen('http://localhost:8000/health')
    print('Health check OK')
except Exception as e:
    print('FAILED:', e)
"
```

---

## Frontend Issues

### Frontend shows stale data / not updating

The frontend uses WebSocket for real-time updates. If the connection drops:
1. Hard reload the page (Ctrl+Shift+R)
2. Check browser console for WebSocket errors
3. Verify API is running on port 8000

### `npm run dev` fails

```bash
cd web/frontend
rm -rf node_modules
npm install
npm run dev
```

### TypeScript errors on build

```bash
cd web/frontend
npm run build 2>&1 | head -50
```

Common issue: type mismatches after backend model changes. Check `src/types/index.ts` against `web/backend/main.py` schemas.

---

## Common Commands for Diagnosis

```bash
# Full system status
python meow.py

# Board contents (formatted)
python -c "import json; print(json.dumps(json.load(open('board/board.json')), indent=2))"

# Agent registry
python -c "import json; print(json.dumps(json.load(open('board/agents.json')), indent=2))"

# API health
curl http://localhost:8000/health

# Recent agent errors
grep "ERROR\|WARN" logs/*.log | tail -30

# Task counts
python -c "
import json
board = json.load(open('board/board.json'))
from collections import Counter
counts = Counter(t['status'] for t in board['tasks'])
for status, n in sorted(counts.items()):
    print(f'  {status}: {n}')
"
```

---

## Getting Help

- Check `CLAUDE.md` for architecture overview
- Check `docs/USER_GUIDE.md` for feature usage
- Check `docs/AGENT_DEVELOPER_GUIDE.md` for agent development
- Check `docs/API.md` for API reference
- File issues at the project's GitHub repository
