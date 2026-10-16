import sys
from collections import deque
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pathfinding import astar, dijkstra, generate_maze, is_reachable
from pathfinding.grid import FREE, WALL, neighbors

ALGOS = [dijkstra, astar, lambda g, s, t: astar(g, s, t, "euclidean")]


def bfs_length(grid, start, goal):
    """Independent oracle: BFS gives the shortest step count on a unit-cost grid."""
    dist, queue = {start: 0}, deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            return dist[cell]
        for nxt in neighbors(grid, cell):
            if nxt not in dist:
                dist[nxt] = dist[cell] + 1
                queue.append(nxt)
    return None


def assert_valid_path(grid, result, start, goal):
    assert result.path[0] == start and result.path[-1] == goal
    assert len(result.path) - 1 == result.path_length
    for a, b in zip(result.path, result.path[1:]):
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1  # one step at a time
        assert grid[b] == FREE                             # never through a wall


@pytest.mark.parametrize("algo", ALGOS)
@pytest.mark.parametrize("seed", range(10))
def test_optimal_and_valid_on_random_mazes(algo, seed):
    grid, start, goal = generate_maze(25, 30, 0.25, seed)
    result = algo(grid, start, goal)
    assert result.found
    assert result.path_length == bfs_length(grid, start, goal)
    assert_valid_path(grid, result, start, goal)


def test_astar_expands_fewer_nodes_on_open_grid():
    grid = np.zeros((40, 40), dtype=np.int8)
    d, a = dijkstra(grid, (0, 0), (39, 39)), astar(grid, (0, 0), (39, 39))
    assert d.path_length == a.path_length == 78
    assert a.expanded_nodes < d.expanded_nodes


@pytest.mark.parametrize("algo", ALGOS)
def test_unreachable_goal(algo):
    grid = np.zeros((5, 5), dtype=np.int8)
    grid[:, 2] = WALL  # full wall splits the grid
    result = algo(grid, (0, 0), (4, 4))
    assert not result.found and result.path == [] and result.path_length == 0


@pytest.mark.parametrize("algo", ALGOS)
def test_start_equals_goal(algo):
    grid = np.zeros((3, 3), dtype=np.int8)
    result = algo(grid, (1, 1), (1, 1))
    assert result.found and result.path == [(1, 1)] and result.path_length == 0


@pytest.mark.parametrize("algo", ALGOS)
def test_wall_start_or_goal_rejected(algo):
    grid = np.zeros((3, 3), dtype=np.int8)
    grid[0, 0] = WALL
    with pytest.raises(ValueError):
        algo(grid, (0, 0), (2, 2))


def test_metrics_are_consistent():
    grid, start, goal = generate_maze(20, 20, 0.2, 1)
    r = astar(grid, start, goal)
    assert r.expanded_nodes == len(r.expanded_order)
    assert r.expanded_density == pytest.approx(r.expanded_nodes / (grid == FREE).sum())
    assert 0 < r.expanded_density <= 1 and r.runtime_s > 0


def test_maze_generation_reproducible_and_solvable():
    g1, s, t = generate_maze(30, 30, 0.3, seed=7)
    g2, _, _ = generate_maze(30, 30, 0.3, seed=7)
    assert np.array_equal(g1, g2)
    assert is_reachable(g1, s, t) and g1[s] == FREE and g1[t] == FREE


def test_maze_generation_bad_input():
    with pytest.raises(ValueError):
        generate_maze(10, 10, 1.0)
    with pytest.raises(ValueError):
        generate_maze(1, 10, 0.1)
    with pytest.raises(ValueError):
        generate_maze(10, 10, 0.95, max_attempts=3)  # practically never solvable
