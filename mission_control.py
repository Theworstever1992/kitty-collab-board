#!/usr/bin/env python3
"""
mission_control.py — Clowder v2 TUI
Rich-based terminal UI with real-time board view.
Connects to the v2 API on port 9000.
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

import httpx

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

API_BASE = os.environ.get("CLOWDER_API_URL", "http://localhost:9000")
REFRESH_INTERVAL = 5  # seconds


# ── Fetchers ───────────────────────────────────────────────────────────────────

async def fetch(path: str) -> Any:
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{API_BASE}{path}")
            return r.json() if r.is_success else []
    except Exception:
        return []


async def fetch_all():
    agents, tasks, ideas, violations = await asyncio.gather(
        fetch("/api/v2/agents"),
        fetch("/api/tasks"),
        fetch("/api/v2/ideas"),
        fetch("/api/v2/governance/violations"),
    )
    return agents, tasks, ideas, violations


# ── Rich renderers ─────────────────────────────────────────────────────────────

def agents_table(agents: list[dict]) -> Table:
    t = Table(title="🐾 Agents", box=box.SIMPLE, expand=True)
    t.add_column("Name", style="bold yellow")
    t.add_column("Role", style="dim")
    t.add_column("Status")
    t.add_column("Model", style="dim")
    for a in agents[:20]:
        status_color = {"online": "green", "idle": "yellow", "offline": "red"}.get(a.get("status", "offline"), "dim")
        t.add_row(
            a.get("name", "?"),
            a.get("role", "?"),
            Text(a.get("status", "offline"), style=status_color),
            a.get("model", "?"),
        )
    return t


def tasks_table(tasks: list[dict]) -> Table:
    t = Table(title="📋 Tasks", box=box.SIMPLE, expand=True)
    t.add_column("ID", style="dim", width=10)
    t.add_column("Title")
    t.add_column("Status")
    t.add_column("Assigned To", style="dim")
    status_colors = {"pending": "dim", "in_progress": "yellow", "done": "green", "blocked": "red"}
    for task in tasks[:15]:
        status = task.get("status", "pending")
        t.add_row(
            task.get("id", "?")[:8],
            task.get("title", "?")[:50],
            Text(status, style=status_colors.get(status, "dim")),
            task.get("assigned_to") or "—",
        )
    return t


def ideas_table(ideas: list[dict]) -> Table:
    t = Table(title="💡 Ideas", box=box.SIMPLE, expand=True)
    t.add_column("Title")
    t.add_column("Author", style="dim")
    t.add_column("🐾", justify="right")
    t.add_column("Status")
    status_colors = {"pending": "yellow", "approved": "green", "rejected": "red"}
    sorted_ideas = sorted(ideas, key=lambda i: i.get("reaction_count", 0), reverse=True)
    for idea in sorted_ideas[:10]:
        status = idea.get("status", "pending")
        t.add_row(
            idea.get("title", "?")[:45],
            idea.get("author") or idea.get("author_id", "?"),
            str(idea.get("reaction_count", 0)),
            Text(status, style=status_colors.get(status, "dim")),
        )
    return t


def violations_table(violations: list[dict]) -> Table:
    t = Table(title="⚠️ Violations", box=box.SIMPLE, expand=True)
    t.add_column("Agent", style="dim")
    t.add_column("Type")
    t.add_column("Severity")
    sev_colors = {"low": "dim", "medium": "yellow", "high": "red"}
    for v in violations[:10]:
        sev = v.get("severity", "low")
        t.add_row(
            v.get("agent_id", "?"),
            v.get("violation_type", "?"),
            Text(sev, style=sev_colors.get(sev, "dim")),
        )
    return t


def build_layout(agents, tasks, ideas, violations) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=2),
    )
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )
    layout["left"].split_column(
        Layout(name="agents"),
        Layout(name="tasks"),
    )
    layout["right"].split_column(
        Layout(name="ideas"),
        Layout(name="violations"),
    )

    layout["header"].update(Panel(
        Text("🐱 Clowder v2 Mission Control", justify="center", style="bold yellow"),
        style="yellow",
    ))
    layout["agents"].update(Panel(agents_table(agents), border_style="dim"))
    layout["tasks"].update(Panel(tasks_table(tasks), border_style="dim"))
    layout["ideas"].update(Panel(ideas_table(ideas), border_style="dim"))
    layout["violations"].update(Panel(violations_table(violations), border_style="dim"))
    layout["footer"].update(Panel(
        Text(f"API: {API_BASE}  |  Refresh every {REFRESH_INTERVAL}s  |  Ctrl+C to quit", style="dim", justify="center"),
        border_style="dim",
    ))
    return layout


# ── Entry point ────────────────────────────────────────────────────────────────

async def run_tui():
    if not HAS_RICH:
        print("Install rich: pip install rich")
        sys.exit(1)

    console = Console()
    with Live(console=console, refresh_per_second=0.5, screen=True) as live:
        while True:
            agents, tasks, ideas, violations = await fetch_all()
            live.update(build_layout(agents, tasks, ideas, violations))
            await asyncio.sleep(REFRESH_INTERVAL)


def main():
    try:
        asyncio.run(run_tui())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
