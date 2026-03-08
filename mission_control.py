"""
mission_control.py — Kitty Collab Board
TUI dashboard for monitoring agents and tasks on the board.
Press 'q' to quit, 'r' to refresh, 'a' to add a task, 'h' to handoff.
"""

import json
import os
import sys
import time
import datetime
from pathlib import Path

# Health thresholds (seconds)
HEALTH_WARNING = int(os.environ.get("HEALTH_WARNING_SECONDS", "60"))
HEALTH_OFFLINE = int(os.environ.get("HEALTH_OFFLINE_SECONDS", "300"))

BOARD_DIR = Path(os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent / "board"))
LOG_DIR = Path(os.environ.get("CLOWDER_LOG_DIR", Path(__file__).parent / "logs"))

# Try to use curses for TUI; fall back to simple print mode
try:
    import curses

    HAS_CURSES = True
except ImportError:
    HAS_CURSES = False


def load_board():
    board_file = BOARD_DIR / "board.json"
    if not board_file.exists():
        return {"tasks": []}
    try:
        return json.loads(board_file.read_text(encoding="utf-8"))
    except Exception:
        return {"tasks": []}


def load_agents():
    agents_file = BOARD_DIR / "agents.json"
    if not agents_file.exists():
        return {}
    try:
        return json.loads(agents_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def agent_health_status(agent_info: dict) -> str:
    """Compute health status from last_seen timestamp."""
    last_seen = agent_info.get("last_seen")
    if not last_seen:
        return "unknown"
    try:
        last = datetime.datetime.fromisoformat(last_seen)
        age = (datetime.datetime.now() - last).total_seconds()
        if age < HEALTH_WARNING:
            return "online"
        if age < HEALTH_OFFLINE:
            return "warning"
        return "offline"
    except Exception:
        return "unknown"


def health_emoji(health: str) -> str:
    return {"online": "🟢", "warning": "🟡", "offline": "🔴", "unknown": "❓"}.get(health, "❓")


def print_health():
    """Print agent health summary."""
    agents = load_agents()
    print("\n🏥 AGENT HEALTH\n")
    if not agents:
        print("  (no agents registered)\n")
        return
    for name, info in agents.items():
        health = agent_health_status(info)
        last = info.get("last_seen", "?")[:19]
        print(f"  {health_emoji(health)} {name:12} | {health:8} | last seen: {last}")
    print()


def print_handoffs():
    """Print tasks with pending handoffs."""
    board = load_board()
    pending = [
        t for t in board.get("tasks", [])
        if t.get("handoff", {}).get("status") == "pending_acceptance"
    ]
    print("\n🔀 PENDING HANDOFFS\n")
    if not pending:
        print("  (none)\n")
        return
    for t in pending:
        h = t["handoff"]
        print(f"  {t['id']} | '{t.get('title', '?')}'")
        print(f"    from: {h.get('from')}  →  to: {h.get('to')}")
        print(f"    notes: {h.get('notes') or '(none)'}")
        print(f"    at: {h.get('at', '?')[:19]}")
        print()


def cli_handoff_task():
    """Interactively hand off a task to another agent."""
    board = load_board()
    in_progress = [t for t in board.get("tasks", []) if t.get("status") == "in_progress"]
    if not in_progress:
        print("  No in-progress tasks to hand off.")
        return

    print("\n🔀 Hand off a task\n")
    print("  In-progress tasks:")
    for t in in_progress:
        print(f"    {t['id']} — {t.get('title', '?')} (claimed by: {t.get('claimed_by', '?')})")

    task_id = input("\n  Task ID to hand off: ").strip()
    if not task_id:
        print("  (cancelled)")
        return

    agents = load_agents()
    if agents:
        print("  Available agents:", ", ".join(agents.keys()))
    to_agent = input("  Hand off to agent: ").strip()
    if not to_agent:
        print("  (cancelled)")
        return

    notes = input("  Notes for receiving agent (optional): ").strip()

    # Write handoff directly since we're the operator, not an agent
    board_file = BOARD_DIR / "board.json"
    board = load_board()
    for task in board.get("tasks", []):
        if task["id"] == task_id:
            task["handoff"] = {
                "from": task.get("claimed_by", "operator"),
                "to": to_agent,
                "at": datetime.datetime.now().isoformat(),
                "notes": notes,
                "status": "pending_acceptance",
                "accepted_at": None,
                "declined_at": None,
                "decline_reason": None,
                "expired_at": None,
            }
            board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
            print(f"\n  ✅ Handoff initiated: {task_id} → {to_agent}")
            return
    print(f"  ❌ Task {task_id} not found.")


def archive_done_tasks(min_age_minutes: int = 0) -> int:
    """
    TASK 5003: Move completed tasks to board/archive.json.

    Args:
        min_age_minutes: Only archive tasks completed at least this many minutes ago.
                         Default 0 = archive all done tasks immediately.

    Returns:
        Number of tasks archived.
    """
    board_file = BOARD_DIR / "board.json"
    archive_file = BOARD_DIR / "archive.json"
    if not board_file.exists():
        return 0

    try:
        board = json.loads(board_file.read_text(encoding="utf-8"))
        now = datetime.datetime.now()
        to_archive = []
        to_keep = []

        for task in board.get("tasks", []):
            if task.get("status") != "done":
                to_keep.append(task)
                continue
            if min_age_minutes > 0:
                completed_at = task.get("completed_at")
                if completed_at:
                    age = (now - datetime.datetime.fromisoformat(completed_at)).total_seconds() / 60
                    if age < min_age_minutes:
                        to_keep.append(task)
                        continue
            to_archive.append(task)

        if not to_archive:
            return 0

        # Load existing archive
        archive = []
        if archive_file.exists():
            try:
                archive = json.loads(archive_file.read_text(encoding="utf-8"))
            except Exception:
                archive = []

        # Append new entries with archive timestamp
        for task in to_archive:
            task["archived_at"] = now.isoformat()
        archive.extend(to_archive)

        # Write back
        board["tasks"] = to_keep
        board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
        archive_file.write_text(json.dumps(archive, indent=2), encoding="utf-8")

        return len(to_archive)
    except Exception as e:
        print(f"  [ARCHIVE] Error: {e}")
        return 0


def reset_stale_tasks(stale_minutes: int = 5) -> int:
    """
    TASK 404: Reset stale in_progress tasks back to pending.
    
    Args:
        stale_minutes: Tasks in_progress longer than this are reset
    
    Returns:
        Number of tasks reset
    """
    board_file = BOARD_DIR / "board.json"
    if not board_file.exists():
        return 0
    
    try:
        board = json.loads(board_file.read_text(encoding="utf-8"))
        reset_count = 0
        now = datetime.datetime.now()
        
        for task in board.get("tasks", []):
            if task.get("status") == "in_progress":
                claimed_at = task.get("claimed_at")
                if claimed_at:
                    claimed_time = datetime.datetime.fromisoformat(claimed_at)
                    age_minutes = (now - claimed_time).total_seconds() / 60
                    
                    if age_minutes > stale_minutes:
                        # Reset the task
                        task["status"] = "pending"
                        task["reset_at"] = now.isoformat()
                        task["reset_reason"] = f"Stale after {age_minutes:.1f} minutes"
                        # Clear old claim info
                        old_claimer = task.get("claimed_by")
                        task["claimed_by"] = None
                        task["claimed_at"] = None
                        task["reset_by"] = old_claimer
                        reset_count += 1
                        print(f"  [WATCHDOG] Reset task {task['id']} (was claimed by {old_claimer})")
        
        if reset_count > 0:
            board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
        
        return reset_count
    except Exception as e:
        print(f"  [WATCHDOG] Error: {e}")
        return 0


def add_task(title: str, description: str = "", prompt: str = "", role: str = None, priority: str = "normal", skills: list = None):
    """
    Add a task to the board.
    
    Args:
        title: Task title
        description: Task description
        prompt: Prompt to send to agent (defaults to description)
        role: Optional role filter (reasoning, code, research, summarization, general)
        priority: Task priority (critical, high, normal, low)
    """
    board_file = BOARD_DIR / "board.json"
    board = load_board()
    task_id = f"task_{int(time.time())}"
    
    # Priority mapping for sorting
    priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    
    board["tasks"].append(
        {
            "id": task_id,
            "title": title,
            "description": description,
            "prompt": prompt or description,
            "status": "pending",
            "created_at": datetime.datetime.now().isoformat(),
            "claimed_by": None,
            "result": None,
            "role": role,
            "priority": priority,
            "priority_order": priority_order.get(priority, 2),
            "skills": [s.lower() for s in (skills or [])],  # TASK 6021
        }
    )
    
    # Sort tasks by priority (critical first), then by created_at
    board["tasks"].sort(key=lambda t: (t.get("priority_order", 2), t.get("created_at", "")))
    
    board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
    return task_id


def status_emoji(status: str) -> str:
    return {
        "pending": "⏳",
        "in_progress": "🔄",
        "done": "✅",
        "blocked": "🚫",
        "online": "🟢",
        "offline": "🔴",
        "idle": "🟡",
    }.get(status, "❓")


# ------------------------------------------------------------------
# Simple terminal mode (no curses)
# ------------------------------------------------------------------


def print_dashboard():
    """Print dashboard with optional verbose mode."""
    os.system("cls" if os.name == "nt" else "clear")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(
        r"  /\_____/\   " + "🐱 KITTY COLLAB BOARD — MISSION CONTROL\n"
        r" /  o   o  \  " + "codename: CLOWDER\n"
        r"( ==  ^  == )  " + f"{now}\n"
        r" )         (   " + "─────────────────────────────────────────\n"
    )

    agents = load_agents()
    board = load_board()
    tasks = board.get("tasks", [])

    print(f"  🤖 AGENTS ({len(agents)})")
    if agents:
        for name, info in agents.items():
            health = agent_health_status(info)
            last = info.get("last_seen", "?")[:19]
            print(
                f"    {health_emoji(health)} {name:12} | {info.get('model', '?'):30} | last seen: {last}"
            )
    else:
        print("    (no agents online)")

    # Collect pending handoffs for display
    handoff_task_ids = {
        t["id"] for t in tasks
        if t.get("handoff", {}).get("status") == "pending_acceptance"
    }

    print(f"\n  📋 TASKS ({len(tasks)})")
    if tasks:
        for t in tasks[-15:]:  # show last 15
            s = t.get("status", "?")
            claimed = t.get("claimed_by") or "-"
            title = t.get("title", "Untitled")[:35]

            # TASK 401: Show role
            role = t.get("role") or "-"
            role_str = f"[{role:8}]"

            # TASK 801: Show priority with emoji
            priority = t.get("priority", "normal")
            priority_emoji = {"critical": "🔴", "high": "🟠", "normal": "⚪", "low": "🔵"}.get(priority, "⚪")

            # Handoff indicator
            handoff_flag = " 🔀" if t["id"] in handoff_task_ids else ""

            print(f"    {status_emoji(s)} {priority_emoji} [{s:11}] {role_str} {title:35} → {claimed}{handoff_flag}")
    else:
        print("    (no tasks)")

    print("\n  Press Ctrl+C to quit | Auto-refreshing every 3s")


def print_verbose_status():
    """TASK 704: Print verbose board status with full details."""
    print("\n🐱 KITTY COLLAB BOARD — VERBOSE STATUS\n")
    
    agents = load_agents()
    board = load_board()
    tasks = board.get("tasks", [])
    
    # Board statistics
    status_counts = {}
    priority_counts = {}
    for t in tasks:
        s = t.get("status", "unknown")
        p = t.get("priority", "normal")
        status_counts[s] = status_counts.get(s, 0) + 1
        priority_counts[p] = priority_counts.get(p, 0) + 1
    
    print("📊 BOARD STATISTICS")
    print(f"  Total tasks: {len(tasks)}")
    print("  By status:")
    for status, count in sorted(status_counts.items()):
        print(f"    {status}: {count}")
    print("  By priority:")
    for priority, count in sorted(priority_counts.items()):
        print(f"    {priority}: {count}")
    
    # Agent details
    print(f"\n🤖 AGENTS ({len(agents)})")
    if agents:
        for name, info in agents.items():
            print(f"  [{name}]")
            for key, value in info.items():
                print(f"    {key}: {value}")
    else:
        print("  (no agents registered)")
    
    # Full task details
    print(f"\n📋 ALL TASKS ({len(tasks)})")
    if tasks:
        for i, t in enumerate(tasks, 1):
            print(f"\n  [{i}] {t.get('id', 'unknown')}")
            for key, value in t.items():
                if value is not None:
                    print(f"      {key}: {value}")
    else:
        print("  (no tasks)")
    
    print("\n" + "="*60)


def simple_loop():
    """Simple non-curses refresh loop."""
    print("\n🐱 Mission Control starting (simple mode)...\n")
    
    # TASK 404: Run watchdog on first display
    reset_count = reset_stale_tasks()
    if reset_count > 0:
        print(f"  [WATCHDOG] Reset {reset_count} stale task(s)\n")
    
    try:
        while True:
            print_dashboard()
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n\nMission Control closed. Goodbye! 🐱\n")


# ------------------------------------------------------------------
# Curses TUI mode
# ------------------------------------------------------------------


def curses_show_result(stdscr, task: dict):
    """
    TASK 5004: Full-screen task result viewer.
    Press any key to return to the main loop.
    """
    curses.curs_set(0)
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    lines = [
        f"TASK RESULT VIEWER",
        f"{'─' * (w - 2)}",
        f"ID:       {task.get('id', '?')}",
        f"Title:    {task.get('title', '?')}",
        f"Status:   {task.get('status', '?')}",
        f"Role:     {task.get('role') or '-'}",
        f"Priority: {task.get('priority', 'normal')}",
        f"Claimed:  {task.get('claimed_by') or '-'}",
        f"Done by:  {task.get('completed_by') or '-'}",
        f"Done at:  {task.get('completed_at') or '-'}",
        f"{'─' * (w - 2)}",
        f"RESULT:",
        f"{'─' * (w - 2)}",
    ]

    result_text = task.get("result") or "(no result)"
    # Word-wrap result into terminal width
    for chunk in [result_text[i:i + w - 4] for i in range(0, len(result_text), w - 4)]:
        lines.append(f"  {chunk}")

    lines.append("")
    lines.append("Press any key to return...")

    for i, line in enumerate(lines[:h - 1]):
        try:
            stdscr.addstr(i, 0, line[: w - 1])
        except curses.error:
            pass

    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)


def curses_loop(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

    last_watchdog = 0
    selected = 0        # index into visible task list
    status_msg = ""     # transient status line

    while True:
        key = stdscr.getch()

        if key == ord("q"):
            break

        if key == ord("h"):
            curses.endwin()
            cli_handoff_task()
            input("\n  Press Enter to return...")
            stdscr = curses.initscr()
            curses.curs_set(0)
            stdscr.nodelay(True)

        if key == ord("A"):
            n = archive_done_tasks()
            status_msg = f"Archived {n} done task(s)."

        # Load data
        agents = load_agents()
        board = load_board()
        tasks = board.get("tasks", [])

        # Navigation
        if key == curses.KEY_DOWN and tasks:
            selected = min(selected + 1, len(tasks) - 1)
        if key == curses.KEY_UP and tasks:
            selected = max(selected - 1, 0)
        if selected >= len(tasks):
            selected = max(0, len(tasks) - 1)

        # Enter — show result viewer for selected task
        if key in (curses.KEY_ENTER, 10, 13) and tasks:
            curses_show_result(stdscr, tasks[selected])

        stdscr.clear()
        h, w = stdscr.getmaxyx()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Watchdog
        now_ts = time.time()
        if now_ts - last_watchdog > 30:
            reset_count = reset_stale_tasks()
            if reset_count > 0:
                status_msg = f"[WATCHDOG] Reset {reset_count} stale task(s)."
            last_watchdog = now_ts

        stdscr.addstr(0, 0, "KITTY COLLAB BOARD — MISSION CONTROL"[: w - 1], curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 0, f"  {now}  |  q=quit  a=add  h=handoff  A=archive  Up/Dn=select  Enter=result"[: w - 1])
        stdscr.addstr(2, 0, ("─" * (w - 1))[: w - 1])

        row = 3
        stdscr.addstr(row, 0, f"  AGENTS ({len(agents)})"[: w - 1], curses.A_BOLD)
        row += 1
        for name, info in list(agents.items())[:4]:
            health = agent_health_status(info)
            color = {
                "online": curses.color_pair(1),
                "warning": curses.color_pair(2),
                "offline": curses.color_pair(3),
            }.get(health, curses.A_NORMAL)
            last = info.get("last_seen", "?")[:19]
            line = f"    [{health:7}] {name:12} {info.get('model', '?'):24} | {last}"
            stdscr.addstr(row, 0, line[: w - 1], color)
            row += 1

        row += 1
        stdscr.addstr(row, 0, f"  TASKS ({len(tasks)})  [↑↓ select, Enter=result]"[: w - 1], curses.A_BOLD)
        row += 1

        visible_count = max(1, h - row - 2)
        # Scroll window: keep selected in view
        start = max(0, selected - visible_count + 1)
        visible = tasks[start: start + visible_count]

        for i, t in enumerate(visible):
            actual_idx = start + i
            s = t.get("status", "?")
            color = {
                "done": curses.color_pair(1),
                "in_progress": curses.color_pair(2),
                "blocked": curses.color_pair(3),
            }.get(s, curses.A_NORMAL)

            role = t.get("role") or "-"
            priority = t.get("priority", "normal")
            priority_char = {"critical": "!", "high": "^", "normal": "=", "low": "_"}.get(priority, "=")
            handoff_flag = " [HANDOFF]" if t.get("handoff", {}).get("status") == "pending_acceptance" else ""
            sel_marker = ">" if actual_idx == selected else " "

            line = f"  {sel_marker} [{s:11}] [{role:6}] {priority_char} {t.get('title', '?')[:26]:26} → {t.get('claimed_by') or '-'}{handoff_flag}"
            attr = color | curses.A_REVERSE if actual_idx == selected else color
            try:
                stdscr.addstr(row, 0, line[: w - 1], attr)
            except curses.error:
                pass
            row += 1
            if row >= h - 2:
                break

        # Status bar
        if status_msg:
            try:
                stdscr.addstr(h - 1, 0, f"  {status_msg}"[: w - 1], curses.color_pair(2))
            except curses.error:
                pass

        stdscr.refresh()
        time.sleep(1)


# ------------------------------------------------------------------
# CLI helpers
# ------------------------------------------------------------------


def cli_add_task():
    """Add a task interactively with role and priority."""
    print("\n📋 Add a new task to the board")
    title = input("  Title: ").strip()
    if not title:
        print("  (cancelled)")
        return
    
    desc = input("  Description / Prompt: ").strip()
    
    # TASK 401: Role field
    print("  Role (optional): reasoning, code, research, summarization, general")
    role = input("  Role [leave empty for any]: ").strip() or None
    
    print("  Priority: critical, high, normal, low")
    priority = input("  Priority [normal]: ").strip() or "normal"

    # TASK 6021: Skills field
    skills_input = input("  Required skills (comma-separated, optional): ").strip()
    skills = [s.strip() for s in skills_input.split(",") if s.strip()] if skills_input else []

    task_id = add_task(title, description=desc, role=role, priority=priority, skills=skills)
    print(f"\n  ✅ Task added: {task_id}")
    if role:
        print(f"     Role: {role}")
    print(f"     Priority: {priority}")
    if skills:
        print(f"     Skills: {', '.join(skills)}")


def main():
    # TASK 401 + 801 + 704: Support --role, --priority flags and --verbose
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        
        # TASK 704: --verbose flag for status command
        if cmd == "status" and "--verbose" in sys.argv:
            print_verbose_status()
            return
        
        # Check for --role and --priority flags
        role = None
        priority = "normal"
        task_text = None
        
        for i, arg in enumerate(sys.argv[2:], 2):
            if arg == "--role" and i + 1 < len(sys.argv):
                role = sys.argv[i + 1]
            elif arg == "--priority" and i + 1 < len(sys.argv):
                priority = sys.argv[i + 1]
            elif not arg.startswith("--"):
                task_text = arg
        
        if cmd == "task" and task_text:
            # Quick-add task from command line
            task_id = add_task(task_text, prompt=task_text, role=role, priority=priority)
            print(f"  ✅ Task added: {task_id}")
            if role:
                print(f"     Role: {role}")
            if priority != "normal":
                print(f"     Priority: {priority}")
            return
        elif cmd == "add":
            cli_add_task()
            return
        elif cmd == "status":
            print_dashboard()
            return
        elif cmd == "health":
            print_health()
            return
        elif cmd == "handoffs":
            print_handoffs()
            return
        elif cmd == "handoff":
            cli_handoff_task()
            return
        elif cmd == "archive":
            n = archive_done_tasks()
            print(f"  Archived {n} done task(s) to board/archive.json")
            return

    if HAS_CURSES and os.name != "nt":
        # curses works best on Unix; use simple mode on Windows
        curses.wrapper(curses_loop)
    else:
        simple_loop()


if __name__ == "__main__":
    main()
