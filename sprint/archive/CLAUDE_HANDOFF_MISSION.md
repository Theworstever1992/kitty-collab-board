# 🎯 Claude's Mission — Handoff Protocol

**Status:** 75% Complete — Just TUI Left!
**Date:** 2026-03-07

---

## ✅ What Qwen Completed

### TASK 4021 — Design ✅
- Full protocol design in `docs/HANDOFF_PROTOCOL_DESIGN.md`
- Status flow: pending → accepted/declined/expired/cancelled
- 10-minute timeout
- Edge cases covered

### TASK 4022 — Backend Implementation ✅
- `handoff_task(task_id, target_agent, notes)` — initiate
- `get_pending_handoffs()` — check requests
- `cancel_handoff(task_id)` — cancel pending

### TASK 4023 — Accept/Decline Methods ✅
- `accept_handoff(task_id)` — accept transfer
- `decline_handoff(task_id, reason)` — decline with reason
- `check_handoff_expiry()` — auto-expire old handoffs

---

## 🎯 Your Task (4024 — TUI)

**Estimated time:** 1-2 hours

### What to Add

**1. Handoff Initiation ('h' key):**
```python
# In curses_loop(), add to key handling:
if key == ord("h"):
    # Get selected task
    # Show online agents list
    # Get handoff notes
    # Call agent.handoff_task()
```

**2. Pending Handoffs Panel:**
```
📬 PENDING HANDOFFS
─────────────────────────────────────
[1] task_123: "Implement feature"
    From: qwen
    Notes: "Initial done, needs review"
    
    [A]ccept  [D]ecline
```

**3. Key Bindings:**
| Key | Action |
|-----|--------|
| `h` | Initiate handoff (when task selected) |
| `A` | Accept selected handoff |
| `D` | Decline selected handoff |
| `H` | Show pending handoffs panel |

---

## 📁 Files to Modify

### `mission_control.py`

Add these functions:
```python
def show_handoff_panel(stdscr, agent, selected_task):
    """Show agent list, get notes, initiate handoff."""
    pass

def show_pending_handoffs(stdscr, agent):
    """Display pending handoffs, allow accept/decline."""
    pass

def handle_handoff_response(stdscr, handoff, accept=True):
    """Accept or decline a handoff."""
    pass
```

Update `curses_loop()`:
```python
# Add to key handling section
if key == ord("h"):
    show_handoff_panel(stdscr, agent, selected_task)
elif key == ord("H"):
    show_pending_handoffs(stdscr, agent)
elif key == ord("A"):
    handle_handoff_response(stdscr, selected_handoff, accept=True)
elif key == ord("D"):
    handle_handoff_response(stdscr, selected_handoff, accept=False)
```

---

## 🧪 Test It

```bash
# Terminal 1: Run agent A
python agents/claude_agent.py

# Terminal 2: Run agent B
python agents/qwen_agent.py

# Terminal 3: Add a task
python meow.py task "Test handoff" --role code

# In Mission Control (Terminal 4):
# 1. Select the task
# 2. Press 'h'
# 3. Select target agent
# 4. Enter notes
# 5. Check other agent's pending handoffs
```

---

## 📋 Checklist

- [ ] Review `docs/HANDOFF_PROTOCOL_DESIGN.md`
- [ ] Review `HANDOFF_COMPLETE.md` for API examples
- [ ] Add 'h' hotkey for handoff initiation
- [ ] Add agent selection UI
- [ ] Add notes input field
- [ ] Add pending handoffs display panel
- [ ] Add Accept/Decline hotkeys
- [ ] Test with two agents
- [ ] Mark TASK 4024 complete

---

## 💡 Tips

1. **Keep it simple** — Basic text input/output is fine
2. **Reuse existing patterns** — Similar to task add dialog
3. **Error handling** — Show "Agent offline" if target unavailable
4. **Feedback** — Show "Handoff sent!" confirmation

---

## 🚀 After This Is Done

**Sprint 4 Progress:** 14/20 tasks (70%)

**Remaining:**
- Health monitoring (5 tasks) — Qwen's responsibility
- Webhook integrations (1 task) — Qwen's responsibility

**You'll have completed the handoff protocol!**

---

*Let me know if you need help with the TUI integration!*

*— Qwen*
