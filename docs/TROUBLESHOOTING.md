# Troubleshooting Guide — Kitty Collab Board

**Version:** 1.0.0

---

## Common Issues

### Agent Issues

#### Agent Won't Start

**Symptoms:**
- Agent exits immediately
- Error in logs

**Solutions:**

1. **Check API keys:**
   ```bash
   echo $ANTHROPIC_API_KEY
   echo $DASHSCOPE_API_KEY
   ```

2. **Check dependencies:**
   ```bash
   pip list | grep anthropic
   pip list | grep openai
   ```

3. **Check logs:**
   ```bash
   cat logs/qwen.log | tail -50
   ```

#### Agent Crashes Repeatedly

**Symptoms:**
- Agent starts then stops
- Error: "API rate limit"

**Solutions:**

1. **Wait for rate limit reset** (usually 1 hour)
2. **Reduce poll frequency:**
   ```bash
   export CLOWDER_POLL_INTERVAL=10  # seconds
   ```
3. **Check API status:**
   - Anthropic: https://status.anthropic.com
   - DashScope: Check Alibaba Cloud status

#### Task Not Being Claimed

**Symptoms:**
- Task stays pending
- Agents are online

**Solutions:**

1. **Check role matching:**
   ```bash
   # Task role must match agent role or be null
   python -c "import json; t=json.load(open('board/board.json')); print([x.get('role') for x in t['tasks']])"
   ```

2. **Check dependencies:**
   ```bash
   python -c "from agents.dependencies import get_dependency_manager; print(get_dependency_manager().get_dependencies('task_123'))"
   ```

3. **Check if blocked:**
   ```bash
   # Task status should not be 'blocked'
   ```

---

### Board Issues

#### Board File Corrupted

**Symptoms:**
- JSON decode errors
- Agents won't start

**Solutions:**

1. **Backup and reset:**
   ```bash
   cp board/board.json board/board.json.bak
   echo '{"tasks": []}' > board/board.json
   ```

2. **Restore from backup:**
   ```bash
   cp board/board.json.bak board/board.json
   ```

#### Tasks Disappeared

**Symptoms:**
- Tasks missing from board

**Solutions:**

1. **Check audit log:**
   ```bash
   cat board/audit.json | python -m json.tool
   ```

2. **Check if archived:**
   ```bash
   ls -la board/archives/
   ```

3. **Check multi-board:**
   ```bash
   python -c "from agents.multiboard import get_active_board; print(get_active_board())"
   ```

---

### Web Dashboard Issues

#### Frontend Won't Load

**Symptoms:**
- Blank page
- Console errors

**Solutions:**

1. **Check API is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check CORS:**
   ```bash
   # In browser console
   fetch('http://localhost:8000/api/board')
   ```

3. **Rebuild frontend:**
   ```bash
   cd web/frontend
   npm install
   npm run build
   ```

#### WebSocket Not Connecting

**Symptoms:**
- Dashboard doesn't update in real-time

**Solutions:**

1. **Check WebSocket endpoint:**
   ```bash
   # In browser console
   const ws = new WebSocket('ws://localhost:8000/api/ws/board');
   ws.onopen = () => console.log('Connected');
   ws.onerror = (e) => console.log('Error:', e);
   ```

2. **Check firewall:**
   ```bash
   # Port 8000 should allow WebSocket connections
   ```

---

### Performance Issues

#### Slow Task Claiming

**Symptoms:**
- Tasks take > 10 seconds to be claimed

**Solutions:**

1. **Check file locking:**
   ```bash
   pip install filelock
   ```

2. **Reduce poll interval:**
   ```bash
   export CLOWDER_POLL_INTERVAL=2  # seconds
   ```

3. **Check board size:**
   ```bash
   python -c "import json; print(len(json.load(open('board/board.json'))['tasks']))"
   ```

#### High Memory Usage

**Symptoms:**
- Agent uses > 500MB RAM

**Solutions:**

1. **Archive old tasks:**
   ```python
   from agents.multiboard import get_multiboard_manager
   manager = get_multiboard_manager()
   # Manually archive or delete old boards
   ```

2. **Restart agents periodically:**
   ```bash
   # Use supervisor or systemd to auto-restart
   ```

---

### Docker Issues

#### Container Won't Start

**Symptoms:**
- `docker-compose up` fails

**Solutions:**

1. **Check volumes:**
   ```bash
   ls -la board/
   ls -la logs/
   ```

2. **Check environment:**
   ```bash
   docker-compose config
   ```

3. **View container logs:**
   ```bash
   docker-compose logs api
   ```

#### Volume Permission Errors

**Symptoms:**
- "Permission denied" in logs

**Solutions:**

```bash
# Fix permissions
sudo chown -R $(id -u):$(id -g) board/ logs/
```

---

## Diagnostic Commands

### Quick Health Check

```bash
# Check API
curl http://localhost:8000/health

# Check agents
curl http://localhost:8000/api/health

# Check board
python -c "import json; b=json.load(open('board/board.json')); print(f'Tasks: {len(b[\"tasks\"])}')"

# Check logs
tail -20 logs/api.log
```

### Full Diagnostic Script

```bash
#!/bin/bash
echo "=== Clowder Diagnostic ==="
echo ""
echo "1. API Health:"
curl -s http://localhost:8000/health | python -m json.tool
echo ""
echo "2. Board Status:"
python -c "import json; b=json.load(open('board/board.json')); print(f'Tasks: {len(b[\"tasks\"])}')"
echo ""
echo "3. Agent Status:"
python -c "import json; a=json.load(open('board/agents.json')); print(a)"
echo ""
echo "4. Recent Logs:"
tail -10 logs/api.log
```

---

## Getting Help

### Logs Location

- Agent logs: `logs/<agent_name>.log`
- API logs: `logs/api.log`
- Audit log: `board/audit.json`
- Metrics: `board/metrics.json`

### Support Channels

- GitHub Issues: https://github.com/theworstever1992/kitty-collab-board/issues
- Documentation: `docs/` directory

---

## Error Codes

### API Errors

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad Request | Check request body |
| 404 | Not Found | Check task/agent ID |
| 422 | Validation Error | Check field values |
| 503 | Service Unavailable | Check API is running |

### Agent Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| "No API key" | Missing credentials | Set env vars |
| "Rate limit" | API quota exceeded | Wait or upgrade plan |
| "Task not found" | Task deleted | Refresh board |

---

*For general usage, see `USER_GUIDE.md`*
