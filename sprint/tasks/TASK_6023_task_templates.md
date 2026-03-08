# TASK 6023 — Task Templates

**Sprint:** 6 | **Phase:** 10 (Advanced Features) | **Assigned:** Claude
**Status:** done
**Completed:** 2026-03-07

## Summary

Added task template system to `meow.py`. Templates are saved to `board/templates.json` and support `{placeholder}` substitution in prompt strings.

## Implementation

### Storage

Templates stored in `board/templates.json`:
```json
{
  "bug-fix": {
    "description": "Fix a bug in the codebase",
    "role": "code",
    "priority": "high",
    "skills": ["python"],
    "prompt_template": "Fix the bug in {file}: {description}"
  }
}
```

### CLI Commands (via `meow template`)

```
meow template list              # list all templates
meow template save <name>       # interactive save (prompts for fields)
meow template use <name>        # create task from template (prompts for placeholders)
meow template delete <name>     # delete a template
```

### Placeholder Substitution

Uses `re.findall(r"\{(\w+)\}", prompt_template)` to extract placeholder names, prompts user for each, then calls `prompt_template.format(**values)`.

### Key Functions in `meow.py`

- `_load_templates() -> dict` — reads `board/templates.json`
- `_save_templates(templates: dict)` — writes `board/templates.json`
- `cmd_template(args: list)` — dispatches to `list/save/use/delete` subcommands
- `main()` routes `meow template` to `cmd_template(args[1:])`

## Files Modified

- `meow.py` — added `TEMPLATES_FILE`, `_load_templates`, `_save_templates`, `cmd_template`, updated `HELP` string and `main()`

## Notes

- Templates file is in `board/` so it's preserved across restarts and accessible to all operators
- `meow template use` calls `add_task()` from `mission_control` — same path as interactive add
