"""Dijkstra's algorithm and A* search, written from scratch on a 4-connected grid.

Both are the same best-first search; they differ only in how the next cell is chosen:
    Dijkstra:  priority = g                (cost so far)
    A*:        priority = g + h(cell, goal) (cost so far + estimate of cost left)
With h = 0 A* *is* Dijkstra. Manhattan and Euclidean estimates never overestimate the
true cost on a 4-connected unit-cost grid (they are "admissible"), so A* stays optimal.
"""
import heapq
import itertools
import math
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np

from .grid import FREE, Cell, neighbors

Heuristic = Callable[[Cell, Cell], float]


def manhattan(a: Cell, b: Cell) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a: Cell, b: Cell) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def zero(a: Cell, b: Cell) -> float:
    return 0.0


HEURISTICS: Dict[str, Heuristic] = {"manhattan": manhattan, "euclidean": euclidean}


@dataclass
class SearchResult:
    """Everything we want to know about one search run."""
    algorithm: str
    found: bool
    path: List[Cell]                 # start..goal inclusive; empty if not found
    path_length: int                 # number of steps (moves) in the path
    expanded_nodes: int              # cells taken off the priority queue and processed
    expanded_density: float          # expanded_nodes / free cells in the grid
    runtime_s: float
    expanded_order: List[Cell] = field(repr=False, default_factory=list)  # for visualization


def _search(grid: np.ndarray, start: Cell, goal: Cell, heuristic: Heuristic, name: str) -> SearchResult:
    if grid[start] != FREE or grid[goal] != FREE:
        raise ValueError("start and goal must be free cells")

    t0 = time.perf_counter()
    counter = itertools.count()  # tie-breaker so the heap never compares cells and ties stay deterministic
    h0 = heuristic(start, goal)
    # Heap items: (f, h, insertion order, cell). Preferring smaller h on equal f pushes A* toward the goal.
    heap = [(h0, h0, next(counter), start)]
    g_cost: Dict[Cell, float] = {start: 0}
    parent: Dict[Cell, Optional[Cell]] = {start: None}
    closed = set()
    expanded_order: List[Cell] = []
    found = False

    while heap:
        _, _, _, cell = heapq.heappop(heap)
        if cell in closed:  # stale duplicate entry (a cheaper route was already processed)
            continue
        closed.add(cell)
        expanded_order.append(cell)
        if cell == goal:
            found = True
            break
        for nxt in neighbors(grid, cell):
            new_g = g_cost[cell] + 1
            if nxt not in g_cost or new_g < g_cost[nxt]:
                g_cost[nxt] = new_g
                parent[nxt] = cell
                h = heuristic(nxt, goal)
                heapq.heappush(heap, (new_g + h, h, next(counter), nxt))

    path: List[Cell] = []
    if found:
        cell: Optional[Cell] = goal
        while cell is not None:
            path.append(cell)
            cell = parent[cell]
        path.reverse()
    runtime = time.perf_counter() - t0

    free_cells = int((grid == FREE).sum())
    return SearchResult(
        algorithm=name, found=found, path=path,
        path_length=len(path) - 1 if found else 0,
        expanded_nodes=len(expanded_order),
        expanded_density=len(expanded_order) / free_cells,
        runtime_s=runtime, expanded_order=expanded_order,
    )


def dijkstra(grid: np.ndarray, start: Cell, goal: Cell) -> SearchResult:
    """Dijkstra's algorithm: expands cells in order of cost-so-far, with no sense of direction."""
    return _search(grid, start, goal, zero, "dijkstra")


def astar(grid: np.ndarray, start: Cell, goal: Cell, heuristic: str = "manhattan") -> SearchResult:
    """A* search: like Dijkstra but biased toward the goal by a heuristic estimate."""
    return _search(grid, start, goal, HEURISTICS[heuristic], f"astar_{heuristic}")
