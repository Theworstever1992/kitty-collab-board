"""
profiles.py — Kitty Collab Board
Agent profiles with cat avatars.

Each agent has: name, bio, skills, avatar, personality, stats
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

from agents.atomic import atomic_write, atomic_read

# Default board directory
BOARD_DIR = Path(__file__).parent.parent / "board"
PROFILES_FILE = BOARD_DIR / "profiles.json"
AVATARS_DIR = Path(__file__).parent.parent / "backend" / "assets" / "avatars"

# Default avatars
DEFAULT_AVATARS = ["tabby.svg", "tuxedo.svg", "calico.svg"]


class ProfileManager:
    """Manage agent profiles."""

    def __init__(self):
        PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)

    def create_profile(
        self,
        name: str,
        bio: str,
        role: str = "general",
        skills: list = None,
        avatar: str = None,
        personality_seed: str = None,
        team: str = None,
    ) -> dict:
        """
        Create a new agent profile.

        Args:
            name: Agent name (unique)
            bio: Short bio/description
            role: Agent role (e.g., "code_reviewer", "developer")
            skills: List of skills (e.g., ["python", "react"])
            avatar: Avatar filename (default: random from templates)
            personality_seed: Personality description for LLM prompts
            team: Team affiliation (e.g., "team-qwen")

        Returns:
            Profile dict
        """
        profiles = self._load_profiles()

        if name in profiles.get("agents", {}):
            raise ValueError(f"Agent '{name}' already exists")

        if avatar is None:
            avatar = random.choice(DEFAULT_AVATARS)

        if personality_seed is None:
            personality_seed = self._generate_personality(role)

        profile = {
            "name": name,
            "bio": bio,
            "role": role,
            "skills": skills or [],
            "avatar": avatar,
            "personality_seed": personality_seed,
            "team": team,
            "status": "active",
            "hired_at": datetime.now().isoformat(),
            "fired_at": None,
            "fire_reason": None,
            "stats": {
                "tasks_completed": 0,
                "messages_posted": 0,
                "total_reactions": 0,
                "violations": 0,
            },
        }

        if "agents" not in profiles:
            profiles["agents"] = {}

        profiles["agents"][name] = profile
        atomic_write(PROFILES_FILE, profiles)

        return profile

    def get_profile(self, name: str) -> Optional[dict]:
        """Get profile by name."""
        profiles = self._load_profiles()
        return profiles.get("agents", {}).get(name)

    def update_profile(self, name: str, updates: dict) -> Optional[dict]:
        """Update profile fields."""
        profiles = self._load_profiles()

        if name not in profiles.get("agents", {}):
            return None

        profile = profiles["agents"][name]
        profile.update(updates)
        profile["updated_at"] = datetime.now().isoformat()

        atomic_write(PROFILES_FILE, profiles)
        return profile

    def list_profiles(self, team: str = None, status: str = "active") -> list:
        """List all profiles, optionally filtered."""
        profiles = self._load_profiles()
        agents = profiles.get("agents", {})

        result = []
        for name, profile in agents.items():
            if team and profile.get("team") != team:
                continue
            if status and profile.get("status") != status:
                continue
            result.append(profile)

        return result

    def delete_profile(self, name: str) -> bool:
        """Soft-delete a profile (mark as fired)."""
        profiles = self._load_profiles()

        if name not in profiles.get("agents", {}):
            return False

        profile = profiles["agents"][name]
        profile["status"] = "fired"
        profile["fired_at"] = datetime.now().isoformat()

        atomic_write(PROFILES_FILE, profiles)
        return True

    def hard_delete_profile(self, name: str) -> bool:
        """Completely remove a profile."""
        profiles = self._load_profiles()

        if name not in profiles.get("agents", {}):
            return False

        del profiles["agents"][name]
        atomic_write(PROFILES_FILE, profiles)
        return True

    def update_stats(self, name: str, stat_updates: dict) -> Optional[dict]:
        """Update agent statistics."""
        profiles = self._load_profiles()

        if name not in profiles.get("agents", {}):
            return None

        profile = profiles["agents"][name]
        if "stats" not in profile:
            profile["stats"] = {}

        for key, value in stat_updates.items():
            if key in profile["stats"]:
                profile["stats"][key] += value
            else:
                profile["stats"][key] = value

        atomic_write(PROFILES_FILE, profiles)
        return profile

    def get_avatar_svg(self, avatar_name: str) -> Optional[str]:
        """Get SVG content for an avatar."""
        avatar_path = AVATARS_DIR / avatar_name
        if not avatar_path.exists():
            return None
        return avatar_path.read_text(encoding="utf-8")

    def list_avatars(self) -> list:
        """List available avatar templates."""
        if not AVATARS_DIR.exists():
            return []
        return [f.stem for f in AVATARS_DIR.glob("*.svg")]

    def _load_profiles(self) -> dict:
        """Load profiles from file."""
        return atomic_read(PROFILES_FILE, {"agents": {}})

    def _generate_personality(self, role: str) -> str:
        """Generate a default personality seed based on role."""
        personalities = {
            "code_reviewer": "You are meticulous and detail-oriented. You take pride in catching subtle bugs and ensuring code quality. You are direct but constructive in feedback.",
            "developer": "You are creative and solution-focused. You enjoy building elegant systems and writing clean, maintainable code. You collaborate well with others.",
            "tester": "You are thorough and systematic. You think of edge cases others miss. You believe quality is everyone's responsibility.",
            "manager": "You are organized and communicative. You keep the team aligned and remove blockers. You balance technical and people concerns.",
            "general": "You are helpful and eager to contribute. You adapt to the team's needs and communicate clearly.",
        }
        return personalities.get(role, personalities["general"])


# Global profile manager instance
_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    """Get the global profile manager instance."""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


# Convenience functions
def create_profile(name: str, bio: str, **kwargs) -> dict:
    """Create a new agent profile."""
    return get_profile_manager().create_profile(name, bio, **kwargs)


def get_profile(name: str) -> Optional[dict]:
    """Get profile by name."""
    return get_profile_manager().get_profile(name)


def list_profiles(**kwargs) -> list:
    """List all profiles."""
    return get_profile_manager().list_profiles(**kwargs)


def update_profile(name: str, updates: dict) -> Optional[dict]:
    """Update profile fields."""
    return get_profile_manager().update_profile(name, updates)


def delete_profile(name: str) -> bool:
    """Soft-delete a profile."""
    return get_profile_manager().delete_profile(name)


def get_avatar_svg(avatar_name: str) -> Optional[str]:
    """Get SVG content for an avatar."""
    return get_profile_manager().get_avatar_svg(avatar_name)
