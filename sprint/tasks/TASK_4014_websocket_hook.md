# Task 4014 — WebSocket Hook for Real-Time Updates

**Status:** ✅ done
**Assigned:** Kimi
**Started:** 2026-03-07
**Completed:** 2026-03-07

## Goal
Create reusable WebSocket hook for live board and log updates.

## Implementation

### Files Created
- `web/frontend/src/hooks/useWebSocket.ts`

### Features
- Automatic connection with reconnection
- Configurable reconnect interval (default 3s)
- Callbacks for board updates and logs
- Connection status tracking
- Message sending capability
- Clean disconnect on unmount

### API
```typescript
const { isConnected, lastMessage, sendMessage } = useWebSocket(
  'ws://localhost:8000/api/ws/board',
  {
    onBoardUpdate: (data) => setTasks(data.tasks),
    onLog: (msg) => console.log(msg),
    onConnect: () => console.log('Connected'),
    onDisconnect: () => console.log('Disconnected'),
  }
);
```

### Usage
- TaskBoard: listens for board updates
- AgentPanel: refreshes on board changes
- LogViewer: receives log messages

---
**Status:** ✅ done
**Completed:** 2026-03-07
