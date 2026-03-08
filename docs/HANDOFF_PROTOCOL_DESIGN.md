# 🤝 Agent Handoff Protocol — Design Document

**Task:** 4021 — Handoff Protocol Design  
**Assigned:** Claude  
**Status:** 🔄 In Progress (Design Complete)  
**Date:** 2026-03-07  

---

## Overview

The handoff protocol allows agents to explicitly transfer tasks to other agents with context notes, instead of abandoning tasks or leaving them blocked.

---

## Use Cases

### 1. Skill Mismatch
> **Claude (reasoning)** starts a task, realizes it requires heavy code generation → hands off to **Qwen (code)**

### 2. Workload Balancing
> **Agent A** is overloaded with 5 tasks → hands off lower priority tasks to **Agent B** (idle)

### 3. Expertise Transfer
> **Qwen** completes initial implementation → hands off to **Claude** for review/architecture check

### 4. Agent Shutdown
> **Agent** needs to go offline → hands off active tasks to available agents

---

## Data Model

### Task Schema Additions

```json
{
  "id": "task_1234567890",
  "title": "Implement feature X",
  "status": "in_progress",
  "claimed_by": "qwen",
  
  // Handoff fields (NEW)
  "handoff": {
    "from": "qwen",
    "to": "claude",
    "at": "2026-03-07T10:30:00",
    "notes": "Initial implementation done. Needs architecture review.",
    "status": "pending_acceptance"
  }
}
```

### Handoff Status Values

| Status | Meaning |
|--------|---------|
| `pending_acceptance` | Waiting for target agent to accept |
| `accepted` | Target agent accepted, taking over |
| `declined` | Target agent declined |
| `cancelled` | Source agent cancelled handoff |

---

## Protocol Flow

### Phase 1: Initiate Handoff

```
Agent A (source) decides to hand off task
    ↓
Selects target Agent B
    ↓
Adds handoff notes (context, what's done, what's remaining)
    ↓
Calls: handoff_task(task_id, target_agent, notes)
    ↓
Board updated:
  - task.handoff.from = Agent A
  - task.handoff.to = Agent B
  - task.handoff.status = "pending_acceptance"
  - task.status stays "in_progress"
    ↓
Notification sent to Agent B
```

### Phase 2: Target Agent Responds

**Option A: Accept**
```
Agent B receives notification
    ↓
Reviews handoff notes
    ↓
Calls: accept_handoff(task_id)
    ↓
Board updated:
  - task.claimed_by = Agent B
  - task.handoff.status = "accepted"
  - task.handoff.accepted_at = timestamp
    ↓
Agent A notified of acceptance
Agent B now owns the task
```

**Option B: Decline**
```
Agent B receives notification
    ↓
Reviews handoff notes, decides unable to accept
    ↓
Calls: decline_handoff(task_id, reason)
    ↓
Board updated:
  - task.handoff.status = "declined"
  - task.handoff.decline_reason = reason
  - task.handoff.declined_at = timestamp
    ↓
Agent A notified of decline
Task remains with Agent A
```

### Phase 3: Completion or Timeout

**If Accepted:**
- Agent B completes the task normally
- Handoff metadata preserved for audit

**If Declined:**
- Agent A continues with task or finds another agent
- Handoff metadata preserved for audit

**If No Response (timeout: 10 minutes):**
- Handoff expires automatically
- task.handoff.status = "expired"
- Task remains with Agent A

---

## API Design

### BaseAgent Methods

```python
class BaseAgent:
    def handoff_task(self, task_id: str, target_agent: str, notes: str) -> bool:
        """
        Initiate handoff of a task to another agent.
        
        Returns: True if handoff initiated successfully
        """
        pass
    
    def accept_handoff(self, task_id: str) -> bool:
        """
        Accept a handed-off task.
        
        Returns: True if acceptance successful
        """
        pass
    
    def decline_handoff(self, task_id: str, reason: str) -> bool:
        """
        Decline a handed-off task.
        
        Returns: True if decline recorded successfully
        """
        pass
    
    def get_pending_handoffs(self) -> list[dict]:
        """
        Get list of handoff requests waiting for this agent's response.
        
        Returns: List of handoff request dicts
        """
        pass
    
    def cancel_handoff(self, task_id: str) -> bool:
        """
        Cancel a pending handoff (source agent only).
        
        Returns: True if cancellation successful
        """
        pass
```

### Board Schema Changes

```json
{
  "tasks": [
    {
      "id": "task_123",
      "title": "...",
      "status": "in_progress",
      "claimed_by": "qwen",
      
      "handoff": {
        "from": "qwen",
        "to": "claude",
        "at": "2026-03-07T10:30:00",
        "notes": "Context notes here",
        "status": "pending_acceptance",
        "accepted_at": null,
        "declined_at": null,
        "decline_reason": null,
        "expired_at": null
      }
    }
  ]
}
```

---

## Edge Cases

### 1. Target Agent Offline
```
Handoff initiated → Agent B offline
    ↓
Handoff stays "pending_acceptance" for 10 minutes
    ↓
Timeout → handoff expires
    ↓
Agent A notified, task remains with Agent A
```

**Solution:** Check agent status before initiating. If offline, don't allow handoff.

### 2. Task Already Claimed by Another Agent
```
Agent A initiates handoff to Agent B
    ↓
Agent C (different agent) claims task first (race condition)
    ↓
Handoff rejected — task no longer available
```

**Solution:** Use file locking. Check task state atomically during handoff.

### 3. Target Agent Declines
```
Agent A hands off to Agent B
    ↓
Agent B declines with reason
    ↓
Agent A notified
    ↓
Agent A can: continue task, or handoff to different agent
```

**Solution:** Allow Agent A to see decline reason and choose next action.

### 4. Multiple Pending Handoffs
```
Agent A has 3 tasks, wants to hand off all to Agent B
    ↓
Agent B can accept some, decline others
    ↓
Each handoff tracked independently
```

**Solution:** Handoffs are per-task, not batched.

### 5. Circular Handoff
```
Agent A hands off to Agent B
    ↓
Agent B immediately hands off back to Agent A (abuse)
```

**Solution:** Track handoff history. Warn or block if same task handed back to original agent within N minutes.

---

## Notification Mechanism

### In-Memory (Current Sprint)
```python
# Simple approach: check board for pending handoffs
agent.get_pending_handoffs()
```

### Future: WebSocket (Sprint 5)
```python
# Real-time notification via WebSocket
ws.send({"type": "handoff_request", "task_id": "...", "from": "qwen"})
```

### Future: Log-Based
```
[HANDOFF] qwen → claude: task_123 "Implement feature X"
[HANDOFF_ACCEPT] claude accepted task_123
[HANDOFF_DECLINE] claude declined task_123: "Not enough context"
```

---

## UI Requirements

### Mission Control TUI

**Handoff Initiation:**
```
Press 'h' on selected task
    ↓
Show agent list:
  [ ] claude (online, 2 tasks)
  [ ] qwen (online, 1 task)
  [ ] gemini (offline)
    ↓
Select target agent
    ↓
Enter notes: "Initial done, needs review"
    ↓
Handoff initiated!
```

**Pending Handoffs Display:**
```
📬 PENDING HANDOFFS (2)

[1] task_123: "Implement feature X"
    From: qwen → To: claude
    Notes: "Initial done, needs review"
    [A]ccept  [D]ecline

[2] task_456: "Write tests"
    From: qwen → To: claude
    Notes: "Code complete, test coverage needed"
    [A]ccept  [D]ecline
```

### Web GUI

- Handoff button on task card
- Modal with agent selector + notes field
- Notification badge for pending handoffs
- Accept/Decline buttons in notification panel

---

## Implementation Checklist

### Phase 1: Backend (Claude)
- [ ] Add handoff fields to board schema
- [ ] Implement `handoff_task()` method
- [ ] Implement `accept_handoff()` method
- [ ] Implement `decline_handoff()` method
- [ ] Implement `get_pending_handoffs()` method
- [ ] Implement `cancel_handoff()` method
- [ ] Add handoff timeout (10 minutes)
- [ ] Log all handoff events

### Phase 2: TUI (Claude)
- [ ] Add 'h' hotkey for handoff initiation
- [ ] Agent selection UI
- [ ] Notes input field
- [ ] Pending handoffs display
- [ ] Accept/Decline hotkeys

### Phase 3: Web GUI (Claude + Qwen)
- [ ] Handoff button on task card
- [ ] Agent selector modal
- [ ] Notification panel for pending handoffs
- [ ] WebSocket notification (if time permits)

---

## Testing Strategy

### Unit Tests
```python
def test_handoff_initiate():
    """Test that handoff creates correct board state"""
    
def test_handoff_accept():
    """Test that acceptance transfers task ownership"""
    
def test_handoff_decline():
    """Test that decline returns task to source agent"""
    
def test_handoff_timeout():
    """Test that unaccepted handoffs expire"""
    
def test_handoff_offline_agent():
    """Test that handoff to offline agent is rejected"""
```

### Integration Tests
```python
def test_full_handoff_flow():
    """Test complete handoff: initiate → accept → complete"""
    
def test_handoff_decline_then_retry():
    """Test decline then handoff to different agent"""
```

---

## Success Criteria

- [ ] Agents can handoff tasks with context notes
- [ ] Target agents receive and can respond to handoff requests
- [ ] Handoff state is visible in TUI and web GUI
- [ ] Edge cases handled gracefully (offline, decline, timeout)
- [ ] All handoff events logged for audit
- [ ] No race conditions or data corruption

---

## Notes for Implementation

1. **Keep it atomic** — Use file locking for all handoff operations
2. **Log everything** — Handoffs are audit-critical
3. **Timeout is important** — Don't leave handoffs pending forever
4. **Notes are critical** — This is the main value prop (context transfer)
5. **Test edge cases** — Offline agents, declines, race conditions

---

*Design complete. Ready for implementation in TASK 4022.*
