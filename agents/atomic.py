"""
atomic.py — Kitty Collab Board
Atomic write utilities for lock-free concurrency.

Uses atomic rename(2) syscall for thread-safe writes without locks.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write(path: Path, data: Any) -> None:
    """
    Write data to a file atomically using rename(2).
    
    This is safe for concurrent access - readers always see complete files,
    never partial writes.
    
    Args:
        path: Target file path
        data: Data to write (will be JSON-encoded if dict/list)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temp file first
    fd, tmp_path = tempfile.mkstemp(
        suffix=".tmp",
        prefix=".atomic_",
        dir=path.parent
    )
    
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f, indent=2)
            else:
                f.write(str(data))
        
        # Atomic rename - this is the key operation
        # On POSIX systems, rename() is atomic
        os.replace(tmp_path, str(path))
    except Exception:
        # Clean up temp file on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_read(path: Path, default: Any = None) -> Any:
    """
    Read JSON file with atomic semantics.
    
    Args:
        path: File to read
        default: Default value if file doesn't exist
        
    Returns:
        Parsed JSON data or default
    """
    if not path.exists():
        return default
    
    try:
        content = path.read_text(encoding='utf-8')
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return default


def generate_message_id() -> str:
    """Generate a unique message ID."""
    import uuid
    return uuid.uuid4().hex[:8]


def format_message_filename(timestamp: str, sender: str, message_id: str) -> str:
    """
    Format a message filename according to the Kitty Collab Protocol.
    
    Format: {timestamp}-{sender}-{id}.json
    Timestamp colons are replaced with dashes for filesystem compatibility.
    
    Args:
        timestamp: ISO format timestamp
        sender: Agent/user name
        message_id: Unique message ID
        
    Returns:
        Filename string
    """
    # Replace colons in timestamp for filesystem compatibility
    safe_timestamp = timestamp.replace(':', '-')
    return f"{safe_timestamp}-{sender}-{message_id}.json"


def parse_message_filename(filename: str) -> dict | None:
    """
    Parse a message filename back into components.
    
    Args:
        filename: Filename to parse
        
    Returns:
        Dict with timestamp, sender, id or None if invalid
    """
    if not filename.endswith('.json'):
        return None
    
    parts = filename[:-5].split('-')  # Remove .json, split by -
    
    if len(parts) < 3:
        return None
    
    # Timestamp might have multiple dashes (date + time)
    # Format: YYYY-MM-DDTHH-MM-SS.microseconds-sender-id
    # We need to reconstruct the timestamp
    
    # Find sender and id (last two parts)
    message_id = parts[-1]
    sender = parts[-2]
    
    # Everything before sender is the timestamp
    timestamp_parts = parts[:-2]
    timestamp = '-'.join(timestamp_parts).replace('-', ':', 3)  # Only replace first 3 dashes
    
    # Restore microseconds separator
    if '.' in timestamp:
        timestamp = timestamp.replace('.', ':', 1).replace(':', '.', 1)
    
    return {
        'timestamp': timestamp,
        'sender': sender,
        'id': message_id
    }
