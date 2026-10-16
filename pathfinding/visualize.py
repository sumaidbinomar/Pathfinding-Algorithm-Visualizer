"""Visualizations: maze/path images, benchmark charts and a search-animation GIF.

Colors follow a validated palette (blue / orange / aqua for the three algorithms, checked for
color-blind separation). Each algorithm also has its own marker and line style so the charts
never rely on color alone.
"""
from pathlib import Path
from typing import Dict, List, Sequence

import matplotlib

matplotlib.use("Agg")  # render to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .algorithms import SearchResult
from .grid import Cell

# --- palette (see module docstring) ---
SURFACE, INK, INK_2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
STYLE = {  # algorithm -> (label, color, marker, linestyle)
    "dijkstra": ("Dijkstra", "#2a78d6", "o", "-"),
    "astar_manhattan": ("A* (Manhattan)", "#eb6834", "s", "--"),
    "astar_euclidean": ("A* (Euclidean)", "#1baf7a", "^", ":"),
}
# Maze cell colors: 0 free, 1 wall, 2 explored, 3 path
MAZE_CMAP = ListedColormap([SURFACE, "#383835", "#b7d3f6", "#104281"])
START_GOAL_COLOR = "#eb6834"

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "DejaVu Sans"],
    "text.color": INK, "axes.labelcolor": INK_2, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": GRID, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.spines.top": False, "axes.spines.right": False,
})


def _draw_maze(ax, grid: np.ndarray, start: Cell, goal: Cell, result: SearchResult, shown: int = None) -> None:
    """Draw walls, the cells explored so far, the final path, and the start/goal."""
    canvas = grid.astype(int).copy()  # 0 free / 1 wall
    explored = result.expanded_order if shown is None else result.expanded_order[:shown]
    for cell in explored:
        canvas[cell] = 2
    if result.found and (shown is None or shown >= len(result.expanded_order)):
        for cell in result.path:
            canvas[cell] = 3
    ax.imshow(canvas, cmap=MAZE_CMAP, vmin=0, vmax=3, interpolation="nearest")
    for cell, letter in ((start, "S"), (goal, "G")):
        ax.scatter(cell[1], cell[0], s=90, marker="s", color=START_GOAL_COLOR, zorder=3)
        ax.annotate(letter, (cell[1], cell[0]), ha="center", va="center", fontsize=6, color="white", zorder=4, weight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def _maze_legend(fig) -> None:
    fig.legend(handles=[
        Patch(color="#383835", label="Wall"), Patch(color="#b7d3f6", label="Explored cell"),
        Patch(color="#104281", label="Final path"), Patch(color=START_GOAL_COLOR, label="Start (S) / Goal (G)"),
    ], loc="lower center", ncol=4, frameon=False, fontsize=9, labelcolor=INK_2)


def plot_maze_comparison(grid: np.ndarray, start: Cell, goal: Cell, results: Dict[str, SearchResult],
                         path: Path, title: str = "") -> None:
    """Side-by-side image of what each algorithm explored on the same maze."""
    fig, axes = plt.subplots(1, len(results), figsize=(4.6 * len(results), 5.4))
    for ax, (name, res) in zip(np.atleast_1d(axes), results.items()):
        _draw_maze(ax, grid, start, goal, res)
        ax.set_title(f"{STYLE[name][0]}\npath {res.path_length} steps · expanded {res.expanded_nodes:,} "
                     f"({res.expanded_density:.0%} of free cells) · {res.runtime_s * 1000:.1f} ms",
                     fontsize=9, color=INK, pad=8)
    if title:
        fig.suptitle(title, fontsize=12, weight="bold", color=INK)
    _maze_legend(fig)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_benchmark_summary(summary: List[Dict], path: Path) -> None:
    """3x3 grid of small charts: rows = metric, columns = obstacle density, x = grid size."""
    metrics = [("mean_expanded_nodes", "Expanded nodes (log scale)", True),
               ("mean_runtime_ms", "Runtime, ms (log scale)", True),
               ("mean_expanded_density", "Expanded-node density", False)]
    densities = sorted({s["density"] for s in summary})
    sizes = sorted({s["size"] for s in summary})
    fig, axes = plt.subplots(len(metrics), len(densities), figsize=(11, 9), sharex=True, squeeze=False)

    for i, (key, ylabel, log) in enumerate(metrics):
        # share the y-range across a row so columns are directly comparable
        values = [s[key] for s in summary]
        lo, hi = min(values), max(values)
        for j, density in enumerate(densities):
            ax = axes[i][j]
            for name, (label, color, marker, ls) in STYLE.items():
                ys = [next(s[key] for s in summary
                           if s["size"] == n and s["density"] == density and s["algorithm"] == name) for n in sizes]
                ax.plot(range(len(sizes)), ys, color=color, marker=marker, linestyle=ls, linewidth=2,
                        markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)
            if log:
                ax.set_yscale("log")
                ax.set_ylim(lo * 0.7, hi * 1.5)
            else:
                ax.set_ylim(0, 1.05)
            ax.grid(axis="y", color=GRID, linewidth=0.8)
            ax.set_axisbelow(True)
            ax.set_xticks(range(len(sizes)))
            ax.set_xticklabels([f"{n}×{n}" for n in sizes])
            if i == 0:
                ax.set_title(f"{density:.0%} obstacles", fontsize=11, color=INK, weight="bold")
            if j == 0:
                ax.set_ylabel(ylabel, fontsize=9)
            if i == len(metrics) - 1:
                ax.set_xlabel("Grid size", fontsize=9)

    fig.legend(handles=[Line2D([0], [0], color=c, marker=m, linestyle=ls, linewidth=2, markersize=7, label=l)
                        for l, c, m, ls in STYLE.values()],
               loc="upper center", ncol=3, frameon=False, fontsize=10, labelcolor=INK_2, bbox_to_anchor=(0.5, 0.97))
    fig.suptitle("Pathfinding benchmark: Dijkstra vs A* (mean over seeds)", fontsize=13, weight="bold", y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_search_gif(grid: np.ndarray, start: Cell, goal: Cell, results: Sequence[SearchResult],
                    path: Path, frames: int = 45, fps: int = 12) -> None:
    """Animated side-by-side of cells being explored; the final path appears at the end."""
    fig, axes = plt.subplots(1, len(results), figsize=(4.4 * len(results), 5.0))
    longest = max(len(r.expanded_order) for r in results)
    steps = np.linspace(0, longest, frames).astype(int)
    steps = np.concatenate([steps, [longest] * 8])  # hold on the finished picture

    def draw(frame: int) -> None:
        for ax, res in zip(np.atleast_1d(axes), results):
            ax.clear()
            shown = min(int(steps[frame]), len(res.expanded_order))
            _draw_maze(ax, grid, start, goal, res, shown=shown)
            ax.set_title(f"{STYLE[res.algorithm][0]}\nexpanded {shown:,} / {len(res.expanded_order):,}",
                         fontsize=10, color=INK)

    _maze_legend(fig)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    anim = FuncAnimation(fig, draw, frames=len(steps))
    path.parent.mkdir(parents=True, exist_ok=True)
    anim.save(path, writer=PillowWriter(fps=fps))
    plt.close(fig)
