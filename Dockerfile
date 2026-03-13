# Kitty Collab Board — Dockerfile
# Serves both v1 (web_chat.py, port 8080) and v2 (backend/main.py, port 9000)

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-bake sentence-transformers model weights so containers start instantly
# (avoids 400MB+ download at runtime — Decision 7 from v2 design doc)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application
COPY . .

# Make alias scripts executable
RUN chmod +x wake serve manager handoff status post read create-profile 2>/dev/null || true

# Create board directory
RUN mkdir -p /app/board/channels /app/board/agents /app/board/archives

# Expose v1 and v2 ports
EXPOSE 8080 9000

# Health check (v1 default)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/channels')" || exit 1

# Default: v1 Web Chat Server
CMD ["python", "-m", "uvicorn", "web_chat:app", "--host", "0.0.0.0", "--port", "8080"]
