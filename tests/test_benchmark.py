import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pathfinding.benchmark import ALGORITHMS, run_benchmark, save_results, summarize


def small_run():
    return run_benchmark(sizes=(10, 15), densities=(0.1, 0.2), seeds=(0, 1), repeats=2)


def test_one_row_per_combination():
    rows = small_run()
    assert len(rows) == 2 * 2 * 2 * len(ALGORITHMS)


def test_summary_averages_over_seeds():
    rows = small_run()
    summary = summarize(rows)
    assert len(summary) == 2 * 2 * len(ALGORITHMS)
    assert all(s["mazes"] == 2 for s in summary)
    first = summary[0]
    matching = [r["expanded_nodes"] for r in rows
                if (r["size"], r["density"], r["algorithm"]) == (first["size"], first["density"], first["algorithm"])]
    assert first["mean_expanded_nodes"] == sum(matching) / len(matching)


def test_save_results_writes_files(tmp_path):
    rows = small_run()
    save_results(rows, summarize(rows), tmp_path)
    for name in ("benchmark_results.csv", "benchmark_summary.csv", "benchmark_summary.json"):
        assert (tmp_path / name).exists()
    with open(tmp_path / "benchmark_results.csv", newline="") as f:
        assert len(list(csv.DictReader(f))) == len(rows)
