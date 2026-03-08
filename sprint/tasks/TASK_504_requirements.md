# TASK 504 — Update requirements.txt

**Assigned:** Claude
**Status:** ✅ done
**Phase:** 5 — Reliability & Hardening

## Description

Update `requirements.txt` to add new dependencies and fix the stale `google-generativeai` reference.

## Changes

```txt
# Remove or keep with note:
rich>=13.0.0          # currently unused — keep for future Mission Control use

# Add:
pyyaml>=6.0           # Phase 2: agents.yaml config loading
filelock>=3.12.0      # Phase 5: cross-platform board locking
google-genai>=1.0.0   # Phase 1: Gemini provider (NOT google-generativeai which is deprecated)
```

## Note

`IMPROVEMENT_PLAN.md` listed `google-generativeai>=0.4.0` — that package is deprecated and
replaced by `google-genai`. This task corrects that.

## Acceptance Criteria

- [ ] `pyyaml`, `filelock`, `google-genai` added
- [ ] Old `google-generativeai` NOT added (it's the wrong package)
- [ ] Comment explaining what each dep is for
- [ ] `rich` kept with a comment noting it's reserved for future TUI work

## Implementation Notes

Updated `requirements.txt`:
- Kept existing deps: `anthropic`, `openai`, `python-dotenv`
- Kept `rich>=13.0.0` with comment noting it's reserved for future Mission Control TUI
- Added `google-genai>=1.0.0` for Gemini provider (NOT the deprecated `google-generativeai`)
- Added `pyyaml>=6.0` for Phase 2 config-driven agent teams
- Added `filelock>=3.12.0` for Phase 5 cross-platform board locking
- Added section comments grouping deps by phase

## Review

**Claude self-review — APPROVED**

Clean, well-commented, correct package names. `google-genai` (not `google-generativeai`) confirmed. Phase-grouped comments make it easy to trace why each dep exists.

No issues.
