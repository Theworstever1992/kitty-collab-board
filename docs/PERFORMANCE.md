# Performance Guide — Kitty Collab Board

**Version:** 1.0.0

---

## Performance Targets

| Metric | Target | Typical |
|--------|--------|---------|
| Agent startup time | < 2s | ~1s |
| Task claim latency | < 100ms | ~50ms |
| Memory per agent | < 200MB | ~100MB |
| Board file size | < 10MB | ~1MB |
| WebSocket latency | < 500ms | ~100ms |
| API response time | < 100ms | ~30ms |

---

## Profiling

### Agent Profiling

```bash
# Profile agent startup
python -m cProfile -o agent_profile.stats agents/generic_agent.py --agent qwen

# Analyze results
python -m pstats agent_profile.stats
# Or use visualization
pip install snakeviz
snakeviz agent_profile.stats
```

### API Profiling

```bash
# Install profiler
pip install py-spy

# Profile running process
py-spy record -o profile.svg --pid $(pgrep -f "uvicorn web.backend.main")
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Run with profiling
python -m memory_profiler agents/generic_agent.py
```

---

## Optimization Techniques

### Board Operations

**Problem:** Large board files slow down reads

**Solutions:**

1. **Archive old tasks:**
   ```python
   # Move completed tasks to archive
   from datetime import datetime, timedelta
   
   cutoff = datetime.now() - timedelta(days=30)
   # Archive tasks older than cutoff
   ```

2. **Cache board data:**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1)
   def get_board_cache():
       return load_board()
   ```

3. **Incremental updates:**
   ```python
   # Only read/write changed tasks
   ```

### File Locking

**Problem:** File locks cause contention

**Solutions:**

1. **Use shorter lock timeouts:**
   ```python
   FileLock("board.json.lock", timeout=5)  # Instead of 10
   ```

2. **Batch operations:**
   ```python
   # Group multiple writes into single locked section
   ```

### Memory Optimization

**Problem:** High memory usage with many tasks

**Solutions:**

1. **Stream large datasets:**
   ```python
   def stream_tasks(board_file):
       with open(board_file) as f:
           for line in f:
               yield json.loads(line)
   ```

2. **Clear caches periodically:**
   ```python
   import gc
   gc.collect()  # Force garbage collection
   ```

3. **Use generators:**
   ```python
   # Instead of list comprehension
   tasks = (t for t in board.get("tasks", []) if t["status"] == "pending")
   ```

---

## Benchmarking

### Run Benchmarks

```bash
# Install benchmark tools
pip install pytest-benchmark

# Run benchmarks
pytest tests/benchmarks.py --benchmark-only
```

### Benchmark Results

| Operation | 10 Tasks | 100 Tasks | 1000 Tasks |
|-----------|----------|-----------|------------|
| Board read | 1ms | 5ms | 50ms |
| Task claim | 10ms | 15ms | 50ms |
| Task complete | 10ms | 15ms | 50ms |

---

## Scaling

### Horizontal Scaling

**Multiple Agent Instances:**

```bash
# Run multiple instances of same agent
python agents/generic_agent.py --agent qwen &
python agents/generic_agent.py --agent qwen &
```

**Load Distribution:**
- Agents automatically distribute tasks
- File locking prevents conflicts

### Vertical Scaling

**Increase Resources:**

```yaml
# docker-compose.yml
services:
  qwen:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 512M
```

---

## Monitoring

### Real-time Monitoring

```bash
# Watch board file size
watch -n 1 'du -h board/board.json'

# Monitor agent memory
ps aux | grep python | grep agent

# Track task completion rate
curl http://localhost:8000/api/analytics/summary
```

### Alerting

**Set up alerts for:**

1. **Agent offline > 5 minutes:**
   ```python
   from agents.health_monitor import HealthMonitor
   monitor = HealthMonitor()
   alerts = monitor.get_alerts()
   ```

2. **High memory usage:**
   ```bash
   # Use system monitoring (Prometheus, etc.)
   ```

3. **Slow task completion:**
   ```python
   # Check metrics
   from agents.metrics import get_metrics_collector
   metrics = get_metrics_collector().get_system_summary()
   ```

---

## Tuning

### Configuration Options

```bash
# Poll interval (seconds)
export CLOWDER_POLL_INTERVAL=5

# Log level
export CLOWDER_LOG_LEVEL=INFO

# Max retries
export CLOWDER_MAX_RETRIES=3

# Retry delay (seconds)
export CLOWDER_RETRY_BASE_DELAY=1.0
```

### Database Backend (Future)

For very large deployments, consider:

- SQLite for local storage
- PostgreSQL for production
- Redis for caching

---

## Best Practices

### Do's

- ✅ Archive old tasks regularly
- ✅ Use role filtering for large task lists
- ✅ Monitor memory usage
- ✅ Set appropriate timeouts
- ✅ Use Docker for isolation

### Don'ts

- ❌ Don't keep > 10000 tasks in active board
- ❌ Don't run agents without monitoring
- ❌ Don't ignore rate limit warnings
- ❌ Don't skip log rotation

---

## Troubleshooting Performance

### Slow Startup

1. Check dependencies load time
2. Reduce initial board read
3. Use lazy loading

### High CPU

1. Profile with `py-spy`
2. Check for tight loops
3. Reduce poll frequency

### Memory Leaks

1. Profile with `memory-profiler`
2. Check for unclosed resources
3. Force garbage collection

---

*For general optimization tips, see `DEVELOPER_GUIDE.md`*
