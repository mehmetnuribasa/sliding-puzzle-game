"""
Solver module for the Sliding Puzzle Game.

Contains solvability verification and A* search-based auto-solver.
The solvability check uses inversion counting to guarantee every
generated puzzle can be completed by the player.
"""

import heapq


# ---------------------------------------------------------------------------
# Solvability helpers
# ---------------------------------------------------------------------------

def count_inversions(flat_grid):
    """
    Count inversions in a flattened grid (excluding the empty tile 0).

    An inversion is a pair (a, b) where a appears before b but a > b.
    """
    tiles = [t for t in flat_grid if t != 0]
    inversions = 0
    for i in range(len(tiles)):
        for j in range(i + 1, len(tiles)):
            if tiles[i] > tiles[j]:
                inversions += 1
    return inversions


def find_blank_row_from_bottom(grid, size):
    """Return the row of the blank tile counting from the bottom (1-indexed)."""
    for row in range(size):
        for col in range(size):
            if grid[row][col] == 0:
                return size - row
    return -1


def is_solvable(grid, size):
    """
    Determine whether a sliding puzzle configuration is solvable.

    Rules:
      - Odd-width grids  (3×3): solvable iff inversion count is even.
      - Even-width grids (4×4): solvable iff (inversions + blank_row_from_bottom) is odd.
    """
    flat = [grid[r][c] for r in range(size) for c in range(size)]
    inversions = count_inversions(flat)

    if size % 2 == 1:
        return inversions % 2 == 0
    else:
        blank_row = find_blank_row_from_bottom(grid, size)
        return (inversions + blank_row) % 2 == 1


# ---------------------------------------------------------------------------
# Goal state utilities
# ---------------------------------------------------------------------------

def get_goal_state(size):
    """
    Generate the goal (solved) state for a given grid size.

    Tiles numbered 1..(size*size-1), blank (0) in the bottom-right corner.
    """
    goal = []
    num = 1
    for r in range(size):
        row = []
        for c in range(size):
            if r == size - 1 and c == size - 1:
                row.append(0)
            else:
                row.append(num)
                num += 1
        goal.append(row)
    return goal


def find_blank(grid, size):
    """Return (row, col) of the blank tile (0)."""
    for r in range(size):
        for c in range(size):
            if grid[r][c] == 0:
                return r, c
    return -1, -1


# ---------------------------------------------------------------------------
# A* solver (practical only for 3×3 grids)
# ---------------------------------------------------------------------------

def manhattan_distance(grid, size):
    """Calculate total Manhattan distance of all tiles from goal positions."""
    distance = 0
    for r in range(size):
        for c in range(size):
            val = grid[r][c]
            if val != 0:
                goal_r = (val - 1) // size
                goal_c = (val - 1) % size
                distance += abs(r - goal_r) + abs(c - goal_c)
    return distance


def _grid_to_tuple(grid):
    """Convert 2-D grid to a hashable tuple of tuples."""
    return tuple(tuple(row) for row in grid)


def _tuple_to_grid(t):
    """Convert tuple of tuples back to a 2-D list grid."""
    return [list(row) for row in t]


def solve_astar(grid, size):
    """
    Solve the puzzle using A* with Manhattan distance heuristic.

    Only recommended for 3×3 grids (larger grids are computationally
    prohibitive).  Returns a list of direction strings that move the
    *blank* tile, or ``None`` if no solution is found / grid too large.
    """
    if size > 3:
        return None  # Too complex for larger grids

    goal = _grid_to_tuple(get_goal_state(size))
    start = _grid_to_tuple(grid)

    if start == goal:
        return []

    # Priority queue entries: (f_score, counter, grid_tuple, move_list)
    counter = 0
    h = manhattan_distance(grid, size)
    open_set = [(h, counter, start, [])]
    closed_set = set()

    # Map the visual direction of the *tile* moving.
    # "up" means tile moves up -> blank moves down (dr=1).
    directions = {
        "up": (1, 0),
        "down": (-1, 0),
        "left": (0, 1),
        "right": (0, -1),
    }

    while open_set:
        _f, _, current, moves = heapq.heappop(open_set)

        if current == goal:
            return moves

        if current in closed_set:
            continue
        closed_set.add(current)

        curr_grid = _tuple_to_grid(current)
        br, bc = find_blank(curr_grid, size)

        for direction, (dr, dc) in directions.items():
            nr, nc = br + dr, bc + dc
            if 0 <= nr < size and 0 <= nc < size:
                new_grid = [row[:] for row in curr_grid]
                new_grid[br][bc], new_grid[nr][nc] = new_grid[nr][nc], new_grid[br][bc]
                new_tuple = _grid_to_tuple(new_grid)

                if new_tuple not in closed_set:
                    g = len(moves) + 1
                    h = manhattan_distance(new_grid, size)
                    counter += 1
                    heapq.heappush(
                        open_set,
                        (g + h, counter, new_tuple, moves + [direction]),
                    )

    return None  # No solution found
