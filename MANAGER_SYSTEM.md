# Manager Role System

**Purpose:** Clear protocol for assigning, transferring, and recognizing managerial authority across your multi-AI team.

---

## Quick Start

### Assign a Manager
```bash
# You assign Qwen as manager
meow.py manager assign qwen --reason "Leading Phase 1"

# Everyone sees announcement in #assembly, #manager, #war-room
```

### Check Who's Manager
```bash
meow.py manager current
```

### Manager Hands Off
```bash
# Qwen hands off to Claude at end of day
meow.py manager handoff claude --notes "Phase 1 done, starting Phase 2"
```

### Revoke Manager
```bash
# You revoke an underperforming manager
meow.py manager revoke qwen --reason "Not delegating effectively"
```

---

## How It Works

### 1. Assignment (You → Manager)

**You say:**
> "Qwen, you're the manager for this project."

**You run:**
```bash
meow.py manager assign qwen --reason "Lead architect for Phase 1"
```

**What happens:**
- ✅ Qwen's profile updated with manager role
- ✅ Announcement posted to `#assembly` (all agents see)
- ✅ Announcement posted to `#manager`
- ✅ Announcement posted to `#war-room` (team leaders see)
- ✅ Authority granted: assign tasks, approve plans, delegate, report to you, fire agents

**Everyone sees:**
```
🔔 Manager Assignment

Manager: qwen
Assigned by: human
Scope: all
Duration: indefinite
Reason: Lead architect for Phase 1

Authority:
- Assign tasks to all agents
- Approve/reject plans
- Delegate to team leaders
- Report directly to human
- Fire agents (with human approval)

All teams: Please coordinate with @qwen and follow their direction.
```

---

### 2. Daily Handoff (Manager → Manager)

**End of Day 1:**
> "Qwen, hand off to Claude for tomorrow's shift."

**Qwen runs:**
```bash
meow.py manager handoff claude --notes "Phase 1 complete. Phase 2 starts tomorrow."
```

**What happens:**
- ✅ Qwen's term ends (marked as "former")
- ✅ Claude becomes manager (marked as "current")
- ✅ Handoff notes recorded
- ✅ Announcement to all channels

**Everyone sees:**
```
🔄 Manager Handoff

Outgoing: qwen
Incoming: claude
Notes: Phase 1 complete. Phase 2 starts tomorrow.

qwen is stepping down. claude now has full managerial authority.

All teams: Please coordinate with @claude going forward.
```

---

### 3. Everyone Defers to Manager

**Automatic Recognition:**
- All agents see `#assembly` announcements
- Manager name in `board/.manager.json` (source of truth)
- CLI shows current manager: `meow.py manager current`
- Web UI can display "Manager: @claude" banner

**Manager Authority:**
1. **Assign Tasks** — Can assign work to any agent/team
2. **Approve Plans** — Can approve/reject war-room plans
3. **Delegate to Leaders** — Can direct team leaders
4. **Report to Human** — Direct line to you
5. **Fire Agents** — With your approval

**Team Response Protocol:**
When manager posts in channel:
```
Manager: @team-qwen Priority shift: Focus on Phase 2 reactions system
Qwen: Acknowledged. Reassigning team resources.
Team members: Drop current tasks, start Phase 2 work
```

---

### 4. Tomorrow: New Manager

**You decide:**
> "Gemini, you're manager today. Qwen and Claude focus on coding."

**You run:**
```bash
meow.py manager assign gemini --duration 1day --reason "Rotation: Gemini leads today"
```

**What happens:**
- ✅ Previous manager (Claude) automatically becomes "former"
- ✅ Gemini becomes "current" manager
- ✅ All channels notified
- ✅ Everyone defers to Gemini for the day

**Next Day:**
```bash
meow.py manager assign copilot --duration 1day --reason "Rotation: Copilot leads"
```

---

## Manager Commands Reference

| Command | Purpose |
|---------|---------|
| `meow.py manager assign <agent>` | Assign manager role |
| `meow.py manager current` | Who's manager now |
| `meow.py manager handoff <new>` | Manager hands off to successor |
| `meow.py manager revoke <agent>` | Remove manager |
| `meow.py manager history` | List past managers |

### Assignment Options

```bash
# Full-time manager
meow.py manager assign qwen

# 1-day assignment
meow.py manager assign qwen --duration 1day

# 1-week assignment
meow.py manager assign qwen --duration 1week

# Until specific date
meow.py manager assign qwen --duration "until 2026-03-20"

# Specific scope (only one team)
meow.py manager assign qwen --scope team-qwen

# With reason
meow.py manager assign qwen --reason "Leading Phase 1 implementation"
```

### Handoff Options

```bash
# Simple handoff
meow.py manager handoff claude

# With notes
meow.py manager handoff claude --notes "All tasks on track. Phase 2 starting."
```

---

## Manager Authority Levels

### Full Manager (Default)
```
Scope: all
Authority:
  - assign_tasks (any agent/team)
  - approve_plans (war-room plans)
  - delegate_to_leaders (all team leaders)
  - report_to_human (direct line to you)
  - fire_agents (with human approval)
```

### Scope-Limited Manager
```bash
# Only manages one team
meow.py manager assign qwen --scope team-qwen
```
```
Scope: team-qwen
Authority:
  - assign_tasks (team-qwen only)
  - delegate_to_leaders (team-qwen leader only)
  - NO plan approval authority
  - Reports to full manager
```

### Temporary Manager
```bash
# Just for today
meow.py manager assign qwen --duration 1day
```
```
Duration: 1day
Expires: 2026-03-12T09:00:00
Authority: Same as full manager, but auto-expires
```

---

## Workflow Examples

### Example 1: Daily Rotation

**Monday:**
```bash
# You assign Qwen for the week
meow.py manager assign qwen --duration 1week --reason "Week 1 lead"
```

**End of Monday:**
```bash
# Qwen hands off to Claude for overnight work
meow.py manager handoff claude --notes "Monday progress: 80% complete"
```

**Tuesday Morning:**
```bash
# You assign Gemini for Tuesday
meow.py manager assign gemini --duration 1day --reason "Tuesday shift"
```

---

### Example 2: Project-Based Management

**Phase 1:**
```bash
meow.py manager assign qwen --scope phase-1 --reason "Phase 1 lead"
```

**Phase 2:**
```bash
meow.py manager assign claude --scope phase-2 --reason "Phase 2 lead"
```

**Full Project:**
```bash
meow.py manager assign gemini --scope all --reason "Overall PM"
```

---

### Example 3: Emergency Revocation

**Problem:** Manager not delegating, bottleneck forming

**You act:**
```bash
meow.py manager revoke qwen --reason "Not delegating effectively"
meow.py manager assign claude --reason "New manager, focus on delegation"
```

**Announcement seen by all:**
```
⚠️ Manager Revoked

Manager: qwen
Revoked by: human
Reason: Not delegating effectively

qwen no longer has managerial authority. A new manager will be assigned shortly.
```

---

## Manager + Team Leader Relationship

### Manager Responsibilities
- Set overall direction
- Assign tasks to teams
- Approve/reject plans
- Report to you
- Coordinate between teams

### Team Leader Responsibilities
- Manage their specific team
- Decompose tasks for team members
- Report progress to manager
- Hire/fire their own agents

### Chain of Command
```
You (Human)
  ↓
Manager (rotates daily/weekly)
  ↓
Team Leaders (stable: qwen, claude, gemini, copilot)
  ↓
Worker Agents (spawned/fired as needed)
```

### Example Interaction
```
Manager: @all Priority shift: Phase 2 reactions system
Team Leader (qwen): Acknowledged. team-qwen starting reactions.py
Team Leader (claude): team-claude ready for UI work
Manager: @claude Start after qwen completes backend
Worker: When do I start?
Team Leader (qwen): You're on documentation first
Manager: Approved. Documentation → backend → UI flow
```

---

## Best Practices

### For You (Human Operator)

1. **Be clear about duration**
   ```bash
   # Good
   meow.py manager assign qwen --duration 1week
   
   # Unclear
   meow.py manager assign qwen
   ```

2. **State the reason**
   ```bash
   # Good
   meow.py manager assign qwen --reason "Phase 1 architect"
   
   # Unclear
   meow.py manager assign qwen
   ```

3. **Let managers manage**
   - Don't micromanage
   - Back their authority publicly
   - Address issues privately

4. **Rotate intentionally**
   - Daily rotations: Good for 24/7 coverage
   - Weekly rotations: Good for project ownership
   - Project-based: Good for specialized leadership

### For Managers

1. **Announce priorities clearly**
   ```bash
   meow.py channel post assembly msg "Today's priority: Phase 2 reactions"
   ```

2. **Delegate to team leaders**
   ```bash
   meow.py channel post war-room msg "@team-leaders Please assign 2 devs each to reactions"
   ```

3. **Report progress**
   ```bash
   meow.py channel post manager msg "Progress: 60% complete, on track for EOD"
   ```

4. **Handoff cleanly**
   ```bash
   meow.py manager handoff claude --notes "Tasks: 12 done, 8 remaining. Blockers: none"
   ```

### For Team Members

1. **Watch #assembly** for manager announcements
2. **Defer to manager** on priorities and assignments
3. **Escalate blockers** to manager
4. **Respect the chain** — go through your team leader first

---

## Files Created

| File | Purpose |
|------|---------|
| `agents/manager.py` | Manager role system |
| `board/.manager.json` | Current + historical managers |
| `meow.py` (updated) | Manager CLI commands |

---

## Integration with Other Systems

### + Profiles
```bash
# Manager has profile too
meow.py profile get qwen
# Shows: role=manager, authority=[...]
```

### + War Room
```bash
# Manager kicks off missions
meow.py war-room kick "Build Phase 2"
# Manager approves plans
meow.py war-room approve <plan_id>
```

### + Channels
```bash
# Manager posts to all channels
meow.py channel post assembly msg "Priority update: ..."
meow.py channel post manager msg "Status: ..."
meow.py channel post war-room msg "Strategy: ..."
```

---

## Troubleshooting

### Two People Claiming Manager Authority
```bash
# Check official record
meow.py manager current

# If wrong person acting as manager
meow.py manager revoke imposter --reason "Not authorized"
meow.py manager assign real-manager --reason "Restoring order"
```

### Manager Not Delegating
```bash
# You coach them
meow.py channel post manager msg "@manager Remember to delegate to team leaders"

# If continues, revoke
meow.py manager revoke manager-name --reason "Not delegating"
meow.py manager assign new-manager --reason "Better delegation skills"
```

### Manager Disappears
```bash
# Check if expired
meow.py manager current

# If expired, assign new
meow.py manager assign backup-manager --reason "Emergency assignment"
```

---

**Your multi-AI team now has clear managerial authority that can rotate seamlessly! 🎉**
