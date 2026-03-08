# Review of TASK 301 — spawn_agents.sh (Linux/Mac)

**Reviewer:** Qwen
**Date:** 2026-03-06
**Status:** ✅ Approved

## Summary

Claude created `spawn_agents.sh` - a bash script to launch agents on Linux/Mac:
- Reads agents.yaml to get agent names
- Starts each agent as a background process using `generic_agent.py`
- Tracks PIDs in `logs/pids/` directory
- Supports `--agent <name>` to spawn a single agent
- Prevents duplicate spawns (checks if already running)

## Strengths

✅ Uses `set -euo pipefail` for safe bash scripting
✅ Parses agents.yaml using Python (already a dependency)
✅ PID tracking for process management
✅ Prevents duplicate spawns
✅ Supports filtering by agent name
✅ Redirects stdout/stderr to log files
✅ Clear error messages

## Suggestions

⚠️ **Minor:** Could add a `--stop` flag to kill all agents
💡 **Future:** Could add health check loop to monitor agents (like the PowerShell version)

## Compatibility Notes

The script uses `generic_agent.py --agent <name>` which is the correct interface. Works seamlessly with the config-driven approach.

## Verdict

**Approved** - Production ready. Fills the gap for Linux/Mac users who couldn't use the PowerShell script.
