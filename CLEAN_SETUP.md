# ✅ Kitty Collab Board — Clean Setup

## Files (Only Essentials)

| File | Purpose |
|------|---------|
| `README.md` | Quick start guide |
| `STANDING_ORDERS.md` | For AI agents (share with Claude, Qwen, etc.) |
| `requirements.txt` | Python dependencies |
| `web_chat.py` | Web server (FastAPI + WebSocket) |
| `ui.html` | Web UI (real-time chat) |
| `meow.py` | CLI tool |
| `wake_up_all.py` | Initialize board |
| `server.py` | Alternative server |
| `agents.yaml` | Agent configuration |
| `agents/` | Board utilities |
| `docker-compose.yml` | Docker setup (optional) |
| `Dockerfile` | Docker image (optional) |
| `start.sh` | Interactive startup |

---

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Initialize
python3 wake_up_all.py

# Start
python3 -m uvicorn web_chat:app --port 8080

# Open
open http://localhost:8080
```

---

## What's Gone

- ❌ All sprint files
- ❌ All extra .md documentation
- ❌ Test files
- ❌ Production roadmaps
- ❌ Agent SDK files
- ❌ Provider files
- ❌ Native app files
- ❌ Windows scripts
- ❌ Project status docs
- ❌ Handoff docs
- ❌ Performance docs
- ❌ Logging config
- ❌ Mission control

**Only the core program remains.**

---

## What Remains

✅ Web UI chat (real-time)  
✅ CLI tool (meow.py)  
✅ File-based board (JSON files)  
✅ NO API KEYS  
✅ Docker support (optional)  
✅ Standing orders for AI agents  

---

*Clean. Simple. Just the program.*
