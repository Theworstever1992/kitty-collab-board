# TASK 301 — spawn_agents.sh (Linux/Mac)

**Assigned:** Claude
**Status:** done
**Phase:** 3 — Cross-Platform Spawning

## Description

Create `spawn_agents.sh` — the Linux/Mac equivalent of `windows/spawn_agents.ps1`.
Reads `agents.yaml`, launches each agent as a background process, writes PIDs to `logs/pids/`.

## Acceptance Criteria

- [x] Reads agent names from `agents.yaml` (can use python -c to parse YAML)
- [x] Launches each: `python agents/generic_agent.py --agent <name> &`
- [x] Stores PID per agent in `logs/pids/<name>.pid`
- [x] Prints status as agents start
- [x] `chmod +x` ready (shebang + executable)
- [x] Graceful if `agents.yaml` not found

## Implementation Notes

Created `/spawn_agents.sh` with:
- `set -euo pipefail` for safety
- Uses `python3 -c "import yaml..."` to parse agent names (no extra deps beyond pyyaml)
- Skips already-running agents (checks PID file + `kill -0`)
- Supports `--agent <name>` to spawn a single agent
- Redirects stdout/stderr to `logs/<name>_stdout.log`
- Requires `chmod +x spawn_agents.sh` before first use (run once manually or via setup)

## Review

_Qwen reviews here_
