"""Run the full experiment and export everything to results/.

    python main.py            # full benchmark (3 sizes x 3 densities x 10 seeds)
    python main.py --quick    # small, fast run for a smoke test
"""
import argparse
from pathlib import Path

from pathfinding.benchmark import ALGORITHMS, run_benchmark, save_results, summarize
from pathfinding.grid import generate_maze
from pathfinding.visualize import make_search_gif, plot_benchmark_summary, plot_maze_comparison

RESULTS = Path(__file__).parent / "results"
SHOWCASE = [(30, 0.10), (50, 0.25), (100, 0.30)]  # (size, obstacle density) mazes drawn as images
SHOWCASE_SEED = 3


def main() -> None:
    parser = argparse.ArgumentParser(description="Dijkstra vs A* grid pathfinding experiments.")
    parser.add_argument("--quick", action="store_true", help="small, fast run")
    args = parser.parse_args()

    if args.quick:
        rows = run_benchmark(sizes=(10, 20), densities=(0.1, 0.3), seeds=range(2), repeats=1)
    else:
        print("Running benchmark (about 15 seconds)...")
        rows = run_benchmark()
    summary = summarize(rows)
    save_results(rows, summary, RESULTS)
    plot_benchmark_summary(summary, RESULTS / "benchmark_summary.png")
    print(f"Benchmark: {len(rows)} runs saved to {RESULTS}")

    # One example maze per showcase setting, solved by every algorithm.
    for size, density in SHOWCASE:
        grid, start, goal = generate_maze(size, size, density, SHOWCASE_SEED)
        results = {name: algo(grid, start, goal) for name, algo in ALGORITHMS.items()}
        out = RESULTS / f"maze_{size}x{size}_{int(density * 100)}pct.png"
        plot_maze_comparison(grid, start, goal, results, out,
                             title=f"{size}×{size} maze, {density:.0%} obstacles (seed {SHOWCASE_SEED})")
        print(f"  {out.name}: " + ", ".join(f"{n}={r.expanded_nodes} expanded" for n, r in results.items()))

    # Animated search on a mid-sized maze.
    grid, start, goal = generate_maze(40, 40, 0.2, SHOWCASE_SEED)
    gif_results = [ALGORITHMS[n](grid, start, goal) for n in ("dijkstra", "astar_manhattan")]
    make_search_gif(grid, start, goal, gif_results, RESULTS / "search_animation.gif")
    print("Saved search_animation.gif")


if __name__ == "__main__":
    main()
