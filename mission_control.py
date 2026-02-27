"""
mission_control.py — Kitty Collab Board
TUI dashboard for monitoring agents and tasks on the board.
Press 'q' to quit, 'r' to refresh, 'a' to add a task.
"""

import json
import os
import sys
import time
import datetime
from pathlib import Path

BOARD_ROOT = Path(__file__).parent
BOARD_DIR = BOARD_ROOT / "board"

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


def add_task(title: str, description: str = "", prompt: str = ""):
    board_file = BOARD_DIR / "board.json"
    board = load_board()
    task_id = f"task_{int(time.time())}"
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
        }
    )
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
    os.system("cls" if os.name == "nt" else "clear")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"""
  /\_____/\   🐱 KITTY COLLAB BOARD — MISSION CONTROL
 /  o   o  \  codename: CLOWDER
( ==  ^  == )  {now}
 )         (   ─────────────────────────────────────────
""")

    agents = load_agents()
    board = load_board()
    tasks = board.get("tasks", [])

    print(f"  🤖 AGENTS ({len(agents)})")
    if agents:
        for name, info in agents.items():
            s = info.get("status", "unknown")
            last = info.get("last_seen", "?")[:19]
            print(
                f"    {status_emoji(s)} {name:12} | {info.get('model', '?'):30} | last seen: {last}"
            )
    else:
        print("    (no agents online)")

    print(f"\n  📋 TASKS ({len(tasks)})")
    if tasks:
        for t in tasks[-15:]:  # show last 15
            s = t.get("status", "?")
            claimed = t.get("claimed_by") or "-"
            title = t.get("title", "Untitled")[:45]
            print(f"    {status_emoji(s)} [{s:11}] {title:45} → {claimed}")
    else:
        print("    (no tasks)")

    print("\n  Press Ctrl+C to quit | Auto-refreshing every 3s")


def simple_loop():
    """Simple non-curses refresh loop."""
    print("\n🐱 Mission Control starting (simple mode)...\n")
    try:
        while True:
            print_dashboard()
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n\nMission Control closed. Goodbye! 🐱\n")


# ------------------------------------------------------------------
# Curses TUI mode
# ------------------------------------------------------------------


def curses_loop(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break

        stdscr.clear()
        h, w = stdscr.getmaxyx()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = "🐱 KITTY COLLAB BOARD — MISSION CONTROL"
        stdscr.addstr(0, 0, header[: w - 1], curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 0, f"  {now}  |  q=quit  r=refresh  a=add task"[: w - 1])
        stdscr.addstr(2, 0, "─" * (w - 1))

        row = 3
        agents = load_agents()
        board = load_board()
        tasks = board.get("tasks", [])

        stdscr.addstr(row, 0, f"  AGENTS ({len(agents)})"[: w - 1], curses.A_BOLD)
        row += 1
        for name, info in list(agents.items())[:5]:
            s = info.get("status", "?")
            color = curses.color_pair(1) if s == "online" else curses.color_pair(3)
            line = f"    [{s:7}] {name:12} {info.get('model', '?')}"
            stdscr.addstr(row, 0, line[: w - 1], color)
            row += 1

        row += 1
        stdscr.addstr(row, 0, f"  TASKS ({len(tasks)})"[: w - 1], curses.A_BOLD)
        row += 1
        for t in tasks[-max(1, h - row - 3) :]:
            s = t.get("status", "?")
            color = {
                "done": curses.color_pair(1),
                "in_progress": curses.color_pair(2),
                "blocked": curses.color_pair(3),
            }.get(s, curses.A_NORMAL)
            line = f"    [{s:11}] {t.get('title', '?')[:40]:40} → {t.get('claimed_by') or '-'}"
            stdscr.addstr(row, 0, line[: w - 1], color)
            row += 1
            if row >= h - 1:
                break

        stdscr.refresh()
        time.sleep(3)


# ------------------------------------------------------------------
# CLI helpers
# ------------------------------------------------------------------


def cli_add_task():
    print("\n📋 Add a new task to the board")
    title = input("  Title: ").strip()
    if not title:
        print("  (cancelled)")
        return
    desc = input("  Description / Prompt: ").strip()
    task_id = add_task(title, description=desc)
    print(f"\n  ✅ Task added: {task_id}")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "add":
            cli_add_task()
            return
        elif cmd == "status":
            print_dashboard()
            return

    if HAS_CURSES and os.name != "nt":
        # curses works best on Unix; use simple mode on Windows
        curses.wrapper(curses_loop)
    else:
        simple_loop()


if __name__ == "__main__":
    main()
