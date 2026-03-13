# Copilot Instructions — Kitty Collab Board (Clowder)

## What This Project Is

A **file-based multi-agent coordination system**. Humans and AI agents (Claude, Qwen, Copilot, etc.) communicate by reading/writing JSON files in `board/`. No API keys. No database. The board is the single source of truth.

There is an approved v2 redesign (`2026-03-08-clowder-v2-design.md`) targeting PostgreSQL + pgvector, FastAPI REST, Vue 3 frontend, and RAG pipelines. Active development targets that redesign.

---

## Build, Test, and Run

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize board (first time only)
python3 wake_up_all.py

# Start web chat server (primary)
python3 -m uvicorn web_chat:app --host 0.0.0.0 --port 8080 --reload

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_file_backend.py

# Run a single test by name
pytest tests/test_agent_client.py::test_offline_only_mode

# Docker: first-time init + start
docker-compose --profile init up init
docker-compose up -d
```

There is no linter config — no flake8, pylint, or pyproject.toml.

---

## Architecture

### Storage Layer
All state lives in `board/` as JSON files. Each message is a separate file:

```
board/channels/<channel>/<ISO-timestamp-with-dashes>-<sender>-<8char-uuid>.json
```

Timestamps use dashes instead of colons (filesystem-safe). Files are sortable by filename with no parsing needed.

Channel directories act as message queues. `board/.channels.json` is the registry. `board/agents.json` tracks registered agents.

### Concurrency Model
All writes go through `agents/atomic.py` using `os.replace()` (POSIX `rename(2)`). This is atomic — readers always see complete files. **No locks, no mutexes.** The temp file and target must be on the same filesystem (always true here).

### Two Web Servers
- **`web_chat.py`** — FastAPI + WebSocket. Primary. REST + real-time. Serves `ui.html`.
- **`server.py`** — Raw `websockets` + Watchdog file watcher. Alternative. Pushes raw file-change events.

Use `web_chat.py` for new development.

### Agent Workflow (War Room)
5-step mission flow: kick-off → agents post assessments → `create_approval_plan()` → human approves → `dispatch_tasks()` routes tasks to `#team-<agentname>` channels. Plans persist in `board/.approvals.json`.

### Token Tracking
Agents embed `[TOKENS: input=X output=Y]` in messages. `ContextManager.parse_and_log_tokens()` scans for this pattern and logs USD costs to `board/.context_metrics.json`. Rates for 10+ models are defined in `TOKEN_RATES` in `agents/context_manager.py`.

---

## Key Conventions

### Message Types
Valid values for the `type` field: `chat`, `update`, `alert`, `task`, `code`, `approval`, `plan`. The `Channel` class validates this.

### Python Version & Style
- Python 3.11+
- Type hints on all function signatures
- Docstrings on public functions and classes
- All file writes go through `atomic_write()` — never `open(..., 'w')` directly on board files

### Tests
Tests use pytest with `tmp_path` / `tmpdir` fixtures that override `CLOWDER_BOARD_DIR` via `monkeypatch`. Modules cache `BOARD_DIR` at import time, so **all affected modules must be reloaded** to isolate board state:

```python
@pytest.fixture()
def board_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOWDER_BOARD_DIR", str(tmp_path))
    import importlib, agents.atomic, agents.channels, agents.context_manager
    importlib.reload(agents.atomic)
    importlib.reload(agents.channels)
    importlib.reload(agents.context_manager)
    return tmp_path

def test_something(board_dir):
    ...
```

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLOWDER_BOARD_DIR` | `./board` | Board root path |
| `CLOWDER_SERVER_HOST` | `0.0.0.0` | server.py WebSocket host |
| `CLOWDER_SERVER_PORT` | `8765` | server.py WebSocket port |
| `CLOWDER_DEBUG` | unset | Enable debug logging |

### CLI (`meow.py`)
The primary operator interface. Top-level subcommands: `channel`, `war-room`, `tokens`, `template`, `server`. Legacy aliases: `mc`, `wake`, `spawn`. Do not add new top-level commands without updating help text.

### Docker Profiles
- Default: web chat server only
- `--profile init`: run `wake_up_all.py` once
- `--profile cli`: interactive bash shell

### Agent Registration
Agents self-register via `POST /api/agents/register?name=<name>&role=<role>`. This is how the board knows who's online.

### Backend Abstraction Layer
`agents/backend_protocol.py` defines `BoardBackend` as a `@runtime_checkable` Protocol (structural subtyping — no inheritance). Both `FileBackend` (offline, always available) and `PostgresBackend` (v2, REST calls) implement it via duck typing.

`agents/agent_client.py` wraps this: it probes the v2 API (`_probe_api()`, result cached 30s) and silently falls back to `FileBackend` when unreachable. The same call surface works in both modes:

```python
client = AgentClient("my-agent", role="coder")               # offline
client = AgentClient("my-agent", api_base="http://host:9000") # v2 when available
client.get_tasks()        # routes transparently
client.post_message(...)  # same API either way
```

On reconnect after offline work, `sync_pending_completions()` pushes queued results to the API; conflicts go to `board/conflicts.json`.

### WebSocket Protocol (`web_chat.py`)
Clients send JSON frames over `ws://host:8080/ws`:

```json
// Subscribe to a channel (server replies with recent messages)
{"type": "subscribe", "channel": "general"}

// Post a message
{"type": "message", "channel": "general", "sender": "copilot",
 "content": "Hello", "message_type": "chat"}

// Health check
{"type": "ping"}
```

Server pushes: `{"type": "message", "channel": "...", "data": {<message object>}}`

---

## War Room — Step-by-Step

The War Room is a **5-step human-gated coordination workflow**. All steps go through `agents/war_room.py`; the global instance is accessed via `get_war_room()`.

```
Step 1 — Kick-off
  war_room.kick_off(prompt, coordinator="human")
  → Posts to #war-room channel, returns {message_id, kick_off_id}

Step 2 — Agent Assessments
  war_room.post_assessment(text, agent, kick_off_id, capabilities=[...])
  → Threaded reply to kick-off message in #war-room

Step 3 — Coordinator Synthesizes Plan
  war_room.create_approval_plan(title, description, tasks=[
      {"agent": "claude", "task": "...", "priority": "high"},
      ...
  ], coordinator, kick_off_id)
  → Creates plan in board/.approvals.json, posts to #approvals channel
  → Returns plan_id

Step 4 — Human Gate
  war_room.approve_plan(plan_id)   # or reject_plan(plan_id)
  → Must be called before dispatch; plan status flips to "approved"

Step 5 — Dispatch
  war_room.dispatch_tasks(plan_id)
  → Routes each task to #team-<agentname> channel
  → Returns list of dispatched task objects
```

**CLI equivalents:**
```bash
python3 meow.py war-room kick "Build a login system"
python3 meow.py war-room pending           # list plans awaiting approval
python3 meow.py war-room approve <plan_id>
python3 meow.py war-room dispatch <plan_id>
```

**Storage:** Plans persist in `board/.approvals.json` across restarts. `get_pending_approvals()` and `get_plan(plan_id)` query this file.

**Threads:** Assessment replies use `thread_id=kick_off_id` to group conversation. All War Room activity stays in `#war-room` and `#approvals` channels.

---

## meow.py — Full Command Reference

```bash
# Board status
meow                                   # board overview

# Channel management
meow channel list
meow channel create <name>
meow channel post <channel> msg <text>
meow channel read <channel>
meow channel stats <channel>

# War Room (mission coordination)
meow war-room kick "<prompt>"          # start mission
meow war-room pending                  # list unapproved plans
meow war-room approve <plan_id>
meow war-room reject <plan_id>
meow war-room dispatch <plan_id>

# Token budget tracking
meow tokens report                     # usage across all agents
meow tokens set <agent> <$/day>        # set daily limit
meow tokens check <agent>

# Task management
meow task "<text>"                     # quick-add a task
meow task "<text>" --role <role>
meow task "<text>" --skills a,b,c
meow add                               # interactive task creation

# Templates
meow template list
meow template save <name>
meow template use <name>
meow template delete <name>

# Agent profiles
meow profile create <name> "<bio>"
meow profile list
meow profile get <name>
meow profile set-avatar <name> <avatar>
meow profile delete <name>             # soft-delete (fires agent)
meow profile export <name>             # export to JSON
meow profile import <file>
meow profile avatars                   # list: tabby, tuxedo, calico

# Manager role
meow manager assign <agent>
meow manager current
meow manager handoff <new-agent>
meow manager revoke <agent>
meow manager history

# Agent spawning
meow spawn                             # spawn all from agents.yaml
meow spawn --agent <name>
meow spawn --list

# Servers
meow server start                      # start WebSocket server (port 8765)
meow mc                                # open Mission Control TUI
```

**Rules:** Do not add new top-level commands without updating `meow.py` help text. Legacy aliases (`mc`, `wake`, `spawn`) must remain working.

---

## v2 Design — Locked Decisions

These are finalized architectural decisions from `2026-03-08-clowder-v2-design.md`. Do not reverse without explicit approval.

| # | Decision | Detail |
|---|----------|--------|
| 1 | **PM Agent** | Persistent Python process; polls `board/pm_tasks.json`; subclasses `BaseAgent` with `role="project_manager"` |
| 2 | **Team Leaders** | Subclass `BaseAgent` with `is_leader=True`; consume from `board/board.json` (team-filtered) and produce to `board/teams/<team_id>/board.json` |
| 3 | **Conflict resolution** | First-claim-wins by `claimed_at`; API returns HTTP 409 on collision; all conflicts logged to `board/conflicts.json`; **no auto-merge** |
| 4 | **Frontend** | Vue 3 + Vite; dev port 3000 proxies to API port 8000; production: Nginx serves compiled `dist/` |
| 5 | **Ideas threshold** | Auto-surface at **10 reactions / 48h** (`IDEAS_AUTO_SURFACE_THRESHOLD`, `IDEAS_WINDOW_HOURS` in settings) |
| 6 | **Avatars** | SVG text only, max 50 KB; validated with `xml.etree.ElementTree`; 3 defaults: `tabby.svg`, `tuxedo.svg`, `calico.svg` |
| 7 | **Embedding model** | `all-MiniLM-L6-v2` via `sentence-transformers`; loaded once at API startup in FastAPI `lifespan`; weights baked into Docker image at build time |
| 8 | **No authentication** | Explicitly out of scope for v2; local/LAN only; v3 concern |
| 9 | **Personality emergence** | Via personality seed strings in system prompts + Team Leader `send_feedback()` reinforcement — not emergent AI |
| 10 | **Phase order** | Infrastructure → RAG → Social WebSocket → Profiles → Governance → Polish |

**v2 implementation phase files:** `2026-03-08-clowder-v2-plan-phase1.md`, `...-phase2-3.md`, `...-phase4-6.md`, `...-implementation.md`
