"""
channels.py — Kitty Collab Board
Channel system for the Kitty Collab Protocol.

Implements file-based channels with atomic writes, sorting, and mirroring.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agents.atomic import atomic_write, atomic_read, generate_message_id, format_message_filename


# Default board directory
BOARD_DIR = Path(
    os.environ.get("CLOWDER_BOARD_DIR", Path(__file__).parent.parent / "board")
)
CHANNELS_DIR = BOARD_DIR / "channels"
ARCHIVES_DIR = BOARD_DIR / "archives"
CHANNELS_REGISTRY = BOARD_DIR / ".channels.json"


class Channel:
    """
    A communication channel in the Kitty Collab Protocol.
    
    Each channel is a directory containing JSON message files.
    Messages are atomically written and can be sorted by various fields.
    """
    
    VALID_MESSAGE_TYPES = {"chat", "update", "alert", "task", "code", "approval", "plan"}
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a channel.
        
        Args:
            name: Channel name (e.g., "war-room", "team-claude")
            description: Human-readable description
        """
        self.name = name.lstrip('#')  # Remove # prefix if present
        self.description = description
        self.path = CHANNELS_DIR / self.name
        
    def create(self) -> "Channel":
        """Create the channel directory and register it."""
        self.path.mkdir(parents=True, exist_ok=True)
        self._register()
        return self
    
    def _register(self) -> None:
        """Register this channel in the central registry."""
        registry = atomic_read(CHANNELS_REGISTRY, {"channels": {}})
        
        registry["channels"][self.name] = {
            "name": self.name,
            "description": self.description,
            "created_at": datetime.now().isoformat(),
        }
        
        atomic_write(CHANNELS_REGISTRY, registry)
    
    def post(
        self,
        content: str,
        sender: str,
        message_type: str = "chat",
        thread_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Post a message to this channel.
        
        Args:
            content: Message content
            sender: Agent/user name (e.g., "claude-code", "human")
            message_type: One of chat, update, alert, task, code, approval, plan
            thread_id: Optional thread ID for replies
            metadata: Optional additional metadata
            
        Returns:
            Message ID
        """
        if message_type not in self.VALID_MESSAGE_TYPES:
            raise ValueError(
                f"Invalid message type: {message_type}. "
                f"Must be one of: {self.VALID_MESSAGE_TYPES}"
            )
        
        timestamp = datetime.now().isoformat()
        message_id = generate_message_id()
        
        message = {
            "id": message_id,
            "sender": sender,
            "channel": self.name,
            "content": content,
            "timestamp": timestamp,
            "thread_id": thread_id,
            "type": message_type,
        }
        
        if metadata:
            message["metadata"] = metadata
        
        # Write atomically
        filename = format_message_filename(timestamp, sender, message_id)
        atomic_write(self.path / filename, message)
        
        return message_id
    
    def read(
        self,
        sort_by: str = "timestamp",
        reverse: bool = False,
        limit: Optional[int] = None,
        message_type: Optional[str] = None,
        sender: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Read messages from this channel.
        
        Args:
            sort_by: Field to sort by (timestamp, sender, type)
            reverse: Reverse sort order
            limit: Maximum number of messages to return
            message_type: Filter by message type
            sender: Filter by sender
            thread_id: Filter by thread ID
            
        Returns:
            List of message dicts
        """
        if not self.path.exists():
            return []
        
        messages = []
        
        for filepath in self.path.glob("*.json"):
            # Skip temp files
            if filepath.suffix == ".tmp":
                continue
            
            message = atomic_read(filepath)
            if message is None:
                continue
            
            # Apply filters
            if message_type and message.get("type") != message_type:
                continue
            if sender and message.get("sender") != sender:
                continue
            if thread_id and message.get("thread_id") != thread_id:
                continue
            
            messages.append(message)
        
        # Sort
        if sort_by in ("timestamp", "sender", "type", "id"):
            messages.sort(key=lambda m: m.get(sort_by, ""), reverse=reverse)
        
        # Limit
        if limit:
            messages = messages[:limit]
        
        return messages
    
    def get_threads(self) -> list[dict]:
        """
        Get all thread roots (messages without thread_id).
        
        Returns:
            List of thread root messages with reply count
        """
        roots = self.read(thread_id=None)
        
        for root in roots:
            # Count replies
            replies = self.read(thread_id=root["id"])
            root["reply_count"] = len(replies)
        
        return roots
    
    def get_thread(self, thread_id: str) -> list[dict]:
        """
        Get all messages in a thread.
        
        Args:
            thread_id: ID of the thread root
            
        Returns:
            List of messages in the thread (including root)
        """
        # Get root
        root = None
        for msg in self.read():
            if msg["id"] == thread_id:
                root = msg
                break
        
        if not root:
            return []
        
        # Get replies
        replies = self.read(thread_id=thread_id)
        
        return [root] + replies
    
    def mirror_to(self, target: "Channel", filter_fn: Optional[callable] = None) -> int:
        """
        Mirror messages from this channel to another channel.
        
        Args:
            target: Target channel to mirror to
            filter_fn: Optional function to filter messages (msg) -> bool
            
        Returns:
            Number of messages mirrored
        """
        messages = self.read()
        mirrored = 0
        
        for msg in messages:
            if filter_fn and not filter_fn(msg):
                continue
            
            # Add mirror metadata
            if "metadata" not in msg:
                msg["metadata"] = {}
            msg["metadata"]["mirrored_from"] = self.name
            msg["metadata"]["mirrored_at"] = datetime.now().isoformat()
            
            # Post to target (new ID, same content)
            target.post(
                content=msg["content"],
                sender=msg["sender"],
                message_type=msg["type"],
                metadata=msg.get("metadata", {}),
            )
            mirrored += 1
        
        return mirrored
    
    def archive(self, max_messages: int = 1000) -> Optional[Path]:
        """
        Archive old messages to reduce channel size.
        
        Keeps the most recent max_messages, archives the rest.
        
        Args:
            max_messages: Number of recent messages to keep
            
        Returns:
            Path to archive file, or None if no archiving needed
        """
        messages = self.read(sort_by="timestamp", reverse=True)
        
        if len(messages) <= max_messages:
            return None
        
        # Messages to archive (oldest)
        to_archive = messages[max_messages:]
        
        # Create archive
        archive_data = {
            "channel": self.name,
            "archived_at": datetime.now().isoformat(),
            "message_count": len(to_archive),
            "messages": to_archive,
        }
        
        # Write archive
        ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
        archive_path = ARCHIVES_DIR / f"{self.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json.gz"
        
        import gzip
        with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2)
        
        # Delete archived messages
        for msg in to_archive:
            timestamp = msg["timestamp"].replace(':', '-')
            filename = f"{timestamp}-{msg['sender']}-{msg['id']}.json"
            filepath = self.path / filename
            if filepath.exists():
                filepath.unlink()
        
        return archive_path
    
    def delete(self) -> None:
        """Delete this channel and unregister it."""
        import shutil
        if self.path.exists():
            shutil.rmtree(self.path)
        
        # Unregister
        registry = atomic_read(CHANNELS_REGISTRY, {"channels": {}})
        if self.name in registry.get("channels", {}):
            del registry["channels"][self.name]
            atomic_write(CHANNELS_REGISTRY, registry)
    
    def get_stats(self) -> dict:
        """Get channel statistics."""
        messages = self.read()
        
        # Count by type
        by_type = {}
        by_sender = {}
        
        for msg in messages:
            msg_type = msg.get("type", "unknown")
            sender = msg.get("sender", "unknown")
            
            by_type[msg_type] = by_type.get(msg_type, 0) + 1
            by_sender[sender] = by_sender.get(sender, 0) + 1
        
        return {
            "name": self.name,
            "total_messages": len(messages),
            "by_type": by_type,
            "by_sender": by_sender,
        }


class ChannelManager:
    """
    Manager for all channels in the Kitty Collab Board.
    """
    
    def __init__(self):
        self._channels: dict[str, Channel] = {}
    
    def get_channel(self, name: str) -> Optional[Channel]:
        """Get a channel by name."""
        name = name.lstrip('#')
        
        if name not in self._channels:
            # Check if channel exists on disk
            channel_path = CHANNELS_DIR / name
            if channel_path.exists():
                # Load from registry
                registry = atomic_read(CHANNELS_REGISTRY, {"channels": {}})
                desc = ""
                if name in registry.get("channels", {}):
                    desc = registry["channels"][name].get("description", "")
                
                self._channels[name] = Channel(name, desc)
            else:
                return None
        
        return self._channels.get(name)
    
    def create_channel(self, name: str, description: str = "") -> Channel:
        """Create a new channel."""
        name = name.lstrip('#')
        channel = Channel(name, description)
        channel.create()
        self._channels[name] = channel
        return channel
    
    def list_channels(self) -> list[dict]:
        """List all registered channels."""
        registry = atomic_read(CHANNELS_REGISTRY, {"channels": {}})
        return list(registry.get("channels", {}).values())
    
    def get_or_create(self, name: str, description: str = "") -> Channel:
        """Get existing channel or create new one."""
        channel = self.get_channel(name)
        if channel:
            return channel
        return self.create_channel(name, description)
    
    def delete_channel(self, name: str) -> bool:
        """Delete a channel."""
        channel = self.get_channel(name)
        if not channel:
            return False
        
        channel.delete()
        del self._channels[name]
        return True


# Global channel manager instance
_channel_manager: Optional[ChannelManager] = None


def get_channel_manager() -> ChannelManager:
    """Get the global channel manager instance."""
    global _channel_manager
    if _channel_manager is None:
        _channel_manager = ChannelManager()
    return _channel_manager


def get_channel(name: str) -> Optional[Channel]:
    """Get a channel by name."""
    return get_channel_manager().get_channel(name)


def create_channel(name: str, description: str = "") -> Channel:
    """Create a new channel."""
    return get_channel_manager().create_channel(name, description)


def get_or_create_channel(name: str, description: str = "") -> Channel:
    """Get existing channel or create new one."""
    return get_channel_manager().get_or_create(name, description)


def list_channels() -> list[dict]:
    """List all registered channels."""
    return get_channel_manager().list_channels()
