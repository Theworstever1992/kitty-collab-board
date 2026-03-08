# Offline-First Architecture Design

**Task:** 5011 — Offline-First Architecture Design
**Date:** 2026-03-07
**Status:** ✅ Complete

---

## Overview

The Native GUI application must work offline and sync when reconnected. This document defines the architecture for offline-first operation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Native GUI (Tauri)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   React UI  │  │  Sync Mgr   │  │  SQLite Cache   │  │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │
│         │                │                   │           │
│         └────────────────┴───────────────────┘           │
└─────────────────────────────────────────────────────────┘
                            ↕ (sync when online)
┌─────────────────────────────────────────────────────────┐
│              Backend (FastAPI + board.json)              │
└─────────────────────────────────────────────────────────┘
```

---

## Data Storage

### Local Cache: SQLite

**Why SQLite:**
- Built into Tauri (via rusqlite)
- Fast queries (< 10ms)
- Supports complex queries
- Transaction support
- Cross-platform

**Schema:**
```sql
-- Tasks table
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    prompt TEXT,
    status TEXT NOT NULL,
    role TEXT,
    priority TEXT DEFAULT 'normal',
    priority_order INTEGER DEFAULT 2,
    created_at TEXT,
    claimed_by TEXT,
    claimed_at TEXT,
    completed_by TEXT,
    completed_at TEXT,
    result TEXT,
    handoff_from TEXT,
    handoff_to TEXT,
    handoff_notes TEXT,
    handoff_status TEXT,
    synced INTEGER DEFAULT 0,  -- 0 = not synced, 1 = synced
    local_changes INTEGER DEFAULT 0,  -- 1 = has local changes
    last_synced_at TEXT
);

-- Agents table
CREATE TABLE agents (
    name TEXT PRIMARY KEY,
    model TEXT,
    role TEXT,
    status TEXT,
    started_at TEXT,
    last_seen TEXT,
    synced INTEGER DEFAULT 0,
    last_synced_at TEXT
);

-- Sync queue (operations to send when online)
CREATE TABLE sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,  -- CREATE, UPDATE, DELETE
    entity_type TEXT NOT NULL,  -- task, agent
    entity_id TEXT NOT NULL,
    data TEXT,  -- JSON of changes
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0
);

-- Indexes for performance
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority_order, created_at);
CREATE INDEX idx_tasks_synced ON tasks(synced);
CREATE INDEX idx_sync_queue_created ON sync_queue(created_at);
```

---

## Sync Protocol

### Optimistic Sync

**Principle:** Local changes are applied immediately, synced to backend when online.

**Flow:**
```
1. User creates/updates task offline
       ↓
2. Change saved to SQLite immediately
       ↓
3. Operation queued in sync_queue
       ↓
4. When online: send queued operations
       ↓
5. Backend applies changes to board.json
       ↓
6. On success: mark synced=1, clear from queue
       ↓
7. On conflict: resolve (see below)
```

### Conflict Resolution

**Strategy:** Last-write-wins with manual override

**Rules:**
1. **Same field modified:** Later timestamp wins
2. **Different fields:** Merge changes
3. **Delete vs Update:** Delete wins (task is gone)
4. **User notified:** Show conflict dialog for manual resolution

**Conflict Detection:**
```python
def detect_conflict(local_task, remote_task):
    """Check if local and remote tasks conflict."""
    if local_task is None or remote_task is None:
        return False
    
    # Compare modification times
    local_modified = local_task.get('updated_at', '')
    remote_modified = remote_task.get('updated_at', '')
    
    # If same field modified on both sides, conflict
    local_fields = get_modified_fields(local_task)
    remote_fields = get_modified_fields(remote_task)
    
    return bool(local_fields & remote_fields)
```

---

## Reconnection Detection

### Backend Health Check

```python
async def check_backend_online() -> bool:
    """Check if backend is available."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'http://localhost:8000/api/board',
                timeout=3.0
            ) as resp:
                return resp.status == 200
    except Exception:
        return False
```

### Polling Strategy

- Check every 30 seconds when offline
- Check every 5 minutes when online
- Exponential backoff on repeated failures

---

## UI Indicators

### Sync Status States

| State | Icon | Description |
|-------|------|-------------|
| Online | 🟢 | Connected, syncing |
| Offline | 🔴 | Disconnected, queuing |
| Syncing | 🔄 | Currently syncing |
| Conflict | ⚠️ | Conflicts need resolution |
| Error | ❌ | Sync failed |

### UI Components

**Status Bar:**
```
[🟢 Online] [Last synced: 2 min ago] [0 pending changes]
[🔴 Offline] [12 pending changes] [Will retry in 30s]
[⚠️ Conflicts] [3 tasks need resolution] [Resolve Now]
```

**Task Indicators:**
- Unsynced task: italic title + "●" indicator
- Conflict: red border + "Resolve" button

---

## Queue Operations

### Operation Types

1. **CREATE** — New task created offline
2. **UPDATE** — Task modified offline
3. **DELETE** — Task deleted offline
4. **CLAIM** — Task claimed offline
5. **COMPLETE** — Task completed offline
6. **HANDOFF** — Task handed off offline

### Queue Processing

```python
async def process_sync_queue():
    """Process queued operations when online."""
    queue = await get_pending_operations()
    
    for op in queue:
        try:
            # Send to backend
            response = await send_operation(op)
            
            if response.success:
                # Mark as synced
                await mark_synced(op.entity_id)
                await remove_from_queue(op.id)
            else:
                # Handle error
                await handle_sync_error(op, response.error)
                
        except Exception as e:
            # Increment retry count
            await increment_retry(op.id)
            
            if op.retry_count >= MAX_RETRIES:
                await handle_permanent_failure(op)
```

---

## Implementation Plan

### Phase 1: SQLite Cache (TASK 5012)
- Create database schema
- Implement CRUD operations
- Add indexes for performance

### Phase 2: Sync Manager (TASK 5013)
- Implement sync queue
- Backend communication
- Conflict detection

### Phase 3: Conflict Resolution (TASK 5014)
- Conflict UI dialog
- Manual merge interface
- Last-write-wins fallback

### Phase 4: UI Integration
- Sync status indicator
- Offline mode styling
- Conflict resolution UI

---

## Testing Strategy

### Unit Tests
- SQLite CRUD operations
- Sync queue processing
- Conflict detection logic

### Integration Tests
- Full sync cycle (offline → online → sync)
- Conflict scenarios
- Reconnection handling

### Manual Tests
- Work offline for extended period
- Create/modify many tasks
- Reconnect and verify sync
- Test conflict resolution UI

---

## Success Criteria

- [ ] App works fully offline
- [ ] Changes sync when reconnected
- [ ] Conflicts detected and resolved
- [ ] User always knows sync state
- [ ] No data loss in any scenario
- [ ] Sync is transparent (doesn't block UI)

---

*Design complete. Ready for implementation in TASK 5012-5014.*
