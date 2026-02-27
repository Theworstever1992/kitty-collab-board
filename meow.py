"""
meow.py — Kitty Collab Board
Main CLI entry point for the Clowder multi-agent system.

Usage:
  python meow.py              # show status
  python meow.py mc           # open Mission Control
  python meow.py wake         # run wake_up
  python meow.py add          # add a task
  python meow.py spawn        # spawn all agents
  python meow.py task <text>  # quick-add a task from the command line
"""

import sys
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent


def banner():
    print(r"""
  /\_____/\
 /  o   o  \    🐱 Kitty Collab Board (Clowder)
( ==  ^  == )   
 )         (    
(           ))  
   \     //
    \___//
""")


def run_wake():
    subprocess.run([sys.executable, str(ROOT / "wake_up.py")])


def run_mc():
    subprocess.run([sys.executable, str(ROOT / "mission_control.py")])


def run_add():
    subprocess.run([sys.executable, str(ROOT / "mission_control.py"), "add"])


def run_spawn():
    ps1 = ROOT / "windows" / "spawn_agents.ps1"
    if ps1.exists():
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)])
    else:
        print("  spawn_agents.ps1 not found.")


def quick_task(text: str):
    from mission_control import add_task

    task_id = add_task(text, prompt=text)
    print(f"  ✅ Task added: {task_id} — '{text}'")


def show_status():
    subprocess.run([sys.executable, str(ROOT / "mission_control.py"), "status"])


HELP = """
Commands:
  meow                → show board status
  meow mc             → open Mission Control TUI
  meow wake           → run wake_up (initialize board + aliases)
  meow add            → add a task interactively
  meow spawn          → spawn all agents via PowerShell
  meow task <text>    → quickly add a task from the command line
  meow help           → show this help
"""


def main():
    args = sys.argv[1:]
    if not args:
        banner()
        show_status()
        return

    cmd = args[0].lower()
    if cmd == "mc":
        run_mc()
    elif cmd == "wake":
        run_wake()
    elif cmd == "add":
        run_add()
    elif cmd == "spawn":
        run_spawn()
    elif cmd == "task" and len(args) > 1:
        quick_task(" ".join(args[1:]))
    elif cmd in ("help", "--help", "-h"):
        print(HELP)
    else:
        print(f"  Unknown command: {cmd}")
        print(HELP)


if __name__ == "__main__":
    main()
