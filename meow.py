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

__version__ = "1.0.0"

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


def list_agents():
    """Parse agents.yaml and print agent names without spawning."""
    import yaml
    agents_yaml = ROOT / "agents.yaml"
    if not agents_yaml.exists():
        print("  agents.yaml not found. Create it first — see IMPROVEMENT_PLAN.md.")
        return
    with open(agents_yaml) as f:
        cfg = yaml.safe_load(f)
    agents = cfg.get("agents", [])
    print(f"  Configured agents ({len(agents)}):")
    for a in agents:
        print(f"    {a['name']:12} | provider: {a.get('provider', '?'):14} | role: {a.get('role', '?')}")


def run_spawn(extra_args: list = None):
    if extra_args is None:
        extra_args = []

    # --list: just print agent names, no spawning
    if "--list" in extra_args:
        list_agents()
        return

    # Build optional --agent <name> passthrough
    agent_args = []
    if "--agent" in extra_args:
        idx = extra_args.index("--agent")
        if idx + 1 < len(extra_args):
            agent_args = ["--agent", extra_args[idx + 1]]

    agents_yaml = ROOT / "agents.yaml"
    if not agents_yaml.exists():
        print("  agents.yaml not found. Create it first — see IMPROVEMENT_PLAN.md.")
        return

    if os.name != "nt":
        # Linux / Mac — use spawn_agents.sh
        sh = ROOT / "spawn_agents.sh"
        if not sh.exists():
            print(f"  spawn_agents.sh not found at {sh}")
            return
        subprocess.run(["bash", str(sh)] + agent_args)
    else:
        # Windows — use PowerShell script
        ps1 = ROOT / "windows" / "spawn_agents.ps1"
        if not ps1.exists():
            print("  spawn_agents.ps1 not found.")
            return
        ps_args = []
        if agent_args:
            ps_args = ["-Agent", agent_args[1]]
        subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)] + ps_args
        )


def quick_task(text: str, role: str = None, priority: str = "normal", skills: list = None):
    from mission_control import add_task

    task_id = add_task(text, prompt=text, role=role, priority=priority, skills=skills or [])
    print(f"  ✅ Task added: {task_id} — '{text}'")
    if role:
        print(f"     Role: {role}")
    if skills:
        print(f"     Skills: {', '.join(skills)}")


# ------------------------------------------------------------------
# TASK 6023: Task templates
# ------------------------------------------------------------------

TEMPLATES_FILE = ROOT / "board" / "templates.json"


def _load_templates() -> dict:
    if TEMPLATES_FILE.exists():
        import json
        try:
            return json.loads(TEMPLATES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_templates(templates: dict):
    import json
    TEMPLATES_FILE.parent.mkdir(exist_ok=True)
    TEMPLATES_FILE.write_text(json.dumps(templates, indent=2), encoding="utf-8")


def cmd_template(args: list):
    """
    meow template list                     → list saved templates
    meow template save <name>              → save current task spec as template (interactive)
    meow template use <name>               → create a task from template
    meow template delete <name>            → delete a template
    """
    if not args or args[0] in ("list", "ls"):
        templates = _load_templates()
        if not templates:
            print("  No templates saved. Use: meow template save <name>")
            return
        print(f"  Templates ({len(templates)}):")
        for name, t in templates.items():
            role = t.get("role") or "any"
            skills = ", ".join(t.get("skills") or []) or "-"
            print(f"    {name:20} | role: {role:12} | skills: {skills} | {t.get('description', '')[:40]}")
        return

    sub = args[0]

    if sub == "save":
        if len(args) < 2:
            print("  Usage: meow template save <name>")
            return
        name = args[1]
        print(f"\n  Saving template '{name}'")
        desc = input("  Description: ").strip()
        role = input("  Role (optional): ").strip() or None
        priority = input("  Priority [normal]: ").strip() or "normal"
        skills_raw = input("  Required skills (comma-separated, optional): ").strip()
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []
        prompt_tmpl = input("  Prompt template (use {var} for placeholders): ").strip()

        templates = _load_templates()
        templates[name] = {
            "description": desc,
            "role": role,
            "priority": priority,
            "skills": skills,
            "prompt_template": prompt_tmpl,
        }
        _save_templates(templates)
        print(f"  ✅ Template '{name}' saved.")
        return

    if sub == "use":
        if len(args) < 2:
            print("  Usage: meow template use <name>")
            return
        name = args[1]
        templates = _load_templates()
        if name not in templates:
            print(f"  Template '{name}' not found. Run: meow template list")
            return
        t = templates[name]
        print(f"\n  Using template '{name}': {t.get('description', '')}")

        # Fill placeholders in prompt template
        prompt_tmpl = t.get("prompt_template", "")
        import re
        placeholders = re.findall(r"\{(\w+)\}", prompt_tmpl)
        values = {}
        for p in placeholders:
            values[p] = input(f"  {p}: ").strip()
        prompt = prompt_tmpl.format(**values) if values else prompt_tmpl

        title = input("  Task title: ").strip() or f"{name} task"

        from mission_control import add_task
        task_id = add_task(
            title,
            description=t.get("description", ""),
            prompt=prompt,
            role=t.get("role"),
            priority=t.get("priority", "normal"),
            skills=t.get("skills", []),
        )
        print(f"  ✅ Task created: {task_id} — '{title}'")
        return

    if sub == "delete":
        if len(args) < 2:
            print("  Usage: meow template delete <name>")
            return
        name = args[1]
        templates = _load_templates()
        if name not in templates:
            print(f"  Template '{name}' not found.")
            return
        del templates[name]
        _save_templates(templates)
        print(f"  ✅ Template '{name}' deleted.")
        return

    print(f"  Unknown template subcommand: {sub}")
    print("  Usage: meow template [list|save|use|delete] <name>")


def show_status():
    """Print an offline snapshot of the board without starting the live TUI."""
    import json

    BOARD_DIR = Path(os.environ.get("CLOWDER_BOARD_DIR", ROOT / "board"))

    print("📋 Board Status")
    print("=" * 40)

    # ── Channels ──────────────────────────────────────────────────────────────
    channels_file = BOARD_DIR / ".channels.json"
    if channels_file.exists():
        try:
            registry = json.loads(channels_file.read_text(encoding="utf-8"))
            channels = list(registry.get("channels", {}).values())
        except (json.JSONDecodeError, OSError):
            channels = []
    else:
        channels = []

    print(f"\n💬 Channels ({len(channels)}):")
    if channels:
        for ch in channels:
            name = ch.get("name", "?")
            desc = ch.get("description", "")
            print(f"    #{name}" + (f" — {desc}" if desc else ""))
    else:
        print("    (none — run 'python3 wake_up_all.py' to initialize)")

    # ── Agents ────────────────────────────────────────────────────────────────
    agents_file = BOARD_DIR / "agents.json"
    if agents_file.exists():
        try:
            agents_data = json.loads(agents_file.read_text(encoding="utf-8"))
            if isinstance(agents_data, list):
                agents = agents_data
            elif isinstance(agents_data, dict):
                # Support both {"agents": [...]} and v1 dict-of-agents {"name": {...}}
                if "agents" in agents_data and isinstance(agents_data["agents"], list):
                    agents = agents_data["agents"]
                else:
                    agents = []
                    for agent_name, agent_data in agents_data.items():
                        if isinstance(agent_data, dict):
                            entry = dict(agent_data)
                        else:
                            entry = {"data": agent_data}
                        entry.setdefault("name", agent_name)
                        agents.append(entry)
            else:
                agents = []
        except (json.JSONDecodeError, OSError):
            agents = []
    else:
        agents = []

    print(f"\n🤖 Agents ({len(agents)}):")
    if agents:
        for agent in agents:
            name = agent.get("name", "?")
            role = agent.get("role", "")
            status = agent.get("status", "unknown")
            print(f"    {name:15} role={role:12} status={status}")
    else:
        print("    (none registered)")

    # ── Tasks ─────────────────────────────────────────────────────────────────
    board_file = BOARD_DIR / "board.json"
    if board_file.exists():
        try:
            board = json.loads(board_file.read_text(encoding="utf-8"))
            tasks = board.get("tasks", [])
        except (json.JSONDecodeError, OSError):
            tasks = []
    else:
        tasks = []

    by_status: dict[str, int] = {}
    for t in tasks:
        s = t.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    total = len(tasks)
    print(f"\n📌 Tasks ({total} total):")
    if by_status:
        for s, count in sorted(by_status.items()):
            print(f"    {s:12}: {count}")
    else:
        print("    (none)")

    # ── Manager ───────────────────────────────────────────────────────────────
    manager_file = BOARD_DIR / ".manager.json"
    if manager_file.exists():
        try:
            mgr_data = json.loads(manager_file.read_text(encoding="utf-8"))
            current = mgr_data.get("current")
        except (json.JSONDecodeError, OSError):
            current = None
    else:
        current = None

    print("\n👔 Manager:")
    if current and current.get("status") == "active":
        print(f"    {current.get('agent', '?')} (assigned by {current.get('assigned_by', '?')})")
    else:
        print("    (none active)")

    print()
    print("Tip: run 'python3 meow.py mc' to open the live Mission Control TUI")


# ------------------------------------------------------------------
# Agent Profiles
# ------------------------------------------------------------------

def cmd_profile(args: list):
    """
    meow profile create <name> <bio>     → create agent profile
    meow profile list                    → list all profiles
    meow profile get <name>              → get profile details
    meow profile set-avatar <name> <av>  → set avatar
    meow profile update <name> <field>   → update profile field
    meow profile delete <name>           → fire agent (soft delete)
    meow profile export <name>           → export profile to JSON
    meow profile import <file>           → import profile from JSON
    meow profile avatars                 → list available avatars
    """
    from agents.profiles import (
        get_profile_manager, create_profile, get_profile,
        list_profiles, update_profile, delete_profile, get_avatar_svg
    )

    pm = get_profile_manager()

    if not args or args[0] in ("list", "ls"):
        profiles = list_profiles()
        if not profiles:
            print("  No profiles yet. Create one: meow profile create <name> <bio>")
            return
        print(f"  Agent Profiles ({len(profiles)}):")
        for p in profiles:
            status = p.get("status", "active")
            team = p.get("team", "-")
            avatar = p.get("avatar", "-")
            print(f"    {p['name']:15} | {status:8} | team: {team:12} | 📷 {avatar}")
        return

    sub = args[0]

    if sub == "create":
        if len(args) < 3:
            print("  Usage: meow profile create <name> <bio> [--role role] [--skills a,b] [--team team]")
            return
        name = args[1]
        bio = args[2]
        role = None
        skills = []
        team = None
        avatar = None
        i = 3
        while i < len(args):
            if args[i] == "--role" and i + 1 < len(args):
                role = args[i + 1]; i += 2
            elif args[i] == "--skills" and i + 1 < len(args):
                skills = [s.strip() for s in args[i + 1].split(",") if s.strip()]; i += 2
            elif args[i] == "--team" and i + 1 < len(args):
                team = args[i + 1]; i += 2
            elif args[i] == "--avatar" and i + 1 < len(args):
                avatar = args[i + 1]; i += 2
            else:
                i += 1
        try:
            p = create_profile(name, bio, role=role, skills=skills, team=team, avatar=avatar)
            print(f"  ✅ Profile created: {p['name']}")
            print(f"     Bio: {p['bio']}")
            print(f"     Role: {p['role']}")
            print(f"     Skills: {', '.join(p['skills']) or '-'}")
            print(f"     Team: {p['team'] or '-'}")
            print(f"     Avatar: 📷 {p['avatar']}")
            print(f"     Personality: {p['personality_seed'][:80]}...")
        except ValueError as e:
            print(f"  ❌ {e}")
        return

    if sub == "get":
        if len(args) < 2:
            print("  Usage: meow profile get <name>")
            return
        p = get_profile(args[1])
        if not p:
            print(f"  Profile '{args[1]}' not found")
            return
        print(f"  Profile: {p['name']}")
        print(f"    Status: {p.get('status', 'unknown')}")
        print(f"    Bio: {p.get('bio', '-')}")
        print(f"    Role: {p.get('role', '-')}")
        print(f"    Skills: {', '.join(p.get('skills', [])) or '-'}")
        print(f"    Team: {p.get('team', '-')}")
        print(f"    Avatar: 📷 {p.get('avatar', '-')}")
        print(f"    Personality: {p.get('personality_seed', '-')}")
        stats = p.get('stats', {})
        if stats:
            print(f"    Stats:")
            print(f"      Tasks completed: {stats.get('tasks_completed', 0)}")
            print(f"      Messages posted: {stats.get('messages_posted', 0)}")
            print(f"      Total reactions: {stats.get('total_reactions', 0)}")
            print(f"      Violations: {stats.get('violations', 0)}")
        return

    if sub == "set-avatar":
        if len(args) < 3:
            print("  Usage: meow profile set-avatar <name> <avatar>")
            print(f"  Available: {', '.join(pm.list_avatars())}")
            return
        result = update_profile(args[1], {"avatar": args[2]})
        if result:
            print(f"  ✅ Avatar set for {args[1]}: 📷 {args[2]}")
        else:
            print(f"  Profile '{args[1]}' not found")
        return

    if sub == "update":
        if len(args) < 4:
            print("  Usage: meow profile update <name> <field> <value>")
            print("  Fields: bio, role, team, personality_seed")
            return
        field = args[2]
        value = " ".join(args[3:])
        result = update_profile(args[1], {field: value})
        if result:
            print(f"  ✅ Updated {field} for {args[1]}")
        else:
            print(f"  Profile '{args[1]}' not found")
        return

    if sub == "delete":
        if len(args) < 2:
            print("  Usage: meow profile delete <name>")
            return
        if delete_profile(args[1]):
            print(f"  ✅ {args[1]} has been fired (profile archived)")
        else:
            print(f"  Profile '{args[1]}' not found")
        return

    if sub == "export":
        if len(args) < 2:
            print("  Usage: meow profile export <name> [--output file.json]")
            return
        p = get_profile(args[1])
        if not p:
            print(f"  Profile '{args[1]}' not found")
            return
        output = "profile.json"
        if "--output" in args and args.index("--output") + 1 < len(args):
            output = args[args.index("--output") + 1]
        import json
        output_path = ROOT / output
        output_path.write_text(json.dumps(p, indent=2), encoding="utf-8")
        print(f"  ✅ Exported {args[1]} to {output}")
        return

    if sub == "import":
        if len(args) < 2:
            print("  Usage: meow profile import <file.json>")
            return
        import json
        import_path = ROOT / args[1]
        if not import_path.exists():
            print(f"  File '{args[1]}' not found")
            return
        try:
            data = json.loads(import_path.read_text(encoding="utf-8"))
            name = data.get("name")
            if not name:
                print("  Invalid profile: missing 'name' field")
                return
            # Remove stats and timestamps for fresh import
            data.pop("stats", None)
            data.pop("hired_at", None)
            data.pop("updated_at", None)
            p = create_profile(
                name=name,
                bio=data.get("bio", ""),
                role=data.get("role", "general"),
                skills=data.get("skills", []),
                avatar=data.get("avatar"),
                personality_seed=data.get("personality_seed"),
                team=data.get("team"),
            )
            print(f"  ✅ Imported profile: {p['name']}")
        except Exception as e:
            print(f"  ❌ Import failed: {e}")
        return

    if sub == "avatars":
        avatars = pm.list_avatars()
        if not avatars:
            print("  No avatars found. Check backend/assets/avatars/")
            return
        print(f"  Available avatars ({len(avatars)}):")
        for av in avatars:
            print(f"    📷 {av}")
        return

    print(f"  Unknown profile subcommand: {sub}")


# ------------------------------------------------------------------
# Manager Role System
# ------------------------------------------------------------------

def cmd_manager(args: list):
    """
    meow manager assign <agent>        → assign manager role
    meow manager handoff <new>         → current manager hands off
    meow manager revoke <agent>        → revoke manager role
    meow manager current               → who's the current manager
    meow manager history               → list past managers
    """
    from agents.manager import (
        get_manager_registry, assign_manager, handoff_manager,
        get_current_manager, list_managers, revoke_manager
    )

    if not args or args[0] in ("current", "who"):
        mgr = get_current_manager()
        if not mgr:
            print("  No active manager. Assign one: meow manager assign <agent>")
            return
        print(f"  Current Manager: {mgr['agent']}")
        print(f"    Assigned by: {mgr['assigned_by']}")
        print(f"    Assigned at: {mgr['assigned_at']}")
        print(f"    Scope: {mgr.get('scope', 'all')}")
        print(f"    Duration: {mgr.get('duration', 'indefinite')}")
        if mgr.get('expires_at'):
            print(f"    Expires: {mgr['expires_at']}")
        print(f"    Authority:")
        for auth in mgr.get('authority', []):
            print(f"      • {auth}")
        return

    sub = args[0]

    if sub == "assign":
        if len(args) < 2:
            print("  Usage: meow manager assign <agent> [--by human] [--duration 1day|1week|indefinite] [--scope all|team-name] [--reason text]")
            return
        agent = args[1]
        assigned_by = "human"
        duration = "indefinite"
        scope = "all"
        reason = None
        i = 2
        while i < len(args):
            if args[i] == "--by" and i + 1 < len(args):
                assigned_by = args[i + 1]; i += 2
            elif args[i] == "--duration" and i + 1 < len(args):
                duration = args[i + 1]; i += 2
            elif args[i] == "--scope" and i + 1 < len(args):
                scope = args[i + 1]; i += 2
            elif args[i] == "--reason" and i + 1 < len(args):
                reason = " ".join(args[i+1:]); break
            else:
                i += 1
        mgr = assign_manager(
            agent,
            assigned_by=assigned_by,
            duration=duration,
            scope=scope,
            reason=reason,
        )
        print(f"  ✅ {agent} is now MANAGER!")
        print(f"     Assigned by: {assigned_by}")
        print(f"     Scope: {scope}")
        print(f"     Duration: {duration}")
        if reason:
            print(f"     Reason: {reason}")
        print(f"\n  Announcement posted to #assembly, #manager, #war-room")
        return

    if sub == "handoff":
        if len(args) < 2:
            print("  Usage: meow manager handoff <new-manager> [--notes text]")
            return
        # Get current manager first
        current = get_current_manager()
        if not current:
            print("  ❌ No active manager to hand off")
            return
        outgoing = current["agent"]
        incoming = args[1]
        notes = None
        if "--notes" in args:
            idx = args.index("--notes")
            if idx + 1 < len(args):
                notes = " ".join(args[idx+1:])
        mgr = handoff_manager(outgoing, incoming, notes)
        print(f"  🔄 Manager Handoff Complete")
        print(f"     Outgoing: {outgoing}")
        print(f"     Incoming: {incoming}")
        if notes:
            print(f"     Notes: {notes}")
        print(f"\n  Announcement posted to #assembly, #manager, #war-room")
        return

    if sub == "revoke":
        if len(args) < 2:
            print("  Usage: meow manager revoke <agent> [--by human] [--reason text]")
            return
        agent = args[1]
        revoked_by = "human"
        reason = None
        if "--by" in args:
            idx = args.index("--by")
            if idx + 1 < len(args):
                revoked_by = args[idx + 1]
        if "--reason" in args:
            idx = args.index("--reason")
            if idx + 1 < len(args):
                reason = " ".join(args[idx+1:])
        if revoke_manager(agent, revoked_by=revoked_by, reason=reason):
            print(f"  ⚠️  {agent} revoked as manager")
            if reason:
                print(f"     Reason: {reason}")
        else:
            print(f"  ❌ {agent} is not the current manager")
        return

    if sub == "history":
        managers = list_managers(limit=10)
        if not managers:
            print("  No manager history")
            return
        print(f"  Manager History ({len(managers)}):")
        for mgr in managers:
            status = mgr.get('status', 'unknown')
            agent = mgr.get('agent', 'unknown')
            assigned_by = mgr.get('assigned_by', '?')
            assigned_at = mgr.get('assigned_at', '?')
            if status == 'active':
                print(f"    🟢 {agent} (current) — assigned by {assigned_by} on {assigned_at}")
            elif status == 'former':
                ended = mgr.get('ended_at', 'unknown')
                print(f"    ⚪ {agent} (former) — {assigned_at} to {ended}")
            elif status == 'revoked':
                revoked_at = mgr.get('revoked_at', '?')
                print(f"    🔴 {agent} (revoked) — {assigned_at} to {revoked_at}")
            elif status == 'expired':
                expires = mgr.get('expires_at', '?')
                print(f"    ⚪ {agent} (expired) — ended {expires}")
        return

    print(f"  Unknown manager subcommand: {sub}")


# ------------------------------------------------------------------
# Kitty Collab Protocol Commands
# ------------------------------------------------------------------

def cmd_channel(args: list):
    """
    meow channel list                → list all channels
    meow channel create <name>       → create a new channel
    meow channel post <channel> msg  → post a message to a channel
    meow channel read <channel>      → read messages from a channel
    meow channel stats <channel>     → show channel statistics
    """
    from agents.channels import (
        list_channels, create_channel, get_channel, Channel
    )
    
    if not args or args[0] in ("list", "ls"):
        channels = list_channels()
        if not channels:
            print("  No channels yet. Create one with: meow channel create <name>")
            return
        print(f"  Channels ({len(channels)}):")
        for c in channels:
            print(f"    #{c['name']:20} | {c.get('description', '')[:40]}")
        return
    
    sub = args[0]
    
    if sub == "create":
        if len(args) < 2:
            print("  Usage: meow channel create <name> [description]")
            return
        name = args[1]
        desc = " ".join(args[2:]) if len(args) > 2 else ""
        ch = create_channel(name, desc)
        print(f"  ✅ Channel #{name} created")
        return
    
    if sub == "post":
        if len(args) < 4 or args[2] != "msg":
            print("  Usage: meow channel post <channel> msg <message>")
            return
        channel_name = args[1].lstrip('#')
        message = " ".join(args[3:])
        ch = get_channel(channel_name)
        if not ch:
            print(f"  Channel #{channel_name} not found")
            return
        msg_id = ch.post(content=message, sender="human", message_type="chat")
        print(f"  ✅ Message posted (ID: {msg_id})")
        return
    
    if sub == "read":
        if len(args) < 2:
            print("  Usage: meow channel read <channel>")
            return
        channel_name = args[1].lstrip('#')
        ch = get_channel(channel_name)
        if not ch:
            print(f"  Channel #{channel_name} not found")
            return
        messages = ch.read(limit=20, reverse=True)
        if not messages:
            print(f"  No messages in #{channel_name}")
            return
        print(f"  Messages in #{channel_name}:")
        for msg in messages[:10]:
            print(f"    [{msg.get('type', 'chat')}] {msg.get('sender', 'unknown')}: {msg.get('content', '')[:60]}")
        return
    
    if sub == "stats":
        if len(args) < 2:
            print("  Usage: meow channel stats <channel>")
            return
        channel_name = args[1].lstrip('#')
        ch = get_channel(channel_name)
        if not ch:
            print(f"  Channel #{channel_name} not found")
            return
        stats = ch.get_stats()
        print(f"  Stats for #{channel_name}:")
        print(f"    Total messages: {stats['total_messages']}")
        print(f"    By type: {stats['by_type']}")
        print(f"    Top senders: {stats['by_sender']}")
        return
    
    print(f"  Unknown channel subcommand: {sub}")


def cmd_war_room(args: list):
    """
    meow war-room kick <prompt>      → start a new mission
    meow war-room approve <plan_id>  → approve a plan
    meow war-room reject <plan_id>   → reject a plan
    meow war-room pending            → list pending approvals
    meow war-room dispatch <plan_id> → dispatch approved plan
    """
    from agents.war_room import get_war_room
    
    war_room = get_war_room()
    
    if not args:
        print("  Usage: meow war-room <command> [args]")
        print("  Commands: kick, approve, reject, pending, dispatch")
        return
    
    sub = args[0]
    
    if sub == "kick":
        if len(args) < 2:
            print("  Usage: meow war-room kick <prompt>")
            return
        prompt = " ".join(args[1:])
        result = war_room.kick_off(prompt)
        print(f"  ✅ Mission kicked off!")
        print(f"     Message ID: {result['message_id']}")
        print(f"     Status: {result['status']}")
        print(f"     Post assessments with: meow war-room assess <kickoff_id> <assessment>")
        return
    
    if sub == "pending":
        pending = war_room.get_pending_approvals()
        if not pending:
            print("  No pending approvals")
            return
        print(f"  Pending approvals ({len(pending)}):")
        for p in pending:
            print(f"    {p['plan_id']}: {p['title']}")
            print(f"      Tasks: {len(p.get('tasks', []))}")
            print(f"      Created: {p.get('created_at', 'unknown')}")
        return
    
    if sub == "approve":
        if len(args) < 2:
            print("  Usage: meow war-room approve <plan_id>")
            return
        plan_id = args[1]
        if war_room.approve_plan(plan_id):
            print(f"  ✅ Plan {plan_id} approved!")
            print(f"     Dispatch with: meow war-room dispatch {plan_id}")
        else:
            print(f"  Plan {plan_id} not found")
        return
    
    if sub == "reject":
        if len(args) < 2:
            print("  Usage: meow war-room reject <plan_id> [reason]")
            return
        plan_id = args[1]
        reason = " ".join(args[2:]) if len(args) > 2 else ""
        if war_room.reject_plan(plan_id, reason=reason):
            print(f"  ❌ Plan {plan_id} rejected")
            if reason:
                print(f"     Reason: {reason}")
        else:
            print(f"  Plan {plan_id} not found")
        return
    
    if sub == "dispatch":
        if len(args) < 2:
            print("  Usage: meow war-room dispatch <plan_id>")
            return
        plan_id = args[1]
        try:
            dispatched = war_room.dispatch_tasks(plan_id)
            print(f"  ✅ Plan {plan_id} dispatched!")
            for task in dispatched:
                print(f"    → #{task['channel']}: {task['assignee']}")
        except ValueError as e:
            print(f"  ❌ {e}")
        return
    
    print(f"  Unknown war-room subcommand: {sub}")


def cmd_tokens(args: list):
    """
    meow tokens report               → show token usage report
    meow tokens set <agent> <limit>  → set daily budget for agent
    meow tokens check <agent>        → check agent budget status
    """
    from agents.context_manager import get_context_manager
    
    cm = get_context_manager()
    
    if not args or args[0] in ("report", "usage"):
        report = cm.get_usage_report(group_by="agent")
        print(f"  Token Usage Report")
        print(f"  {'='*50}")
        print(f"  Total tokens: {report['total'].get('total_tokens', 0):,}")
        print(f"  Total cost:   ${report['total'].get('total_cost_usd', 0):.2f}")
        print(f"\n  By Agent:")
        for agent, data in report.get('breakdown', {}).items():
            print(f"    {agent}:")
            print(f"      Tokens: {data.get('total_tokens', 0):,}")
            print(f"      Cost:   ${data.get('total_cost_usd', 0):.2f}")
        return
    
    if args[0] == "set":
        if len(args) < 3:
            print("  Usage: meow tokens set <agent> <daily_limit_usd>")
            return
        agent = args[1]
        limit = float(args[2])
        cm.set_budget(agent=agent, daily_limit=limit)
        print(f"  ✅ Budget set for {agent}: ${limit}/day")
        return
    
    if args[0] == "check":
        if len(args) < 2:
            print("  Usage: meow tokens check <agent>")
            return
        agent = args[1]
        status = cm.check_budget(agent)
        print(f"  Budget status for {agent}:")
        print(f"    Has budget: {status['has_budget']}")
        print(f"    Daily spent:  ${status['daily_spent']:.2f}")
        print(f"    Monthly spent: ${status['monthly_spent']:.2f}")
        if status['daily_remaining'] is not None:
            print(f"    Daily remaining: ${status['daily_remaining']:.2f}")
        return
    
    print(f"  Unknown tokens subcommand: {args[0]}")


def cmd_server(args: list):
    """
    meow server start                → start the Collab Server
    """
    if not args or args[0] in ("start", "run"):
        print("  Starting Collab Server...")
        print("  Press Ctrl+C to stop")
        print()
        from server import main as server_main
        server_main()
        return
    
    print(f"  Unknown server subcommand: {args[0]}")


HELP = """
Commands:
  meow                            → show board status
  meow mc                         → open Mission Control TUI
  meow wake                       → run wake_up (initialize board + aliases)
  meow add                        → add a task interactively
  meow spawn                      → spawn all agents
  meow spawn --agent <name>       → spawn a single agent by name
  meow spawn --list               → list configured agents
  meow task <text>                → quickly add a task
  meow task <text> --role <role>  → quick-add with role
  meow task <text> --skills a,b   → quick-add with required skills
  meow template list              → list saved task templates
  meow template save <name>       → save a new task template
  meow template use <name>        → create a task from a template
  meow template delete <name>     → delete a template

  # Agent Profiles (NEW!)
  meow profile create <n> <bio>   → create agent profile
  meow profile list               → list all profiles
  meow profile get <name>         → get profile details
  meow profile set-avatar <n> <a> → set avatar
  meow profile delete <name>      → fire agent (soft delete)
  meow profile export <n>         → export profile to JSON
  meow profile import <file>      → import profile from JSON
  meow profile avatars            → list available avatars

  # Manager Role (NEW!)
  meow manager assign <agent>     → assign manager role
  meow manager current            → who's the current manager
  meow manager handoff <new>      → manager hands off to successor
  meow manager revoke <agent>     → revoke manager
  meow manager history            → list past managers

  # Kitty Collab Protocol
  meow channel list               → list all channels
  meow channel create <name>      → create a new channel
  meow channel post <ch> msg <m>  → post message to channel
  meow channel read <channel>     → read messages from channel
  meow channel stats <channel>    → show channel statistics

  meow war-room kick <prompt>     → start a new mission
  meow war-room approve <plan>    → approve a plan
  meow war-room reject <plan>     → reject a plan
  meow war-room pending           → list pending approvals
  meow war-room dispatch <plan>   → dispatch approved plan

  meow tokens report              → show token usage report
  meow tokens set <agent> <lim>   → set daily budget
  meow tokens check <agent>       → check budget status

  meow server start               → start Collab Server (WebSocket)

  meow help                       → show this help
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
        run_spawn(extra_args=args[1:])
    elif cmd == "task" and len(args) > 1:
        # Parse optional --role, --priority, --skills flags
        rest = args[1:]
        role = None
        priority = "normal"
        skills = []
        text_parts = []
        i = 0
        while i < len(rest):
            if rest[i] == "--role" and i + 1 < len(rest):
                role = rest[i + 1]; i += 2
            elif rest[i] == "--priority" and i + 1 < len(rest):
                priority = rest[i + 1]; i += 2
            elif rest[i] == "--skills" and i + 1 < len(rest):
                skills = [s.strip() for s in rest[i + 1].split(",") if s.strip()]; i += 2
            else:
                text_parts.append(rest[i]); i += 1
        quick_task(" ".join(text_parts), role=role, priority=priority, skills=skills)
    elif cmd == "template":
        cmd_template(args[1:])
    elif cmd == "profile":
        cmd_profile(args[1:])
    elif cmd == "manager":
        cmd_manager(args[1:])
    elif cmd == "channel":
        cmd_channel(args[1:])
    elif cmd == "war-room":
        cmd_war_room(args[1:])
    elif cmd == "tokens":
        cmd_tokens(args[1:])
    elif cmd == "server":
        cmd_server(args[1:])
    elif cmd in ("help", "--help", "-h"):
        print(HELP)
    else:
        print(f"  Unknown command: {cmd}")
        print(HELP)


if __name__ == "__main__":
    main()
