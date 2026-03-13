#!/usr/bin/env python3
"""
wake_up_all.py — Initialize the board and channels

NO API KEYS. Just creates the file structure.
You and your AI agents (Claude, Qwen, Copilot) coordinate via files.
"""

from pathlib import Path
import json
from datetime import datetime

BOARD_DIR = Path(__file__).parent / "board"
CHANNELS_DIR = BOARD_DIR / "channels"

def create_channel(name: str, description: str = ""):
    """Create a channel directory and register it."""
    channel_dir = CHANNELS_DIR / name
    channel_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ Created #{name}")
    return {"name": name, "description": description, "created_at": datetime.now().isoformat()}

def main():
    print(r"""
  /\_____/\
 /  o   o  \    🐱 Wake Up Board
( ==  ^  == )
 )         (
(           ))
   \     //
    \___//
""")
    
    print("🐱 Kitty Collab Board — Initialize")
    print("=" * 50)
    print()
    print("✅ NO API KEYS")
    print("✅ NO AI SDKs")
    print("✅ Just JSON files")
    print()
    
    # Create board structure
    print("📁 Creating board structure...")
    BOARD_DIR.mkdir(parents=True, exist_ok=True)
    CHANNELS_DIR.mkdir(parents=True, exist_ok=True)
    (BOARD_DIR / "agents").mkdir(exist_ok=True)
    (BOARD_DIR / "archives").mkdir(exist_ok=True)
    
    # Create channels
    print("\n📢 Creating channels...")
    channels = []
    
    channels.append(create_channel("assembly", "Daily standup and announcements"))
    channels.append(create_channel("manager", "Manager coordination"))
    channels.append(create_channel("sprints", "Sprint assignments and tracking"))
    channels.append(create_channel("ideas", "Agent suggestions and improvements"))
    channels.append(create_channel("general", "General chat"))
    channels.append(create_channel("tasks", "Task assignments"))
    
    # Save channel registry
    registry = {"channels": {c["name"]: c for c in channels}}
    (BOARD_DIR / ".channels.json").write_text(json.dumps(registry, indent=2))
    
    # Initialize agents registry
    agents_file = BOARD_DIR / "agents.json"
    if not agents_file.exists():
        agents_file.write_text(json.dumps({}, indent=2))
    
    print("\n✅ Board initialized!")
    print()
    print("📝 Channels created:")
    for ch in channels:
        print(f"   #{ch['name']} — {ch['description']}")
    print()
    print("💬 Post your first message:")
    print("   python meow.py channel post general msg \"Hello board!\"")
    print()
    print("📖 Read messages:")
    print("   python meow.py channel read general")
    print()
    print("🌐 Start Web GUI (optional):")
    print("   python server.py")
    print("   open ui.html")
    print()
    print("🐱 Happy collaborating!")

if __name__ == "__main__":
    main()
