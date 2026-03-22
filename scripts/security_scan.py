#!/usr/bin/env python3
"""
security_scan.py — Detect obfuscated exec() backdoor patterns in Python source files.

Exits with code 1 and prints offending lines if any dangerous patterns are found.
Designed to run as a CI step before tests.
"""

from __future__ import annotations

import sys
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns that must never appear in a source file.
# Each entry is (description, regex).  We match against the full text of a
# file so multi-line patterns (e.g. variable defined on one line,
# exec() on another) are still caught.
# ---------------------------------------------------------------------------
EXEC_PATTERNS: list[tuple[str, str]] = [
    (
        "exec(compile(…)) — dynamic code compilation and execution",
        r"exec\s*\(\s*compile\s*\(",
    ),
    (
        "exec() of base64-decoded data",
        r"exec\s*\([^)]*b64decode",
    ),
    (
        "exec() of zlib-decompressed data",
        r"exec\s*\([^)]*decompress",
    ),
    (
        "__import__('base64') outside of a comment or string",
        r"__import__\s*\(\s*['\"]base64['\"]\s*\)",
    ),
    (
        "__import__('zlib') outside of a comment or string",
        r"__import__\s*\(\s*['\"]zlib['\"]\s*\)",
    ),
]

# If ALL of these patterns are present anywhere in the file, flag it.
COMPOUND_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "XOR-obfuscation lambda combined with exec() — likely backdoor",
        [
            r"lambda\s+\w+\s*,\s*\w+\s*:\s*bytes\s*\(\s*\[.*\^",  # XOR lambda
            r"\bexec\s*\(",  # exec call
            r"\bb64decode\b",  # base64
        ],
    ),
    (
        "base64 + zlib + exec() triad",
        [
            r"\bb64decode\b",
            r"\bdecompress\b",
            r"\bexec\s*\(",
        ],
    ),
]

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = [ROOT]
EXCLUDE_DIRS = {".git", "frontend", "__pycache__", ".venv", "node_modules"}
EXCLUDE_FILES = {Path(__file__).resolve()}  # don't flag ourselves


def iter_python_files() -> list[Path]:
    results: list[Path] = []
    for scan_dir in SCAN_DIRS:
        for path in scan_dir.rglob("*.py"):
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            if path.resolve() in EXCLUDE_FILES:
                continue
            results.append(path)
    return sorted(results)


def scan_file(path: Path) -> list[str]:
    """Return a list of human-readable violation messages for *path*."""
    violations: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        # Files that cannot be decoded as UTF-8 are themselves suspicious
        # (could be binary payloads masquerading as Python); flag them.
        violations.append(
            "  ✗ File is not valid UTF-8 — binary or encoded content detected"
        )
        return violations
    except OSError as exc:
        return [f"  [read error] {exc}"]

    # Individual pattern checks (search whole text)
    for description, pattern in EXEC_PATTERNS:
        if re.search(pattern, text):
            violations.append(f"  ✗ {description}")

    # Compound pattern checks (all sub-patterns must match)
    for description, sub_patterns in COMPOUND_PATTERNS:
        if all(re.search(p, text, re.DOTALL) for p in sub_patterns):
            violations.append(f"  ✗ {description}")

    return violations


def main() -> int:
    files = iter_python_files()
    found_any = False

    for path in files:
        violations = scan_file(path)
        if violations:
            found_any = True
            rel = path.relative_to(ROOT)
            print(f"\n🚨 {rel}")
            for v in violations:
                print(v)

    if found_any:
        print(
            "\n❌ Security scan FAILED — obfuscated exec() backdoor pattern detected."
            "\n   Review the flagged files and remove any suspicious code before committing."
        )
        return 1

    print("✅ Security scan passed — no obfuscated exec() backdoor patterns found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
