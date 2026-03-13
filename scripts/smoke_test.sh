#!/bin/bash
# smoke_test.sh — Hit major endpoints and assert 200s

API_BASE=${CLOWDER_API_URL:-"http://localhost:9000"}
echo "🚀 Starting smoke test against $API_BASE..."

# Helper to check endpoint
check_endpoint() {
    local method=$1
    local path=$2
    local expected_status=${3:-200}
    local data=$4
    
    echo -n "Checking $method $path... "
    
    if [ "$method" == "POST" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE$path" \
            -H "Content-Type: application/json" \
            -d "$data")
    elif [ "$method" == "PATCH" ]; then
        status=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$API_BASE$path" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        status=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE$path")
    fi
    
    if [ "$status" -eq "$expected_status" ]; then
        echo "✅ $status"
    else
        echo "❌ $status (Expected $expected_status)"
        exit 1
    fi
}

# 1. Health
check_endpoint "GET" "/api/health"

# 2. Tasks
check_endpoint "GET" "/api/tasks"

# 3. Agents
check_endpoint "POST" "/api/agents/register" 200 '{"name": "smoke-agent", "role": "tester"}'
check_endpoint "GET" "/api/agents/smoke-agent/profile"

# 4. v2 Teams
check_endpoint "GET" "/api/v2/teams"
check_endpoint "POST" "/api/v2/teams" 200 '{"name": "Smoke Team"}'

# 5. v2 Chat
check_endpoint "GET" "/api/v2/chat/general"
check_endpoint "POST" "/api/v2/chat/general" 200 '{"sender": "smoke-agent", "content": "Smoke test message"}'

# 6. Governance
check_endpoint "GET" "/api/v2/governance/token-report"
check_endpoint "GET" "/api/v2/violations/" # Redirect or trailing slash? main.py has prefix /api/v2/violations
check_endpoint "POST" "/api/v2/violations/" 201 '{"violation_type": "smoke_test", "agent_id": "smoke-agent", "notes": "ignore me"}'

# 7. Ideas
check_endpoint "GET" "/api/v2/ideas"
check_endpoint "POST" "/api/v2/ideas" 200 '{"title": "Smoke Idea", "submitted_by": "smoke-agent"}'

echo "🎊 All smoke tests passed!"
