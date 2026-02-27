"""
wake_up.py — Kitty Collab Board
Initializes the board environment and prints shell alias setup instructions.
Run this first thing on a new machine/session.
"""

import json
import os
import sys
import datetime
from pathlib import Path

BOARD_ROOT = Path(__file__).parent
BOARD_DIR = BOARD_ROOT / "board"
LOG_DIR = BOARD_ROOT / "logs"


def banner():
    print(r"""
  /\_____/\
 /  o   o  \    🐱 Kitty Collab Board
( ==  ^  == )   codename: CLOWDER
 )         (    
(           ))  wake_up.py — initializing...
   \     //
    \___//
""")


def init_board():
    """Create board files if they don't exist."""
    BOARD_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)

    board_file = BOARD_DIR / "board.json"
    if not board_file.exists():
        board = {
            "created_at": datetime.datetime.now().isoformat(),
            "tasks": [],
        }
        board_file.write_text(json.dumps(board, indent=2), encoding="utf-8")
        print(f"  ✅ Created board: {board_file}")
    else:
        print(f"  ✅ Board exists: {board_file}")

    agents_file = BOARD_DIR / "agents.json"
    if not agents_file.exists():
        agents_file.write_text("{}", encoding="utf-8")
        print(f"  ✅ Created agents registry: {agents_file}")
    else:
        print(f"  ✅ Agents file exists: {agents_file}")


def print_aliases():
    """Print PowerShell alias setup commands to paste into your profile."""
    root = BOARD_ROOT.resolve()
    print("\n📋 Paste these into your PowerShell $PROFILE to set up aliases:\n")
    print(f'  function wake_up    {{ python "{root}\\wake_up.py" @args }}')
    print(f'  function meow       {{ python "{root}\\meow.py" @args }}')
    print(f'  function mc         {{ python "{root}\\mission_control.py" @args }}')
    print(f'  function clowder    {{ python "{root}\\meow.py" @args }}')
    print()
    print(
        f"  Your $PROFILE is at: {os.environ.get('USERPROFILE', 'C:\\Users\\<you>')}\\Documents\\PowerShell\\Microsoft.PowerShell_profile.ps1"
    )


def main():
    banner()
    print("Initializing Kitty Collab Board...\n")
    init_board()
    print_aliases()
    print("\n✅ All done! Run `meow` or `python meow.py` to get started.\n")


if __name__ == "__main__":
    main()
