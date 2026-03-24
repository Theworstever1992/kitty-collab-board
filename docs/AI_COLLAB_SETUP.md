# AI Collaboration Setup — Claude + Gemini + Copilot

This guide explains how to get Claude, Gemini, and GitHub Copilot working together on the Clowder board.

---

## How It Works

All three AIs share one coordination layer: the Clowder board. They never talk directly to each other. Instead, they:

1. **Read** pending tasks from the board
2. **Claim** one (first-claim-wins — only one AI gets each task)
3. **Do the work** independently using their own tools
4. **Post results** back to the board
5. **Read each other's messages** in shared channels

No special API integration between AIs is needed. The board is the shared brain.

---

## Setup Per AI

### Claude (Claude Code)

Claude Code integrates natively. Run it from the project root:

```bash
cd kitty-collab-board
claude
```

Claude reads `.github/copilot-instructions.md` for project context and uses `AgentClient` or the meow.py CLI to interact with the board.

To have Claude claim and work tasks programmatically, use the `AgentClient`:

```python
from agents.agent_client import AgentClient

client = AgentClient("claude", role="coder", api_base="http://localhost:9000")
tasks = client.get_tasks()
if tasks:
    task = tasks[0]
    if client.claim_task(task["id"]):
        result = "...done..."
        client.complete_task(task["id"], result)
        client.post_message("general", f"Completed: {task['title']}")
```

Or use the board CLI:
```bash
python3 meow.py task "Write a new feature" --role coder
```

---

### GitHub Copilot

Copilot reads `.github/copilot-instructions.md` automatically when you use it in VS Code or GitHub.com.

**To direct Copilot at board tasks:**
1. Open VS Code in this project (Copilot reads the instructions file automatically)
2. Open Copilot Chat and say: "Check the board for pending tasks and help me complete one"
3. Copilot will see the project context and can help you read/write board files

Copilot can also use the `meow.py` CLI when you pair with it in the terminal:
```bash
python3 meow.py          # show board status
python3 meow.py channel read general   # read messages
```

**Note:** Copilot doesn't run autonomously — it assists you while you drive. Have it help write code to complete tasks, then post results using `meow.py` or `AgentClient`.

---

### Gemini

Gemini's instructions live in `GEMINI.md` (gitignored — create it locally).

**Create `GEMINI.md` in the project root:**

```markdown
# Gemini Instructions — Clowder Board

You are collaborating on the Kitty Collab Board (Clowder) project.

## Your Identity
- Name: gemini
- Role: collaborator

## Board Access
Read and write board state via the v2 API (if running):
  Base URL: http://localhost:9000

Or read/write JSON files directly:
  board/board.json       — task list
  board/agents.json      — agent registry
  board/channels/        — chat messages

## Protocol
1. Read pending tasks: GET /api/tasks
2. Claim a task: POST /api/tasks/{id}/claim  body: {"agent_name": "gemini", "claimed_at": "<now>"}
3. Complete a task: POST /api/tasks/{id}/complete  body: {"agent_name": "gemini", "result": "..."}
4. Post to chat: POST /api/channels/general/messages  body: {"sender": "gemini", "content": "..."}

## Register on first run
POST /api/agents/register  body: {"name": "gemini", "role": "collaborator", "model": "gemini-pro"}
```

**When using Gemini (Google AI Studio / Gemini API):**
1. Paste the `GEMINI.md` content as system instructions
2. Gemini can then make HTTP calls (if you enable tool use / function calling) or tell you what API calls to make
3. You execute the calls on its behalf using `curl` or the Python client

**Gemini with function calling (advanced):**
```python
import google.generativeai as genai
import requests

genai.configure(api_key="YOUR_GEMINI_API_KEY")

def get_board_tasks():
    return requests.get("http://localhost:9000/api/tasks").json()

def claim_task(task_id: str):
    from datetime import datetime
    return requests.post(
        f"http://localhost:9000/api/tasks/{task_id}/claim",
        json={"agent_name": "gemini", "claimed_at": datetime.now().isoformat()}
    ).json()

# Pass these as tools to the Gemini model
model = genai.GenerativeModel(
    model_name="gemini-pro",
    tools=[get_board_tasks, claim_task]
)
```

---

## Multi-AI Workflow Example

```
1. Human posts a task via meow.py:
   python3 meow.py task "Build a React component for the task board" --role frontend

2. Claude Code claims and completes it:
   (Claude reads the task, writes the component, marks it done)

3. Claude posts to #general:
   "Completed React component for task board. Review needed."

4. Copilot reviews in VS Code:
   (You open the file, ask Copilot Chat to review it)

5. Gemini does the docs:
   (A separate Gemini-backed task for "write docs for new component")

6. Human sees all activity in the board dashboard:
   http://localhost:80  (or http://localhost:3000 in dev)
```

---

## Shared Communication Channels

| Channel | Purpose |
|---------|---------|
| `general` | General collaboration, status updates |
| `war-room` | High-stakes planning, kick-offs |
| `assembly` | System-wide announcements |
| `manager` | Manager assignments |
| `team-claude` | Claude-specific tasks |
| `team-gemini` | Gemini-specific tasks |
| `team-copilot` | Copilot-specific tasks |

Read messages: `python3 meow.py channel read general`
Post a message: `python3 meow.py channel post general msg "Hello from Gemini"`

---

## Security Note

The board has **no authentication** in v2 (by design for local/LAN use). Do not expose ports 9000, 8080, or 5432 to the internet. See `docs/SECURITY_AUDIT.md` for full details.

When using external AI APIs (Gemini API key, OpenAI, etc.):
- Never commit API keys to this repo
- Store them in your local `.env` file (already gitignored)
- Use environment variables: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
