"""Grid world and random maze generation.

A grid is a 2-D NumPy array: 0 = free cell, 1 = wall. Cells are (row, col) tuples and
the agent moves in 4 directions (up, down, left, right), each step costing 1.
"""
from collections import deque
from typing import Iterator, Tuple

import numpy as np

Cell = Tuple[int, int]
FREE, WALL = 0, 1
MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))


def neighbors(grid: np.ndarray, cell: Cell) -> Iterator[Cell]:
    """Yield the free cells next to `cell` (inside the grid, not walls)."""
    rows, cols = grid.shape
    r, c = cell
    for dr, dc in MOVES:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr, nc] == FREE:
            yield (nr, nc)


def is_reachable(grid: np.ndarray, start: Cell, goal: Cell) -> bool:
    """Breadth-first flood fill: can the agent get from start to goal at all?"""
    if grid[start] != FREE or grid[goal] != FREE:
        return False
    seen, queue = {start}, deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            return True
        for nxt in neighbors(grid, cell):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return False


def generate_maze(rows: int, cols: int, density: float, seed: int = 0,
                  max_attempts: int = 200) -> Tuple[np.ndarray, Cell, Cell]:
    """Create a random obstacle grid that is guaranteed to be solvable.

    Each cell becomes a wall with probability `density`. The start is the top-left
    corner and the goal the bottom-right corner (always kept free). If a random
    layout happens to block every route, a new one is drawn from the same seeded
    generator, so the result is still fully reproducible for a given seed.

    Returns (grid, start, goal).
    """
    if not 0.0 <= density < 1.0:
        raise ValueError("density must be in [0, 1)")
    if rows < 2 or cols < 2:
        raise ValueError("grid must be at least 2x2")

    rng = np.random.default_rng(seed)
    start, goal = (0, 0), (rows - 1, cols - 1)
    for _ in range(max_attempts):
        grid = (rng.random((rows, cols)) < density).astype(np.int8)
        grid[start] = grid[goal] = FREE
        if is_reachable(grid, start, goal):
            return grid, start, goal
    raise ValueError(f"no solvable {rows}x{cols} maze found at density {density}; lower the density")
