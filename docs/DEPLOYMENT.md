# Kitty Collab Board — Deployment Guide

---

## Prerequisites

- Python 3.11 or 3.12
- `pip install -r requirements.txt`
- API keys: `ANTHROPIC_API_KEY`, `DASHSCOPE_API_KEY`

---

## Local (Single Machine)

### Setup

```bash
git clone <repo>
cd kitty-collab-board
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in API keys
python wake_up.py
```

`wake_up.py` creates `board/` and `logs/` directories. It only needs to run once.

### Running Agents

Start each agent in a separate terminal:

```bash
python agents/claude_agent.py
python agents/qwen_agent.py
```

Or use the spawn script (Linux/Mac):

```bash
python meow.py spawn            # all agents
python meow.py spawn --agent claude   # single agent
```

### Running the Web UI

```bash
# Terminal 1: API
uvicorn web.backend.main:app --reload --port 8000

# Terminal 2: Frontend
cd web/frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

---

## Docker

### Build and Start

```bash
docker-compose up -d
```

This starts:
- `api` — FastAPI backend on port 8000
- `claude-agent` — Anthropic agent (waits for API to be healthy)
- `qwen-agent` — Qwen agent (waits for API to be healthy)

### Environment

Create `.env` at project root:

```bash
ANTHROPIC_API_KEY=sk-ant-...
DASHSCOPE_API_KEY=sk-...
```

Docker Compose reads this automatically. All containers share these keys.

### Volumes

```yaml
volumes:
  - ./board:/app/board    # shared task board
  - ./logs:/app/logs      # shared agent logs
```

Board and logs are on the host — you can run `python meow.py` locally while agents run in containers.

### Health Checks

The API container runs a health check every 30 seconds:
```bash
python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
```

Agent containers wait for `service_healthy` before starting. If the board directory is missing, the API reports unhealthy and agents won't start.

### Useful Commands

```bash
docker-compose up -d              # start all services
docker-compose logs -f            # stream all logs
docker-compose logs -f api        # stream API logs only
docker-compose ps                 # service status
docker-compose restart claude-agent  # restart single service
docker-compose down               # stop all services
docker-compose down -v            # stop + remove volumes (clears board!)
```

### Rebuilding After Code Changes

```bash
docker-compose build
docker-compose up -d
```

---

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | yes (Claude) | — | Anthropic API key |
| `DASHSCOPE_API_KEY` | yes (Qwen) | — | DashScope API key |
| `CLOWDER_BOARD_DIR` | no | `./board` | Board directory path |
| `CLOWDER_LOG_DIR` | no | `./logs` | Log directory path |
| `CLOWDER_AGENT_WARNING_SECONDS` | no | `60` | Seconds before agent is "warning" |

---

## CI/CD (GitHub Actions)

Tests run automatically on push and pull requests to `main`. See `.github/workflows/test.yml`.

The workflow:
1. Checks out code
2. Sets up Python 3.11 and 3.12 (matrix)
3. Installs dependencies
4. Runs `wake_up.py` to initialize test board
5. Runs `pytest tests/ -v --tb=short`

Dummy API keys are used — no real API calls during tests.

To add a new test, create a file in `tests/` following pytest conventions.

---

## Pre-Production Checklist

- [ ] API keys are in `.env` (not committed to git)
- [ ] `board/` and `logs/` directories exist (run `python wake_up.py`)
- [ ] `filelock` is installed (`pip install filelock`) — prevents board corruption
- [ ] At least one agent is running and registered (`python meow.py` shows it online)
- [ ] API health check passes: `curl http://localhost:8000/health`
- [ ] Logs directory is writable by agent processes
- [ ] Board file is writable by all agents and the API

---

## File Locations

```
kitty-collab-board/
├── board/
│   ├── board.json        # task board (agents read/write)
│   ├── agents.json       # agent registry (agents write, operator reads)
│   ├── archive.json      # archived done tasks
│   ├── templates.json    # task templates
│   └── audit.log         # audit trail (if audit module enabled)
├── logs/
│   ├── claude.log        # Claude agent log
│   └── qwen.log          # Qwen agent log
├── web/
│   ├── backend/main.py   # FastAPI app
│   └── frontend/         # React + TypeScript frontend
├── agents/
│   ├── base_agent.py     # base class
│   ├── claude_agent.py   # Claude implementation
│   └── qwen_agent.py     # Qwen implementation
└── .github/
    └── workflows/
        ├── test.yml              # CI tests
        └── docker-publish.yml    # Docker image publish
```

---

## Updating

```bash
git pull
pip install -r requirements.txt   # pick up new dependencies
python wake_up.py                  # in case board structure changed
docker-compose build && docker-compose up -d  # if using Docker
```
