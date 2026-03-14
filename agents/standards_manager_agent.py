"""
standards_manager_agent.py — Standards Manager Agent.
Scans completed tasks for code-quality violations, posts summaries to
#standards-violations channel and inserts rows into StandardsViolation.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

# Patterns that suggest a quality problem in task results
_VIOLATION_RULES: list[dict[str, Any]] = [
    {
        "rule": "no_type_hints",
        "severity": "medium",
        "pattern": re.compile(r"def \w+\([^)]*\)\s*:(?!\s*->)", re.MULTILINE),
        "description": "Function missing return type annotation",
    },
    {
        "rule": "bare_except",
        "severity": "high",
        "pattern": re.compile(r"\bexcept\s*:", re.MULTILINE),
        "description": "Bare except clause — catches all exceptions indiscriminately",
    },
    {
        "rule": "hardcoded_secret",
        "severity": "high",
        "pattern": re.compile(r'(?i)(password|secret|token|api_key)\s*=\s*["\'][^"\']{6,}["\']'),
        "description": "Possible hardcoded secret in task result",
    },
    {
        "rule": "no_docstring",
        "severity": "low",
        "pattern": re.compile(r'class \w+.*:\s*\n\s+(?!""")', re.MULTILINE),
        "description": "Class missing docstring",
    },
    {
        "rule": "todo_left_in_result",
        "severity": "low",
        "pattern": re.compile(r"\bTODO\b|\bFIXME\b|\bHACK\b"),
        "description": "TODO / FIXME marker left in completed task result",
    },
]


class StandardsManagerAgent:
    """
    Reads completed tasks from the API, scans their ``result`` field for
    known violation patterns, and posts each finding back via
    ``POST /api/v2/violations``.
    """

    def __init__(self, api_base: str, agent_name: str = "standards-manager") -> None:
        self.api_base = api_base.rstrip("/")
        self.agent_name = agent_name

    # ── Public interface ───────────────────────────────────────────────────────

    async def run_once(self) -> dict:
        """
        Fetch all completed tasks, scan for violations, post findings.
        Returns a summary dict with counts.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{self.api_base}/api/tasks?status=done")
            resp.raise_for_status()
            tasks: list[dict] = resp.json()

        total_violations = 0
        scanned = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            for task in tasks:
                result_text = task.get("result") or ""
                if not result_text:
                    continue
                scanned += 1
                found = self._scan(result_text)
                for violation in found:
                    await client.post(
                        f"{self.api_base}/api/v2/violations",
                        json={
                            "agent_name": task.get("assigned_to") or "unknown",
                            "task_id": task.get("id"),
                            "violation_type": violation["rule"],
                            "description": violation["description"],
                            "severity": violation["severity"],
                            "reported_by": self.agent_name,
                        },
                    )
                    total_violations += 1

        # Broadcast summary to #main-hall
        if total_violations:
            msg = (
                f"⚠️ **Standards scan complete** — {total_violations} violation(s) found "
                f"across {scanned} completed tasks. "
                f"Check `/violations` in the UI or `GET /api/v2/violations`."
            )
        else:
            msg = (
                f"✅ **Standards scan complete** — {scanned} tasks scanned, no violations. "
                f"Looking clean 🐾"
            )

        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{self.api_base}/api/v2/chat/main-hall",
                json={"sender": self.agent_name, "content": msg, "type": "update"},
            )

        return {
            "scanned": scanned,
            "violations_found": total_violations,
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _scan(self, text: str) -> list[dict]:
        """Return list of violation dicts found in *text*."""
        violations: list[dict] = []
        for rule in _VIOLATION_RULES:
            if rule["pattern"].search(text):
                violations.append(
                    {
                        "rule": rule["rule"],
                        "severity": rule["severity"],
                        "description": rule["description"],
                    }
                )
        return violations
