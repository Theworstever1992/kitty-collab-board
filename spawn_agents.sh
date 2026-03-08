#!/usr/bin/env bash
# spawn_agents.sh — Launch all Clowder agents on Linux/Mac
# Reads agents.yaml and starts each agent as a background process.
# Usage: ./spawn_agents.sh [--agent <name>]

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT/logs/pids"
AGENTS_YAML="$ROOT/agents.yaml"

mkdir -p "$PID_DIR"

if [ ! -f "$AGENTS_YAML" ]; then
    echo "Error: agents.yaml not found at $ROOT"
    echo "Create it first — see IMPROVEMENT_PLAN.md for the schema."
    exit 1
fi

# Parse agent names from agents.yaml using Python (already a dependency)
AGENT_NAMES=$(python3 -c "
import yaml, sys
with open('$AGENTS_YAML') as f:
    cfg = yaml.safe_load(f)
for a in cfg.get('agents', []):
    print(a['name'])
")

FILTER="${1:-}"
if [ "$FILTER" = "--agent" ] && [ -n "${2:-}" ]; then
    AGENT_NAMES="$2"
fi

for name in $AGENT_NAMES; do
    PID_FILE="$PID_DIR/$name.pid"
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "  [$name] already running (pid $(cat "$PID_FILE"))"
        continue
    fi
    python3 "$ROOT/agents/generic_agent.py" --agent "$name" \
        > "$ROOT/logs/${name}_stdout.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "  [$name] started (pid $!)"
done

echo ""
echo "All agents launched. Monitor with: python meow.py mc"
