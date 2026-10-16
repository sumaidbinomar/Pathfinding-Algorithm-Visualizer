"""Benchmark the algorithms on identical mazes and export the metrics.

Every (size, density, seed) combination builds ONE maze, and every algorithm solves that
same maze, so the comparison is fair. Runtime is the median of several repeats to reduce
timing noise; the other metrics are deterministic.
"""
import csv
import json
import statistics
from pathlib import Path
from typing import Dict, List, Sequence

from .algorithms import astar, dijkstra
from .grid import generate_maze

ALGORITHMS = {
    "dijkstra": dijkstra,
    "astar_manhattan": lambda g, s, t: astar(g, s, t, "manhattan"),
    "astar_euclidean": lambda g, s, t: astar(g, s, t, "euclidean"),
}
DEFAULT_SIZES = (20, 50, 100)
DEFAULT_DENSITIES = (0.1, 0.2, 0.3)
DEFAULT_SEEDS = tuple(range(10))
METRICS = ("path_length", "expanded_nodes", "expanded_density", "runtime_ms")


def run_benchmark(sizes: Sequence[int] = DEFAULT_SIZES, densities: Sequence[float] = DEFAULT_DENSITIES,
                  seeds: Sequence[int] = DEFAULT_SEEDS, repeats: int = 5) -> List[Dict]:
    """Return one row per (size, density, seed, algorithm)."""
    rows = []
    for size in sizes:
        for density in densities:
            for seed in seeds:
                grid, start, goal = generate_maze(size, size, density, seed)
                lengths = set()
                for name, algo in ALGORITHMS.items():
                    runs = [algo(grid, start, goal) for _ in range(repeats)]
                    result = runs[0]
                    lengths.add(result.path_length)
                    rows.append({
                        "size": size, "density": density, "seed": seed, "algorithm": name,
                        "path_length": result.path_length,
                        "expanded_nodes": result.expanded_nodes,
                        "expanded_density": round(result.expanded_density, 4),
                        "runtime_ms": round(statistics.median(r.runtime_s for r in runs) * 1000, 4),
                    })
                if len(lengths) != 1:  # all three are optimal, so they must agree
                    raise AssertionError(f"algorithms disagree on path length for {size}x{size} d={density} seed={seed}: {lengths}")
    return rows


def summarize(rows: List[Dict]) -> List[Dict]:
    """Average each metric over the seeds, per (size, density, algorithm)."""
    groups: Dict[tuple, List[Dict]] = {}
    for row in rows:
        groups.setdefault((row["size"], row["density"], row["algorithm"]), []).append(row)
    summary = []
    for (size, density, algorithm), items in groups.items():
        entry = {"size": size, "density": density, "algorithm": algorithm, "mazes": len(items)}
        for metric in METRICS:
            entry[f"mean_{metric}"] = round(statistics.mean(r[metric] for r in items), 4)
        summary.append(entry)
    return summary


def save_results(rows: List[Dict], summary: List[Dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in (("benchmark_results", rows), ("benchmark_summary", summary)):
        with open(out_dir / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    (out_dir / "benchmark_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
