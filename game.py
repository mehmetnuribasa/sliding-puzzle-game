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

    # Difficulty presets: (grid_size, shuffle_moves or None for full)
    DIFFICULTY_PRESETS = {
        "easy":   {"size": 3, "shuffle_moves": 15},
        "medium": {"size": 3, "shuffle_moves": None},   # Full shuffle
        "hard":   {"size": 4, "shuffle_moves": None},   # Full shuffle
    }

    def __init__(self, size=3, difficulty="medium"):
        """
        Initialise a new board of the given *size* (3 → 3×3, 4 → 4×4).

        The *difficulty* parameter controls shuffle intensity:
          - ``'easy'``   → 3×3 grid, 15 random moves from solved state
          - ``'medium'`` → 3×3 grid, full random shuffle
          - ``'hard'``   → 4×4 grid, full random shuffle

        The board is automatically shuffled into a valid, solvable state.
        """
        self.difficulty = difficulty
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
        preset = self.DIFFICULTY_PRESETS.get(self.difficulty)
        if preset and preset["shuffle_moves"] is not None:
            self.shuffle_limited(preset["shuffle_moves"])
        else:
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

    def shuffle_limited(self, num_moves=15):
        """
        Shuffle by making *num_moves* random moves from the solved state.

        This guarantees solvability (any sequence of moves from the goal
        is reversible) while producing an easier puzzle than a full
        random shuffle.  Avoids immediately undoing the previous move
        so the resulting state is meaningfully shuffled.
        """
        self.grid = [row[:] for row in self.goal]
        opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
        last_dir = None

        for _ in range(num_moves):
            br, bc = self.find_blank()
            dir_map = {
                "up":    (br - 1, bc),
                "down":  (br + 1, bc),
                "left":  (br, bc - 1),
                "right": (br, bc + 1),
            }
            candidates = []
            for d, (nr, nc) in dir_map.items():
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if last_dir is None or d != opposite[last_dir]:
                        candidates.append((d, nr, nc))
            if not candidates:
                continue
            d, nr, nc = random.choice(candidates)
            self.grid[br][bc], self.grid[nr][nc] = (
                self.grid[nr][nc],
                self.grid[br][bc],
            )
            last_dir = d

        # Avoid starting in the solved state
        if self.is_solved():
            self.shuffle_limited(num_moves)

    # ------------------------------------------------------------------
    # Tile movement
    # ------------------------------------------------------------------

    def find_blank(self):
        """Return (row, col) of the blank tile."""
        return find_blank(self.grid, self.size)

    def move_tile(self, row, col):
        """
        Attempt to slide the tile(s) between (*row*, *col*) and the blank space.
        Supports multi-tile sliding if they are in the same row or col.

        Returns a list of tuples for animation: (val, from_r, from_c, to_r, to_c).
        """
        if self.solved or self.paused:
            return []

        br, bc = self.find_blank()

        # Must be in same row or col, and not the blank itself
        if (row != br and col != bc) or (row == br and col == bc):
            return []

        if self.start_time is None:
            self.start_time = time.time()

        moves = self._execute_multi_move(row, col, br, bc)

        if moves:
            self.move_count += 1
            # Store the old blank position so undo can reverse the multi-move
            self.move_history.append((br, bc))

            if self.is_solved():
                self.elapsed_time = self.get_elapsed_time()
                self.solved = True
                self._update_best_score()

        return moves

    def _execute_multi_move(self, target_r, target_c, blank_r, blank_c):
        """Internal helper to shift tiles and return animation data."""
        moves = []
        if target_r == blank_r:
            # Horizontal slide
            step = 1 if target_c < blank_c else -1
            curr_c = blank_c
            while curr_c != target_c:
                next_c = curr_c - step
                val = self.grid[target_r][next_c]
                self.grid[target_r][curr_c] = val
                moves.append((val, target_r, next_c, target_r, curr_c))
                curr_c = next_c
            self.grid[target_r][target_c] = 0
        else:
            # Vertical slide
            step = 1 if target_r < blank_r else -1
            curr_r = blank_r
            while curr_r != target_r:
                next_r = curr_r - step
                val = self.grid[next_r][target_c]
                self.grid[curr_r][target_c] = val
                moves.append((val, next_r, target_c, curr_r, target_c))
                curr_r = next_r
            self.grid[target_r][target_c] = 0
            
        return moves

    def move_by_direction(self, direction):
        """
        Move a tile using a direction string (``'up'``, ``'down'``,
        ``'left'``, ``'right'``).

        The direction refers to the visual movement of the *tile*
        (not the blank).

        Returns a list of tuples for animation: (val, from_r, from_c, to_r, to_c).
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
            return []

        tr, tc = dir_map[direction]

        if 0 <= tr < self.size and 0 <= tc < self.size:
            return self.move_tile(tr, tc)

        return []

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def undo(self):
        """
        Undo the most recent move.

        Returns a list of tuples for animation: (val, from_r, from_c, to_r, to_c).
        """
        if not self.move_history or self.solved:
            return []

        old_br, old_bc = self.move_history.pop()
        curr_br, curr_bc = self.find_blank()

        # Reversing a multi-move is the same as moving the old blank space
        moves = self._execute_multi_move(old_br, old_bc, curr_br, curr_bc)
        
        if moves:
            self.move_count = max(0, self.move_count - 1)
            
        return moves

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
