"""
manager.py — Kitty Collab Board
Manager role assignment and handoff system.

Features:
- Assign manager role to any agent
- Manager announces authority to all channels
- Clear handoff protocol (outgoing → incoming)
- Everyone sees who's in charge
- Daily/weekly rotation support
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from agents.atomic import atomic_write, atomic_read
from agents.channels import get_channel, get_or_create_channel

# Default board directory
BOARD_DIR = Path(__file__).parent.parent / "board"
MANAGER_FILE = BOARD_DIR / ".manager.json"


class ManagerRegistry:
    """Track current and historical managers."""

    def __init__(self):
        MANAGER_FILE.parent.mkdir(parents=True, exist_ok=True)

    def assign_manager(
        self,
        agent_name: str,
        assigned_by: str = "human",
        duration: str = "indefinite",
        scope: str = "all",
        reason: str = None,
    ) -> dict:
        """
        Assign manager role to an agent.

        Args:
            agent_name: Agent to make manager
            assigned_by: Who is assigning (usually "human")
            duration: "indefinite", "1day", "1week", "until <date>"
            scope: "all", "team-qwen", "phase-1", etc.
            reason: Optional reason for assignment

        Returns:
            Manager assignment record
        """
        registry = self._load_registry()

        # End previous manager's term if exists
        if registry.get("current"):
            registry["current"]["ended_at"] = datetime.now().isoformat()
            registry["current"]["status"] = "former"
            registry["history"].append(registry["current"])

        # Create new manager record
        expires_at = self._calculate_expiry(duration)

        manager_record = {
            "agent": agent_name,
            "assigned_by": assigned_by,
            "assigned_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "duration": duration,
            "scope": scope,
            "reason": reason,
            "status": "active",
            "authority": [
                "assign_tasks",
                "approve_plans",
                "delegate_to_leaders",
                "report_to_human",
                "fire_agents",  # With human approval
            ],
        }

        registry["current"] = manager_record
        atomic_write(MANAGER_FILE, registry)

        # Announce to all channels
        self._announce_assignment(manager_record)

        return manager_record

    def handoff_manager(
        self,
        outgoing_manager: str,
        incoming_manager: str,
        handoff_notes: str = None,
    ) -> dict:
        """
        Manager hands off to successor.

        Args:
            outgoing_manager: Current manager
            incoming_manager: New manager
            handoff_notes: Transition notes

        Returns:
            Handoff record
        """
        registry = self._load_registry()

        # Verify outgoing is current manager
        if not registry.get("current") or registry["current"]["agent"] != outgoing_manager:
            raise ValueError(f"{outgoing_manager} is not the current manager")

        # End outgoing term
        registry["current"]["ended_at"] = datetime.now().isoformat()
        registry["current"]["status"] = "former"
        registry["current"]["handoff_to"] = incoming_manager
        registry["history"].append(registry["current"])

        # Create new manager record
        manager_record = {
            "agent": incoming_manager,
            "assigned_by": outgoing_manager,  # Handoff, not human assignment
            "assigned_at": datetime.now().isoformat(),
            "expires_at": None,  # Inherits original expiry or indefinite
            "duration": "indefinite",
            "scope": registry["current"].get("scope", "all"),
            "reason": f"Handoff from {outgoing_manager}",
            "handoff_notes": handoff_notes,
            "status": "active",
            "authority": registry["current"].get("authority", []),
        }

        registry["current"] = manager_record
        atomic_write(MANAGER_FILE, registry)

        # Announce handoff
        self._announce_handoff(outgoing_manager, incoming_manager, handoff_notes)

        return manager_record

    def get_current_manager(self) -> Optional[dict]:
        """Get current manager record."""
        registry = self._load_registry()
        current = registry.get("current")

        if not current:
            return None

        # Check if expired
        if current.get("expires_at"):
            expiry = datetime.fromisoformat(current["expires_at"])
            if datetime.now() > expiry:
                # Auto-expire
                current["status"] = "expired"
                registry["history"].append(current)
                registry["current"] = None
                atomic_write(MANAGER_FILE, registry)
                return None

        return current

    def list_managers(self, limit: int = 10) -> list:
        """List recent managers (current + history)."""
        registry = self._load_registry()
        result = []

        if registry.get("current"):
            result.append(registry["current"])

        # Add recent history
        history = registry.get("history", [])
        result.extend(history[-limit+1:] if len(history) > limit-1 else history)

        return result

    def revoke_manager(self, agent_name: str, revoked_by: str = "human", reason: str = None) -> bool:
        """Revoke manager role."""
        registry = self._load_registry()

        if not registry.get("current") or registry["current"]["agent"] != agent_name:
            return False

        registry["current"]["status"] = "revoked"
        registry["current"]["revoked_by"] = revoked_by
        registry["current"]["revoked_at"] = datetime.now().isoformat()
        registry["current"]["revoke_reason"] = reason
        registry["history"].append(registry["current"])
        registry["current"] = None

        atomic_write(MANAGER_FILE, registry)

        # Announce revocation
        self._announce_revocation(agent_name, revoked_by, reason)

        return True

    def _load_registry(self) -> dict:
        """Load manager registry."""
        return atomic_read(MANAGER_FILE, {"current": None, "history": []})

    def _calculate_expiry(self, duration: str) -> Optional[str]:
        """Calculate expiry timestamp from duration string."""
        from datetime import timedelta

        if duration == "indefinite":
            return None

        now = datetime.now()

        if duration == "1day":
            expiry = now + timedelta(days=1)
        elif duration == "1week":
            expiry = now + timedelta(days=7)
        elif duration.startswith("until "):
            # Parse date: "until 2026-03-15"
            date_str = duration.replace("until ", "").strip()
            try:
                expiry = datetime.fromisoformat(date_str)
            except ValueError:
                expiry = now + timedelta(days=1)  # Default to 1 day
        else:
            expiry = now + timedelta(days=1)  # Default

        return expiry.isoformat()

    def _announce_assignment(self, manager_record: dict):
        """Announce manager assignment to all channels."""
        agent = manager_record["agent"]
        assigned_by = manager_record["assigned_by"]
        scope = manager_record.get("scope", "all")
        reason = manager_record.get("reason", "")

        # Announcement message
        message = f"""🔔 **Manager Assignment**

**Manager:** {agent}
**Assigned by:** {assigned_by}
**Scope:** {scope}
**Duration:** {manager_record.get('duration', 'indefinite')}
{f'**Reason:** {reason}' if reason else ''}

**Authority:**
- Assign tasks to all agents
- Approve/reject plans
- Delegate to team leaders
- Report directly to human
- Fire agents (with human approval)

All teams: Please coordinate with @{agent} and follow their direction.
"""

        # Post to assembly (main announcement channel)
        assembly = get_or_create_channel("assembly")
        assembly.post(
            content=message,
            sender="system",
            message_type="alert",
        )

        # Post to manager channel
        manager_ch = get_or_create_channel("manager")
        manager_ch.post(
            content=f"🟢 **{agent}** assumes manager role. Assigned by {assigned_by}.",
            sender="system",
            message_type="update",
        )

        # Post to war-room
        war_room = get_or_create_channel("war-room")
        war_room.post(
            content=f"🔔 **Management Change:** @{agent} is now manager. Scope: {scope}.",
            sender="system",
            message_type="alert",
        )

    def _announce_handoff(self, outgoing: str, incoming: str, notes: str = None):
        """Announce manager handoff."""
        message = f"""🔄 **Manager Handoff**

**Outgoing:** {outgoing}
**Incoming:** {incoming}
{f'**Notes:** {notes}' if notes else ''}

{outgoing} is stepping down. {incoming} now has full managerial authority.

All teams: Please coordinate with @{incoming} going forward.
"""

        assembly = get_or_create_channel("assembly")
        assembly.post(
            content=message,
            sender="system",
            message_type="alert",
        )

        manager_ch = get_or_create_channel("manager")
        manager_ch.post(
            content=f"🔄 Handoff: {outgoing} → {incoming}",
            sender="system",
            message_type="update",
        )

    def _announce_revocation(self, agent: str, revoked_by: str, reason: str = None):
        """Announce manager revocation."""
        message = f"""⚠️ **Manager Revoked**

**Manager:** {agent}
**Revoked by:** {revoked_by}
{f'**Reason:** {reason}' if reason else ''}

{agent} no longer has managerial authority. A new manager will be assigned shortly.
"""

        assembly = get_or_create_channel("assembly")
        assembly.post(
            content=message,
            sender="system",
            message_type="alert",
        )


# Global registry instance
_manager_registry: Optional[ManagerRegistry] = None


def get_manager_registry() -> ManagerRegistry:
    """Get global manager registry."""
    global _manager_registry
    if _manager_registry is None:
        _manager_registry = ManagerRegistry()
    return _manager_registry


# Convenience functions
def assign_manager(agent: str, **kwargs) -> dict:
    """Assign manager role."""
    return get_manager_registry().assign_manager(agent, **kwargs)


def handoff_manager(outgoing: str, incoming: str, notes: str = None) -> dict:
    """Handoff manager role."""
    return get_manager_registry().handoff_manager(outgoing, incoming, notes)


def get_current_manager() -> Optional[dict]:
    """Get current manager."""
    return get_manager_registry().get_current_manager()


def list_managers(limit: int = 10) -> list:
    """List recent managers."""
    return get_manager_registry().list_managers(limit)


def revoke_manager(agent: str, **kwargs) -> bool:
    """Revoke manager role."""
    return get_manager_registry().revoke_manager(agent, **kwargs)
