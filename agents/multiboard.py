"""
multiboard.py — Kitty Collab Board
Multi-board support for task isolation and switching.

Allows running multiple independent task boards (e.g., per project, team, or environment).
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

try:
    from filelock import FileLock
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False


BASE_DIR = Path(os.environ.get("CLOWDER_BASE_DIR", Path(__file__).parent.parent))
BOARDS_DIR = BASE_DIR / "boards"
CONFIG_FILE = BOARDS_DIR / "boards.json"


class _NoOpLock:
    """Fallback context manager when filelock is not installed."""
    def __enter__(self): return self
    def __exit__(self, *_): pass


def _lock(file_path: Path):
    """Return a FileLock for the given path, or a no-op context if unavailable."""
    if FILELOCK_AVAILABLE:
        return FileLock(str(file_path) + ".lock", timeout=10)
    return _NoOpLock()


@dataclass
class BoardInfo:
    """Information about a task board."""
    name: str
    description: str
    board_dir: str
    created_at: str
    last_accessed: str
    task_count: int = 0
    is_active: bool = False


class MultiBoardManager:
    """
    Manages multiple independent task boards.

    Each board has its own:
    - board.json (tasks)
    - agents.json (agent registry)
    - audit.json (audit log)
    - metrics.json (metrics)
    """

    def __init__(self, boards_dir: Optional[Path] = None):
        self.boards_dir = Path(boards_dir) if boards_dir else BOARDS_DIR
        self.config_file = self.boards_dir / "boards.json"
        self.boards_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> Dict:
        """Load board registry."""
        if not self.config_file.exists():
            return {"boards": {}, "active_board": "default"}
        try:
            with _lock(self.config_file):
                content = self.config_file.read_text(encoding="utf-8")
                if not content.strip():
                    return {"boards": {}, "active_board": "default"}
                return json.loads(content)
        except (json.JSONDecodeError, Exception):
            return {"boards": {}, "active_board": "default"}

    def _save_config(self, data: Dict):
        """Save board registry atomically."""
        with _lock(self.config_file):
            self.config_file.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8"
            )

    def create_board(self, name: str, description: str = "") -> str:
        """
        Create a new task board.

        Args:
            name: Board name (alphanumeric, underscores/hyphens)
            description: Optional description

        Returns:
            Board name if successful

        Raises:
            ValueError: If board already exists
        """
        # Validate name
        if not name or not name.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Board name must be alphanumeric with underscores/hyphens")

        data = self._load_config()

        if name in data["boards"]:
            raise ValueError(f"Board '{name}' already exists")

        board_dir = self.boards_dir / name
        board_dir.mkdir(parents=True, exist_ok=True)

        # Initialize board files
        board_file = board_dir / "board.json"
        agents_file = board_dir / "agents.json"
        audit_file = board_dir / "audit.json"
        metrics_file = board_dir / "metrics.json"

        board_file.write_text(json.dumps({"tasks": []}, indent=2), encoding="utf-8")
        agents_file.write_text(json.dumps({}, indent=2), encoding="utf-8")
        audit_file.write_text(json.dumps([], indent=2), encoding="utf-8")
        metrics_file.write_text(json.dumps({"tasks": {}, "agents": {}, "snapshots": []}, indent=2), encoding="utf-8")

        now = datetime.now().isoformat()
        data["boards"][name] = {
            "name": name,
            "description": description,
            "board_dir": str(board_dir),
            "created_at": now,
            "last_accessed": now,
            "task_count": 0,
            "is_active": False,
        }

        self._save_config(data)
        return name

    def get_board(self, name: str) -> Optional[BoardInfo]:
        """Get information about a board."""
        data = self._load_config()
        board_data = data["boards"].get(name)
        if not board_data:
            return None

        # Update task count
        board_path = Path(board_data["board_dir"])
        board_file = board_path / "board.json"
        task_count = 0
        if board_file.exists():
            try:
                board = json.loads(board_file.read_text(encoding="utf-8"))
                task_count = len(board.get("tasks", []))
            except Exception:
                pass

        return BoardInfo(
            name=board_data["name"],
            description=board_data.get("description", ""),
            board_dir=board_data["board_dir"],
            created_at=board_data.get("created_at"),
            last_accessed=board_data.get("last_accessed"),
            task_count=task_count,
            is_active=board_data.get("is_active", False),
        )

    def list_boards(self) -> List[BoardInfo]:
        """List all boards."""
        data = self._load_config()
        boards = []

        for name, board_data in data["boards"].items():
            board_path = Path(board_data["board_dir"])
            board_file = board_path / "board.json"
            task_count = 0
            if board_file.exists():
                try:
                    board = json.loads(board_file.read_text(encoding="utf-8"))
                    task_count = len(board.get("tasks", []))
                except Exception:
                    pass

            boards.append(BoardInfo(
                name=board_data["name"],
                description=board_data.get("description", ""),
                board_dir=board_data["board_dir"],
                created_at=board_data.get("created_at"),
                last_accessed=board_data.get("last_accessed"),
                task_count=task_count,
                is_active=board_data.get("is_active", False),
            ))

        return boards

    def delete_board(self, name: str) -> bool:
        """
        Delete a board and all its data.

        Args:
            name: Board name to delete

        Returns:
            True if deleted, False if board doesn't exist
        """
        data = self._load_config()

        if name not in data["boards"]:
            return False

        # Don't delete active board
        if data["boards"][name].get("is_active"):
            raise ValueError("Cannot delete active board. Switch to another board first.")

        board_dir = Path(data["boards"][name]["board_dir"])

        # Remove board files
        for f in ["board.json", "agents.json", "audit.json", "metrics.json"]:
            board_file = board_dir / f
            if board_file.exists():
                board_file.unlink()

        # Remove directory if empty
        try:
            board_dir.rmdir()
        except OSError:
            pass  # Directory not empty, leave it

        del data["boards"][name]
        self._save_config(data)
        return True

    def switch_board(self, name: str) -> bool:
        """
        Switch the active board.

        Args:
            name: Board name to switch to

        Returns:
            True if successful

        Raises:
            ValueError: If board doesn't exist
        """
        data = self._load_config()

        if name not in data["boards"]:
            raise ValueError(f"Board '{name}' does not exist")

        # Deactivate current active board
        for board_name in data["boards"]:
            data["boards"][board_name]["is_active"] = False

        # Activate new board
        data["boards"][name]["is_active"] = True
        data["boards"][name]["last_accessed"] = datetime.now().isoformat()
        data["active_board"] = name

        self._save_config(data)
        return True

    def get_active_board(self) -> Optional[BoardInfo]:
        """Get the currently active board."""
        data = self._load_config()
        active_name = data.get("active_board", "default")
        return self.get_board(active_name)

    def get_active_board_path(self) -> Path:
        """Get the path to the active board directory."""
        board = self.get_active_board()
        if board:
            return Path(board.board_dir)
        # Default to original location
        return BASE_DIR / "board"

    def get_board_path(self, name: str) -> Optional[Path]:
        """Get the path to a specific board directory."""
        board = self.get_board(name)
        if board:
            return Path(board.board_dir)
        return None

    def export_board(self, name: str, output_path: Path) -> Optional[Path]:
        """
        Export a board's data to a single JSON file.

        Args:
            name: Board name to export
            output_path: Path to save export

        Returns:
            Path to exported file
        """
        board = self.get_board(name)
        if not board:
            return None

        board_dir = Path(board.board_dir)
        export_data = {
            "board_name": name,
            "description": board.description,
            "exported_at": datetime.now().isoformat(),
            "tasks": [],
            "agents": {},
            "audit_log": [],
            "metrics": {},
        }

        # Load all board data
        for filename, key in [
            ("board.json", "tasks"),
            ("agents.json", "agents"),
            ("audit.json", "audit_log"),
            ("metrics.json", "metrics"),
        ]:
            file_path = board_dir / filename
            if file_path.exists():
                try:
                    data = json.loads(file_path.read_text(encoding="utf-8"))
                    if key == "tasks":
                        export_data["tasks"] = data.get("tasks", [])
                    else:
                        export_data[key] = data
                except Exception:
                    pass

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        return output_path

    def import_board(self, export_path: Path, name: Optional[str] = None) -> Optional[str]:
        """
        Import a board from an export file.

        Args:
            export_path: Path to export file
            name: Optional new name for the board

        Returns:
            Name of imported board
        """
        if not export_path.exists():
            return None

        try:
            export_data = json.loads(export_path.read_text(encoding="utf-8"))
        except Exception:
            return None

        board_name = name or export_data.get("board_name", f"imported_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        description = export_data.get("description", "")

        # Create new board
        try:
            self.create_board(board_name, description)
        except ValueError:
            # Board exists, generate unique name
            board_name = f"{board_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.create_board(board_name, description)

        board = self.get_board(board_name)
        if not board:
            return None

        board_dir = Path(board.board_dir)

        # Write imported data
        if "tasks" in export_data:
            board_file = board_dir / "board.json"
            board_file.write_text(
                json.dumps({"tasks": export_data["tasks"]}, indent=2),
                encoding="utf-8"
            )

        if "agents" in export_data:
            agents_file = board_dir / "agents.json"
            agents_file.write_text(
                json.dumps(export_data["agents"], indent=2),
                encoding="utf-8"
            )

        if "audit_log" in export_data:
            audit_file = board_dir / "audit.json"
            audit_file.write_text(
                json.dumps(export_data["audit_log"], indent=2),
                encoding="utf-8"
            )

        if "metrics" in export_data:
            metrics_file = board_dir / "metrics.json"
            metrics_file.write_text(
                json.dumps(export_data["metrics"], indent=2),
                encoding="utf-8"
            )

        return board_name


# Global manager instance
_manager: Optional[MultiBoardManager] = None


def get_multiboard_manager() -> MultiBoardManager:
    """Get the global multi-board manager instance."""
    global _manager
    if _manager is None:
        _manager = MultiBoardManager()
    return _manager


# Convenience functions
def create_board(name: str, description: str = "") -> str:
    return get_multiboard_manager().create_board(name, description)


def switch_board(name: str) -> bool:
    return get_multiboard_manager().switch_board(name)


def get_active_board() -> Optional[BoardInfo]:
    return get_multiboard_manager().get_active_board()


def get_active_board_path() -> Path:
    return get_multiboard_manager().get_active_board_path()


def list_boards() -> List[BoardInfo]:
    return get_multiboard_manager().list_boards()


def export_board(name: str, output_path: Path) -> Optional[Path]:
    return get_multiboard_manager().export_board(name, output_path)


def import_board(export_path: Path, name: Optional[str] = None) -> Optional[str]:
    return get_multiboard_manager().import_board(export_path, name)
