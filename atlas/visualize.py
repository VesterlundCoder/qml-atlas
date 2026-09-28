"""Atlas visualization: phase diagrams and QA distributions.

Generates the key figures for the Quantum Advantage Boundary Atlas:
  - Phase diagram: A(n, r, B) heatmap
  - QA level distribution
  - Status distribution (red/yellow/green)
  - Per-method comparison

Usage:
    python -m projects.QAB.atlas.visualize --output figures/
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from projects.QAB.atlas.registry import AtlasRegistry

ATLAS_DIR = Path(__file__).resolve().parent / "v0.1"
DB_PATH = ATLAS_DIR / "atlas.db"


def fig_phase_diagram(registry: AtlasRegistry, output_dir: Path):
    """Recovery phase diagram: P_recover(n, r) for uniform sampling."""
    records = registry.query(track="infrastructure", project="R01")
    phase_records = [r for r in records if r.metadata.get("type") == "phase_diagram"]

    if not phase_records:
        print("  [SKIP] No phase diagram records found")
        return

    # Build n × r matrix
    sizes = sorted(set(r.problem_size for r in phase_records))
    radii = sorted(set(r.metadata.get("radius", 0) for r in phase_records))

    matrix = np.full((len(sizes), len(radii)), np.nan)
    for r in phase_records:
        i = sizes.index(r.problem_size)
        j = radii.index(r.metadata.get("radius", 0))
        matrix[i, j] = r.metric_C

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(radii)))
    ax.set_xticklabels([f"r={r}" for r in radii])
    ax.set_yticks(range(len(sizes)))
    ax.set_yticklabels([f"n={n}" for n in sizes])
    ax.set_xlabel("Recovery radius r")
    ax.set_ylabel("Problem size n")
    ax.set_title("Recovery Phase Diagram: $P_{recover}(n, r, B=200)$")

    for i in range(len(sizes)):
        for j in range(len(radii)):
            if not np.isnan(matrix[i, j]):
                ax.text(j, i, f"{matrix[i,j]:.3f}", ha="center", va="center", fontsize=9)

    plt.colorbar(im, ax=ax, label="$P_{recover}$")
    plt.tight_layout()
    path = output_dir / "atlas_phase_diagram.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


def fig_qa_distribution(registry: AtlasRegistry, output_dir: Path):
    """QA level distribution across all records."""
    records = registry.query()
    if not records:
        return

    qa_counts = defaultdict(int)
    for r in records:
        qa_counts[r.qa_level] += 1

    levels = sorted(qa_counts.keys())
    counts = [qa_counts[l] for l in levels]
    labels = [f"QA{l}" if l >= 0 else "N/A" for l in levels]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#999999", "#ff6b6b", "#ffd93d", "#6bcf7f", "#4ecdc4", "#45b7d1", "#a78bfa"]
    ax.bar(labels, counts, color=[colors[l + 1] if l + 1 < len(colors) else "#999999" for l in levels])
    ax.set_xlabel("QA Level")
    ax.set_ylabel("Number of experiments")
    ax.set_title("Quantum Advantage Ladder Distribution")
    plt.tight_layout()
    path = output_dir / "atlas_qa_distribution.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


def fig_status_pie(registry: AtlasRegistry, output_dir: Path):
    """Status distribution: red/yellow/green."""
    status_counts = registry.count_by_status()
    if not status_counts:
        return

    colors_map = {
        "classical_advantage": "#ff6b6b",
        "unresolved": "#ffd93d",
        "quantum_candidate": "#6bcf7f",
        "not_assessed": "#cccccc",
    }
    labels = list(status_counts.keys())
    sizes = [status_counts[l] for l in labels]
    colors = [colors_map.get(l, "#999999") for l in labels]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
    ax.set_title("Experiment Outcomes")
    plt.tight_layout()
    path = output_dir / "atlas_status_pie.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


def fig_sampler_comparison(registry: AtlasRegistry, output_dir: Path):
    """Mean p_r by sampler across sizes (from GQO records)."""
    records = registry.query(project="R12")
    if not records:
        return

    # Group by (sampler, n)
    data = defaultdict(list)
    for r in records:
        sampler = r.metadata.get("sampler", r.quantum_method or r.classical_method)
        data[(sampler, r.problem_size)].append(r.metric_Q or r.metric_C)

    samplers = sorted(set(k[0] for k in data))
    sizes = sorted(set(k[1] for k in data))

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(sizes))
    width = 0.8 / len(samplers)

    for i, sampler in enumerate(samplers):
        means = [np.mean(data.get((sampler, n), [0])) for n in sizes]
        ax.bar(x + i * width, means, width, label=sampler)

    ax.set_xticks(x + width * len(samplers) / 2)
    ax.set_xticklabels([f"n={n}" for n in sizes])
    ax.set_ylabel("Mean $p_r$")
    ax.set_title("Recovery-Basin Mass by Sampler and Size")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    path = output_dir / "atlas_sampler_comparison.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  [OK] {path}")


def main():
    parser = argparse.ArgumentParser(description="Visualize the Atlas")
    parser.add_argument("--output", type=str, default="figures", help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    registry = AtlasRegistry(DB_PATH)
    print(f"Visualizing Atlas ({registry.count()} records)...")

    fig_phase_diagram(registry, output_dir)
    fig_qa_distribution(registry, output_dir)
    fig_status_pie(registry, output_dir)
    fig_sampler_comparison(registry, output_dir)

    print(f"\nFigures saved to {output_dir}/")


if __name__ == "__main__":
    main()
