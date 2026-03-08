# TASK 6021 — Skills-Based Task Routing

**Sprint:** 6 | **Phase:** 10 (Advanced Features) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Summary

Extended the task routing system so tasks can declare required skills (`skills: list[str]`) and agents only claim tasks where they have ALL required skills. Propagated through BaseAgent, FastAPI, and mission_control.

## Implementation

### `agents/base_agent.py`

- `__init__` now accepts `skills: list[str] = None`; stored as `self.skills`
- `register()` writes `"skills": self.skills` to `agents.json`
- `get_tasks()` extended with skills filtering:

```python
task_skills = [s.lower() for s in (t.get("skills") or [])]
if task_skills and self.skills:
    skills_ok = all(s in self.skills for s in task_skills)
elif task_skills and not self.skills:
    skills_ok = False  # task needs skills, agent has none
else:
    skills_ok = True   # no skill requirement
if role_ok and skills_ok:
    filtered.append(t)
```

- Tasks without `skills` field are claimable by any agent (backwards compatible)

### `web/backend/main.py`

- `TaskCreate` model: added `skills: list[str] = []`
- `TaskUpdate` model: added `skills: Optional[list[str]] = None`
- `POST /api/tasks`: stores skills lowercased in task JSON
- `PUT /api/tasks/{id}`: updates skills when provided

### `mission_control.py`

- `add_task()` now accepts `skills: list = None`; stored in task JSON
- Interactive TUI prompts for skills when adding a task

### `meow.py`

- `quick_task()` accepts `skills: list = None`
- `meow task <text> --skills python,react` parses comma-separated skills

## Backwards Compatibility

Tasks without `skills` field are treated as no requirement — all agents can claim them. Agents without declared skills can still claim unskilled tasks.

## Files Modified

- `agents/base_agent.py`
- `web/backend/main.py`
- `mission_control.py`
- `meow.py`
