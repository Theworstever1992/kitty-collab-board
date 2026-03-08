"""
test_multiboard.py — Tests for multi-board support (TASK 6025)

Tests multiple independent boards and board switching.
"""

import pytest
from pathlib import Path
from agents.board_manager import BoardManager


class TestMultiBoard:
    """Tests for multi-board functionality."""

    def test_create_board(self, tmp_path):
        """Test creating a new board."""
        manager = BoardManager(base_dir=tmp_path)

        success = manager.create_board("board_new")
        assert success
        assert (tmp_path / "board_new" / "board.json").exists()
        assert (tmp_path / "board_new" / "agents.json").exists()

    def test_list_boards(self, tmp_path):
        """Test listing boards."""
        manager = BoardManager(base_dir=tmp_path)

        manager.create_board("board_1")
        manager.create_board("board_2")
        manager.create_board("board_3")

        boards = manager.list_boards()
        assert len(boards) >= 3
        assert "board_1" in boards
        assert "board_2" in boards
        assert "board_3" in boards

    def test_switch_board(self, tmp_path):
        """Test switching between boards."""
        manager = BoardManager(base_dir=tmp_path)

        manager.create_board("board_alpha")
        manager.create_board("board_beta")

        assert manager.current_board == "board"
        success = manager.switch_board("board_alpha")
        assert success
        assert manager.current_board == "board_alpha"

    def test_copy_board(self, tmp_path):
        """Test copying board data."""
        manager = BoardManager(base_dir=tmp_path)

        # Create source board
        manager.create_board("source")
        board_dir = manager.get_board_dir("source")
        (board_dir / "board.json").write_text('{"tasks": [{"id": "1", "title": "Test"}]}')

        # Copy to new board
        success = manager.copy_board("source", "copy")
        assert success

        # Verify copy
        copy_dir = manager.get_board_dir("copy")
        assert copy_dir.exists()
        assert (copy_dir / "board.json").exists()

    def test_delete_board(self, tmp_path):
        """Test deleting a board."""
        manager = BoardManager(base_dir=tmp_path)

        manager.create_board("to_delete")
        assert (tmp_path / "to_delete").exists()

        success = manager.delete_board("to_delete")
        assert success
        assert not (tmp_path / "to_delete").exists()

    def test_cannot_delete_default_board(self, tmp_path):
        """Test that default board cannot be deleted."""
        manager = BoardManager(base_dir=tmp_path)

        success = manager.delete_board("board")
        assert not success  # Should fail without force=True

        success = manager.delete_board("board", force=True)
        assert success  # Should work with force=True

    def test_board_isolation(self, tmp_path):
        """Test that boards are independent."""
        manager = BoardManager(base_dir=tmp_path)

        # Create two boards with different content
        manager.create_board("board_isolated_1")
        manager.create_board("board_isolated_2")

        board1_dir = manager.get_board_dir("board_isolated_1")
        board2_dir = manager.get_board_dir("board_isolated_2")

        (board1_dir / "board.json").write_text('{"tasks": [{"id": "task_1"}]}')
        (board2_dir / "board.json").write_text('{"tasks": [{"id": "task_2"}]}')

        # Verify isolation
        board1_data = (board1_dir / "board.json").read_text()
        board2_data = (board2_dir / "board.json").read_text()

        assert "task_1" in board1_data
        assert "task_2" not in board1_data
        assert "task_2" in board2_data
        assert "task_1" not in board2_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
