import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pathfinding import astar, dijkstra, generate_maze
from pathfinding.benchmark import run_benchmark, summarize
from pathfinding.visualize import make_search_gif, plot_benchmark_summary, plot_maze_comparison


def solve_all(size=15, density=0.2, seed=0):
    grid, s, g = generate_maze(size, size, density, seed)
    results = {"dijkstra": dijkstra(grid, s, g), "astar_manhattan": astar(grid, s, g)}
    return grid, s, g, results


def test_maze_comparison_png(tmp_path):
    grid, s, g, results = solve_all()
    out = tmp_path / "maze.png"
    plot_maze_comparison(grid, s, g, results, out, title="test")
    assert out.stat().st_size > 1000


def test_benchmark_summary_png(tmp_path):
    rows = run_benchmark(sizes=(10, 15), densities=(0.1, 0.2, 0.3), seeds=(0, 1), repeats=1)
    out = tmp_path / "summary.png"
    plot_benchmark_summary(summarize(rows), out)
    assert out.stat().st_size > 1000


def test_gif(tmp_path):
    grid, s, g, results = solve_all()
    out = tmp_path / "search.gif"
    make_search_gif(grid, s, g, list(results.values()), out, frames=5, fps=5)
    assert out.read_bytes()[:3] == b"GIF"
