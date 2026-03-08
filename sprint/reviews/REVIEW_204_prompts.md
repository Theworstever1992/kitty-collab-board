# Review of TASK 204 — prompts.py Role System Prompts

**Reviewer:** Qwen
**Date:** 2026-03-06
**Status:** ✅ Approved

## Summary

Claude created `agents/prompts.py` with default system prompts for all 5 roles:
- reasoning, code, research, summarization, general
- Each prompt explains the agent's role in Clowder
- Clear guidelines for each role
- `get_system_prompt()` function with fallback to "general"

## Strengths

✅ All 5 roles covered with appropriate prompts
✅ Each prompt mentions the Clowder multi-agent system context
✅ Clear guidelines specific to each role
✅ Emphasizes conciseness and structured output (for other agents to read)
✅ Fallback to "general" for unknown roles

## Comparison with My Implementation

Our implementations are nearly identical - we both:
- Used `ROLE_PROMPTS: dict[str, str]` structure
- Implemented `get_system_prompt(role)` with fallback
- Covered all 5 roles
- Emphasized collaboration and structured output

Claude's version has slightly more detailed guidelines per role.

## Verdict

**Approved** - Production ready. Well-structured prompts that will help agents understand their roles.
