#!/bin/bash
# start.sh — Kitty Collab Board

set -e

echo "🐱 Kitty Collab Board"
echo "===================="
echo ""
echo "Choose mode:"
echo "  1) Docker (recommended)"
echo "  2) Native Python"
echo ""
read -p "Select [1-2]: " choice

if [ "$choice" = "1" ]; then
    # Docker mode
    echo ""
    echo "🐳 Docker Mode"
    echo "=============="
    echo ""
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose not found. Install Docker first."
        exit 1
    fi
    
    # Use docker compose or docker-compose
    COMPOSE_CMD="docker compose"
    if ! command -v docker &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    fi
    
    # Initialize if needed
    if [ ! -d "board/channels" ]; then
        echo "📁 Initializing board..."
        $COMPOSE_CMD --profile init up init
        echo ""
    fi
    
    # Start services
    echo "🚀 Starting services..."
    $COMPOSE_CMD up -d
    
    echo ""
    echo "✅ Services started!"
    echo ""
    echo "📊 Access Points:"
    echo "   Web UI: http://localhost:8080"
    echo ""
    echo "📝 Useful Commands:"
    echo "   View logs:     $COMPOSE_CMD logs -f"
    echo "   Stop:          $COMPOSE_CMD down"
    echo "   CLI access:    $COMPOSE_CMD --profile cli run cli"
    echo ""
    
else
    # Native Python mode
    echo ""
    echo "🐍 Native Python Mode"
    echo "====================="
    echo ""
    
    # Initialize if needed
    if [ ! -d "board/channels" ]; then
        echo "📁 Initializing board..."
        python3 wake_up_all.py
        echo ""
    fi
    
    # Check dependencies
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo "⚠️  Installing dependencies..."
        pip install -r requirements.txt
        echo ""
    fi
    
    # Start server
    echo "🚀 Starting Web Chat Server..."
    echo ""
    echo "📊 Access: http://localhost:8080"
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""
    
    python3 -m uvicorn web_chat:app --host 0.0.0.0 --port 8080 --reload
fi
