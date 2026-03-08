"""
board_manager.py — Multi-board support (TASK 6025)

Allows agents to work with multiple independent boards.
Each board is isolated and independent.
"""

import json
import os
from pathlib import Path
from typing import Optional, List


class BoardManager:
    """Manages multiple independent boards."""

    def __init__(self, default_board: Optional[str] = None, base_dir: Optional[Path] = None):
        """
        Initialize board manager.

        Args:
            default_board: Default board name (or None for 'board')
            base_dir: Base directory for all boards
        """
        self.base_dir = Path(base_dir) if base_dir else Path(
            os.environ.get("CLOWDER_BOARD_DIR", Path.cwd() / "board")
        ).parent
        self.default_board = default_board or "board"
        self.current_board = self.default_board

    def list_boards(self) -> List[str]:
        """List all available boards."""
        boards = []
        for item in self.base_dir.glob("board*"):
            if item.is_dir():
                boards.append(item.name)
        return sorted(boards)

    def create_board(self, name: str) -> bool:
        """Create a new board directory."""
        board_path = self.base_dir / name
        if board_path.exists():
            return False

        board_path.mkdir(parents=True, exist_ok=True)
        # Create empty board.json and agents.json
        (board_path / "board.json").write_text(json.dumps({"tasks": []}))
        (board_path / "agents.json").write_text(json.dumps({}))
        return True

    def switch_board(self, name: str) -> bool:
        """Switch to a different board."""
        board_path = self.base_dir / name
        if not board_path.exists():
            return False
        self.current_board = name
        return True

    def get_board_dir(self, board_name: Optional[str] = None) -> Path:
        """Get full path to board directory."""
        board = board_name or self.current_board
        return self.base_dir / board

    def get_board_json(self, board_name: Optional[str] = None) -> Path:
        """Get path to board.json file."""
        return self.get_board_dir(board_name) / "board.json"

    def get_agents_json(self, board_name: Optional[str] = None) -> Path:
        """Get path to agents.json file."""
        return self.get_board_dir(board_name) / "agents.json"

    def copy_board(self, from_board: str, to_board: str) -> bool:
        """Copy all data from one board to another."""
        from_dir = self.get_board_dir(from_board)
        to_dir = self.get_board_dir(to_board)

        if not from_dir.exists() or to_dir.exists():
            return False

        to_dir.mkdir(parents=True, exist_ok=True)

        # Copy board.json
        board_file = from_dir / "board.json"
        if board_file.exists():
            (to_dir / "board.json").write_text(board_file.read_text())

        # Copy agents.json
        agents_file = from_dir / "agents.json"
        if agents_file.exists():
            (to_dir / "agents.json").write_text(agents_file.read_text())

        return True

    def delete_board(self, name: str, force: bool = False) -> bool:
        """Delete a board. Won't delete default board unless forced."""
        if name == self.default_board and not force:
            return False

        board_path = self.get_board_dir(name)
        if not board_path.exists():
            return False

        # Switch to default board if deleting current
        if self.current_board == name:
            self.current_board = self.default_board

        # Remove board directory
        import shutil

        try:
            shutil.rmtree(board_path)
            return True
        except Exception:
            return False


# Global manager instance
_manager: Optional[BoardManager] = None


def get_board_manager() -> BoardManager:
    """Get global board manager instance."""
    global _manager
    if _manager is None:
        _manager = BoardManager()
    return _manager


def set_active_board(name: str) -> bool:
    """Switch to a different board."""
    return get_board_manager().switch_board(name)


def get_active_board_dir() -> Path:
    """Get current active board directory."""
    return get_board_manager().get_board_dir()


def list_all_boards() -> List[str]:
    """List all boards."""
    return get_board_manager().list_boards()


if __name__ == "__main__":
    manager = BoardManager()

    # Create some boards
    print("Creating test boards...")
    manager.create_board("board_team_a")
    manager.create_board("board_team_b")

    # List boards
    print(f"Available boards: {manager.list_boards()}")

    # Switch boards
    print(f"Current board: {manager.current_board}")
    manager.switch_board("board_team_a")
    print(f"Switched to: {manager.current_board}")
