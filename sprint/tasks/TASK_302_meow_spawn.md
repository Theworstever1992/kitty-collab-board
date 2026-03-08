# TASK 302 — meow.py spawn (Linux + agents.yaml)

**Assigned:** Claude
**Status:** done
**Phase:** 3 — Cross-Platform Spawning

## Description

Update `meow.py` `run_spawn()` to work cross-platform and read from `agents.yaml`.
Currently calls PowerShell only — needs Linux/Mac path.

## Acceptance Criteria

- [x] On Linux/Mac: runs `spawn_agents.sh`
- [x] On Windows: runs existing `windows/spawn_agents.ps1`
- [x] `meow spawn --agent <name>` spawns a single agent by name
- [x] `meow spawn --list` prints agents from `agents.yaml` without spawning
- [x] If `agents.yaml` not found, prints helpful error

## Implementation Notes

Updated `run_spawn()` in `meow.py` to:
- Accept `extra_args` list passed from `main()`
- Check `--list` flag → calls new `list_agents()` helper (parses agents.yaml with yaml, prints table)
- Check `--agent <name>` flag → passes through to spawn script
- Branch on `os.name != 'nt'` for Linux/Mac (runs `bash spawn_agents.sh`) vs Windows (PowerShell)
- Checks for agents.yaml existence before attempting spawn; prints actionable error if missing
- Updated HELP string to document all new options
- `main()` now passes `args[1:]` as `extra_args` for the spawn command

## Review

_Qwen reviews here_
