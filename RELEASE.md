# RELEASE v1.0.0 — Deployment Guide

Kitty Collab Board (Clowder) is now production-ready! This guide covers three deployment options.

---

## 🐳 Docker (Recommended for Production)

### Prerequisites
- Docker Desktop installed and running
- API keys in `.env` file

### Deploy Locally

```bash
# 1. Clone the repository
git clone https://github.com/theworstever1992/kitty-collab-board.git
cd kitty-collab-board

# 2. Create and fill .env
cp .env.example .env
# Edit .env with your API keys:
#   ANTHROPIC_API_KEY=sk-ant-...
#   DASHSCOPE_API_KEY=...

# 3. Start services
docker-compose up -d

# 4. Monitor from host
python mission_control.py
```

Services start on:
- **API Backend:** `http://localhost:8000`
- **Web UI:** `http://localhost:3000`
- **Board/Logs:** Mounted from your local `board/` and `logs/` directories

### Pulling from GHCR

```bash
# Use pre-built images from GitHub Container Registry
docker pull ghcr.io/theworstever1992/clowder-api:1.0.0
docker pull ghcr.io/theworstever1992/clowder-claude:1.0.0
docker pull ghcr.io/theworstever1992/clowder-qwen:1.0.0

# Update docker-compose.yml to reference these images, then:
docker-compose up -d
```

### Kubernetes (Advanced)

Kubernetes manifests available in `docs/k8s/` for cluster deployments. See `docs/DEPLOYMENT.md` for full details.

---

## 💻 Local Installation (Development)

### Prerequisites
- Python 3.11 or 3.12
- pip or uv
- API keys

### Install & Run

```bash
# 1. Clone repository
git clone https://github.com/theworstever1992/kitty-collab-board.git
cd kitty-collab-board

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 4. Initialize board
python wake_up.py

# 5. Start agents
python agents/claude_agent.py &
python agents/qwen_agent.py &

# 6. Open Mission Control (Terminal UI)
python mission_control.py
```

**Or with web UI:**

```bash
# Terminal 1: Backend API
cd web/backend
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend (requires Node.js)
cd web/frontend
npm install
npm run dev  # Opens on http://localhost:3000

# Terminal 3: Agents
python agents/claude_agent.py &
python agents/qwen_agent.py &

# Terminal 4: Monitor
python mission_control.py
```

---

## 🖥️ Native Desktop App (macOS / Windows / Linux)

### Download

Visit [GitHub Releases](https://github.com/theworstever1992/kitty-collab-board/releases) and download:
- **macOS:** `clowder-v1.0.0.dmg` (Intel + Apple Silicon)
- **Windows:** `clowder-v1.0.0.msi` or `.exe` (x64 + ARM64)
- **Linux:** `clowder-v1.0.0.AppImage` or `.deb`

### Install

**macOS:**
```bash
# Mount the DMG and drag app to Applications folder
open clowder-v1.0.0.dmg
```

**Windows:**
```powershell
# Run the installer
clowder-v1.0.0.msi
```

**Linux:**
```bash
# AppImage (make executable and run)
chmod +x clowder-v1.0.0.AppImage
./clowder-v1.0.0.AppImage

# Or install .deb (Ubuntu/Debian)
sudo dpkg -i clowder-v1.0.0.deb
```

### Launch

The app appears in your system tray with:
- Quick access menu
- Real-time task board
- Agent health status
- Native desktop notifications
- Automatic sync when offline

**API Configuration:**
On first launch, configure your API backend:
- Local: `http://localhost:8000`
- Docker: `http://localhost:8000` (from host)
- Remote: `https://your-server.com`

---

## 🔐 Environment Variables

Create `.env` file in project root:

```env
# Required: AI Provider Keys
ANTHROPIC_API_KEY=sk-ant-xxxx
DASHSCOPE_API_KEY=xxxx

# Optional: Board & Logging
CLOWDER_BOARD_DIR=./board
CLOWDER_LOG_DIR=./logs
CLOWDER_ARCHIVE_AFTER_DAYS=30

# Optional: API Server
CLOWDER_API_HOST=0.0.0.0
CLOWDER_API_PORT=8000
CLOWDER_WEB_ORIGINS=http://localhost:3000,http://localhost:8000

# Optional: Agent Config
CLOWDER_POLL_INTERVAL=5.0
CLOWDER_HEARTBEAT_INTERVAL=30.0

# Optional: Health Monitoring
CLOWDER_AGENT_WARNING_SECONDS=60
CLOWDER_AGENT_OFFLINE_SECONDS=300
CLOWDER_DISCORD_WEBHOOK_URL=
CLOWDER_SLACK_WEBHOOK_URL=
```

See `.env.example` for all available options.

---

## 📚 Documentation

- **[User Guide](docs/USER_GUIDE.md)** — Operating the board and managing tasks
- **[API Reference](docs/API_REFERENCE.md)** — REST endpoints and WebSocket API
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** — Building agents and custom features
- **[Architecture](docs/ARCHITECTURE.md)** — System design and data flow
- **[Performance](docs/PERFORMANCE.md)** — Optimization and tuning
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** — Common issues and fixes
- **[Deployment](docs/DEPLOYMENT.md)** — Production deployment strategies

---

## 🚀 Post-Deploy Checklist

After deployment, verify:

- [ ] Board initialized at `board/board.json`
- [ ] Agents registered in `board/agents.json`
- [ ] Tasks can be added via `meow add` or web UI
- [ ] Agents claim and complete tasks
- [ ] WebSocket connection works (web UI updates real-time)
- [ ] Logs visible in `logs/` directory or web UI
- [ ] Health monitoring shows agents online
- [ ] Analytics dashboard displays metrics

### Health Check

```bash
# Check board status
python meow.py

# Check API health
curl http://localhost:8000/api/health

# Check agent logs
tail -f logs/claude_agent.log
```

---

## 🔄 Updating

### Docker
```bash
docker pull ghcr.io/theworstever1992/clowder-api:latest
docker-compose up -d --pull always
```

### Local
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Native App
Visit [Releases](https://github.com/theworstever1992/kitty-collab-board/releases) for latest version.

---

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/theworstever1992/kitty-collab-board/issues)
- **Discussions:** [GitHub Discussions](https://github.com/theworstever1992/kitty-collab-board/discussions)
- **Docs:** See `docs/` folder for comprehensive guides

---

## 📊 Performance Targets

- Agent startup time: < 2 seconds
- Task claiming latency: < 100ms
- Memory per agent: < 200MB
- Board file size: < 10MB (with archival)
- WebSocket message latency: < 500ms

See `docs/PERFORMANCE.md` for detailed benchmarks and tuning guide.

---

**Ready to launch! 🚀**

For detailed information, see [STANDING_ORDERS.md](STANDING_ORDERS.md) for agent protocol and [docs/](docs/) for comprehensive documentation.
