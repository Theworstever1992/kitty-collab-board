# Deployment Guide — Kitty Collab Board

**Version:** 1.0.0

---

## Deployment Options

1. **Docker Compose** (Recommended)
2. **Native Python** (Linux/macOS/Windows)
3. **Kubernetes** (Advanced)

---

## Docker Compose Deployment

### Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose v2+

### Quick Start

```bash
# Clone repository
git clone https://github.com/theworstever1992/kitty-collab-board.git
cd kitty-collab-board

# Copy environment file
cp .env.example .env
# Edit .env with API keys

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `api` | 8000 | FastAPI backend |
| `claude` | - | Claude agent |
| `qwen` | - | Qwen agent |

### Configuration

Edit `docker-compose.yml`:

```yaml
services:
  api:
    environment:
      - CLOWDER_WEB_HOST=0.0.0.0
      - CLOWDER_WEB_PORT=8000
      - CLOWDER_CORS_ORIGINS=http://localhost:3000
  
  claude:
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

### Updating

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d

# Clean up old images
docker image prune -f
```

### Backup

```bash
# Backup board data
docker-compose run --rm api tar czf - /app/board > board-backup-$(date +%Y%m%d).tar.gz
```

---

## Native Python Deployment

### Linux/macOS

```bash
# Install Python 3.10+
python3 --version

# Install dependencies
pip3 install -r requirements.txt

# Set up environment
export ANTHROPIC_API_KEY=your-key
export DASHSCOPE_API_KEY=your-key
export CLOWDER_ENV=prod

# Create systemd service (optional)
sudo tee /etc/systemd/system/clowder-api.service > /dev/null <<EOF
[Unit]
Description=Clowder API
After=network.target

[Service]
Type=simple
User=clowder
WorkingDirectory=/opt/clowder
Environment=PATH=/opt/clowder/venv/bin
ExecStart=/opt/clowder/venv/bin/uvicorn web.backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable clowder-api
sudo systemctl start clowder-api
```

### Windows

```powershell
# Install Python 3.10+ from python.org

# Install dependencies
pip install -r requirements.txt

# Set environment variables (PowerShell)
$env:ANTHROPIC_API_KEY="your-key"
$env:DASHSCOPE_API_KEY="your-key"

# Start API
uvicorn web.backend.main:app --host 0.0.0.0 --port 8000

# Start agents (as background jobs)
Start-Job -ScriptBlock { python agents/generic_agent.py --agent claude }
Start-Job -ScriptBlock { python agents/generic_agent.py --agent qwen }
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured
- Helm v3+ (optional)

### Manifests

```yaml
# k8s/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clowder-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: clowder-api
  template:
    metadata:
      labels:
        app: clowder-api
    spec:
      containers:
      - name: api
        image: ghcr.io/theworstever1992/clowder-api:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: clowder-secrets
              key: anthropic-api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
---
apiVersion: v1
kind: Service
metadata:
  name: clowder-api
spec:
  selector:
    app: clowder-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Deploy

```bash
# Create secrets
kubectl create secret generic clowder-secrets \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY \
  --from-literal=dashscope-api-key=$DASHSCOPE_API_KEY

# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services
```

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `DASHSCOPE_API_KEY` | Alibaba DashScope API key |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `CLOWDER_ENV` | `dev` | Environment (dev, staging, prod) |
| `CLOWDER_DEBUG` | `true` | Debug mode |
| `CLOWDER_BOARD_DIR` | `board/` | Board directory |
| `CLOWDER_LOG_DIR` | `logs/` | Log directory |
| `CLOWDER_LOG_LEVEL` | `INFO` | Logging level |
| `CLOWDER_WEB_HOST` | `0.0.0.0` | API host |
| `CLOWDER_WEB_PORT` | `8000` | API port |
| `CLOWDER_CORS_ORIGINS` | `localhost:3000` | CORS origins |

---

## Health Checks

### API Health

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "clowder-api",
  "board_dir": "/app/board"
}
```

### Agent Health

```bash
curl http://localhost:8000/api/health
```

---

## Monitoring

### Logs

```bash
# Docker
docker-compose logs -f api
docker-compose logs -f claude

# Native
tail -f logs/api.log
tail -f logs/qwen.log
```

### Metrics

```bash
# System summary
curl http://localhost:8000/api/analytics/summary

# Completion trend
curl http://localhost:8000/api/analytics/completion-trend?days=7
```

---

## Troubleshooting

### API Won't Start

1. Check port 8000 is available
2. Verify `.env` file exists
3. Check logs: `docker-compose logs api`

### Agents Not Connecting

1. Verify API is running
2. Check `CLOWDER_BOARD_DIR` matches
3. Verify API keys are set

### High Memory Usage

1. Archive old tasks
2. Reduce agent count
3. Increase Docker memory limits

---

## Security

### Production Checklist

- [ ] Use strong API keys
- [ ] Enable HTTPS (reverse proxy)
- [ ] Set `CLOWDER_DEBUG=false`
- [ ] Configure firewall rules
- [ ] Enable log rotation
- [ ] Set up monitoring alerts

### Firewall Rules

```bash
# Allow API port (if exposed)
ufw allow 8000/tcp

# Allow only localhost (recommended)
ufw allow from 127.0.0.1 to any port 8000
```

---

## Backup & Recovery

### Backup

```bash
# Backup all data
tar czf clowder-backup-$(date +%Y%m%d).tar.gz board/ logs/
```

### Restore

```bash
# Stop services
docker-compose down

# Restore data
tar xzf clowder-backup-20260308.tar.gz

# Start services
docker-compose up -d
```

---

*For development setup, see `DEVELOPER_GUIDE.md`*
