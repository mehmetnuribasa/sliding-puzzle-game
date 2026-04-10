"""
Game module for the Sliding Puzzle Game.

Contains the Board class which manages all game state: grid layout,
move validation, move history (for undo), timer, and win detection.
"""

import random
import time

from solver import is_solvable, get_goal_state, find_blank


class Board:
    """
    Represents the sliding puzzle board.

    The grid is a 2-D list of integers where 0 represents the empty tile.
    Goal state has tiles 1..(N*N-1) in row-major order with 0 at the
    bottom-right corner.
    """

    def __init__(self, size=3):
        """
        Initialise a new board of the given *size* (3 → 3×3, 4 → 4×4).

        The board is automatically shuffled into a valid, solvable state.
        """
        self.size = size
        self.goal = get_goal_state(size)
        self.grid = []
        self.move_count = 0
        self.start_time = None
        self.elapsed_time = 0.0
        self.paused = False
        self.pause_start = None
        self.total_pause_time = 0.0
        self.move_history = []  # Stack of (row, col) for undo
        self.solved = False
        self.best_moves = None   # Best score tracking (in-memory)
        self.best_time = None
        self.reset()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def reset(self):
        """Reset the board to a new shuffled, solvable configuration."""
        self.grid = [row[:] for row in self.goal]
        self.move_count = 0
        self.start_time = None
        self.elapsed_time = 0.0
        self.paused = False
        self.pause_start = None
        self.total_pause_time = 0.0
        self.move_history = []
        self.solved = False
        self.shuffle()

    def shuffle(self):
        """
        Shuffle tiles randomly while guaranteeing solvability.

        Uses Fisher-Yates shuffle on a flat list, then checks solvability.
        If unsolvable, swaps the first two non-zero tiles to fix parity.
        Re-shuffles if the result happens to already be solved.
        """
        flat = list(range(self.size * self.size))
        random.shuffle(flat)

        # Rebuild grid from flat list
        self.grid = []
        for r in range(self.size):
            row = []
            for c in range(self.size):
                row.append(flat[r * self.size + c])
            self.grid.append(row)

        # Fix solvability if needed
        if not is_solvable(self.grid, self.size):
            positions = []
            for r in range(self.size):
                for c in range(self.size):
                    if self.grid[r][c] != 0:
                        positions.append((r, c))
                    if len(positions) == 2:
                        break
                if len(positions) == 2:
                    break
            r1, c1 = positions[0]
            r2, c2 = positions[1]
            self.grid[r1][c1], self.grid[r2][c2] = (
                self.grid[r2][c2],
                self.grid[r1][c1],
            )

        # Avoid starting in the solved state
        if self.is_solved():
            self.shuffle()

    # ------------------------------------------------------------------
    # Tile movement
    # ------------------------------------------------------------------

    def find_blank(self):
        """Return (row, col) of the blank tile."""
        return find_blank(self.grid, self.size)

    def move_tile(self, row, col):
        """
        Attempt to slide the tile at (*row*, *col*) into the blank space.

        Returns ``True`` if the move was valid and executed, ``False``
        otherwise.  Starts the timer on the first valid move and checks
        the win condition after every successful move.
        """
        if self.solved or self.paused:
            return False

        br, bc = self.find_blank()

        # Only adjacent tiles (Manhattan distance 1) may move
        if abs(row - br) + abs(col - bc) != 1:
            return False

        # Start timer on the very first move
        if self.start_time is None:
            self.start_time = time.time()

        # Swap tile with blank
        self.grid[br][bc], self.grid[row][col] = (
            self.grid[row][col],
            self.grid[br][bc],
        )
        self.move_count += 1
        self.move_history.append((br, bc))

        # Win detection
        if self.is_solved():
            self.solved = True
            self.elapsed_time = self.get_elapsed_time()
            self._update_best_score()

        return True

    def move_by_direction(self, direction):
        """
        Move a tile using a direction string (``'up'``, ``'down'``,
        ``'left'``, ``'right'``).

        The direction refers to the visual movement of the *tile*
        (not the blank).  For example ``'up'`` slides the tile that is
        below the blank upward into the gap.

        Returns ``(moved, from_row, from_col)``.
        """
        br, bc = self.find_blank()

        # Map: direction the tile moves → position of the tile to move
        dir_map = {
            "up": (br + 1, bc),
            "down": (br - 1, bc),
            "left": (br, bc + 1),
            "right": (br, bc - 1),
        }

        if direction not in dir_map:
            return False, -1, -1

        tr, tc = dir_map[direction]

        if 0 <= tr < self.size and 0 <= tc < self.size:
            if self.move_tile(tr, tc):
                return True, tr, tc

        return False, -1, -1

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def undo(self):
        """
        Undo the most recent move.

        Returns ``(success, from_row, from_col)`` where *from_row/col*
        is the position the tile animated *from* (i.e. the current blank
        that will receive the tile back).
        """
        if not self.move_history or self.solved:
            return False, -1, -1

        last_row, last_col = self.move_history.pop()
        br, bc = self.find_blank()

        self.grid[br][bc], self.grid[last_row][last_col] = (
            self.grid[last_row][last_col],
            self.grid[br][bc],
        )
        self.move_count = max(0, self.move_count - 1)
        return True, br, bc

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def is_solved(self):
        """Return ``True`` if the grid matches the goal state."""
        return self.grid == self.goal

    def get_elapsed_time(self):
        """Return elapsed play time in seconds (excludes paused time)."""
        if self.start_time is None:
            return 0.0
        if self.solved:
            return self.elapsed_time
        if self.paused:
            return self.pause_start - self.start_time - self.total_pause_time
        return time.time() - self.start_time - self.total_pause_time

    def is_tile_in_correct_position(self, row, col):
        """Return ``True`` if the tile at (*row*, *col*) matches the goal."""
        return (
            self.grid[row][col] == self.goal[row][col]
            and self.grid[row][col] != 0
        )

    def get_tile_value(self, row, col):
        """Return the integer value of the tile at (*row*, *col*)."""
        return self.grid[row][col]

    # ------------------------------------------------------------------
    # Pause
    # ------------------------------------------------------------------

    def toggle_pause(self):
        """Toggle the pause state (no effect if game hasn't started or is won)."""
        if self.solved or self.start_time is None:
            return

        if self.paused:
            self.total_pause_time += time.time() - self.pause_start
            self.paused = False
        else:
            self.pause_start = time.time()
            self.paused = True

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _update_best_score(self):
        """Update in-memory best score if the current run is better."""
        if self.best_moves is None or self.move_count < self.best_moves:
            self.best_moves = self.move_count
        if self.best_time is None or self.elapsed_time < self.best_time:
            self.best_time = self.elapsed_time
