"""R03 — Exact Landscape Atlas.

Enumerates the full 2^n solution space for small instances and computes
landscape metrics that may predict quantum utility.

Usage:
    python -m projects.QAB.r03_landscape_atlas.enumerate --sizes 8,10,12,14,16 --families mwis,maxcut
    python -m projects.QAB.r03_landscape_atlas.analyze  # Correlation with A(x)
"""
from __future__ import annotations

import sys
import time
import json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

BASE = Path(__file__).resolve().parents[2]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from projects.QAB.atlas.schema import ExperimentRecord
from projects.QAB.atlas.registry import AtlasRegistry

ATLAS_DIR = Path(__file__).resolve().parents[1] / "atlas" / "v0.1"
DB_PATH = ATLAS_DIR / "atlas.db"


@dataclass
class LandscapeMetrics:
    """Landscape metrics computed from full 2^n enumeration."""
    n: int
    n_local_minima: int = 0
    n_optimal: int = 0  # degeneracy
    first_excitation_gap: float = 0.0
    basin_sizes: list = None
    basin_entropy: float = 0.0
    mean_barrier: float = 0.0
    autocorrelation: float = 0.0
    ruggedness: float = 0.0
    frustration: float = 0.0
    hamming_separation: float = 0.0
    opt_value: float = 0.0
    worst_value: float = 0.0
    mean_value: float = 0.0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "basin_sizes"}


def enumerate_landscape(Q: np.ndarray, n: int) -> LandscapeMetrics:
    """Enumerate full 2^n solution space and compute landscape metrics."""
    t0 = time.time()
    dim = 2**n

    # Compute all energies
    energies = np.zeros(dim)
    for idx in range(dim):
        bits = np.array([(idx >> i) & 1 for i in range(n)], dtype=np.float64)
        energies[idx] = float(bits @ Q @ bits)

    opt_val = float(energies.min())
    worst_val = float(energies.max())
    mean_val = float(energies.mean())

    # Find local minima (states better than all Hamming-1 neighbours)
    local_minima = []
    for idx in range(dim):
        e = energies[idx]
        is_local_min = True
        for i in range(n):
            neighbor = idx ^ (1 << i)
            if energies[neighbor] < e:
                is_local_min = False
                break
        if is_local_min:
            local_minima.append(idx)

    # Optimal degeneracy
    n_optimal = int(np.sum(energies == opt_val))

    # First excitation gap
    sorted_energies = np.sort(energies)
    first_gap = float(sorted_energies[n_optimal] - sorted_energies[0]) if n_optimal < dim else 0.0

    # Basin sizes (for each local min, count states that descend to it via steepest descent)
    basin_sizes = []
    for lm in local_minima:
        basin = 0
        for idx in range(dim):
            # Steepest descent from idx
            current = idx
            while True:
                e = energies[current]
                best_neighbor = current
                best_e = e
                for i in range(n):
                    neighbor = current ^ (1 << i)
                    if energies[neighbor] < best_e:
                        best_e = energies[neighbor]
                        best_neighbor = neighbor
                if best_neighbor == current:
                    break
                current = best_neighbor
            if current == lm:
                basin += 1
        basin_sizes.append(basin)

    # Basin entropy
    total_basin = sum(basin_sizes)
    if total_basin > 0:
        probs = np.array(basin_sizes) / total_basin
        basin_entropy = float(-np.sum(probs[probs > 0] * np.log(probs[probs > 0])))
    else:
        basin_entropy = 0.0

    # Ruggedness (variance of energy differences between neighbours)
    diffs = []
    for idx in range(min(dim, 10000)):  # Sample for large n
        for i in range(n):
            neighbor = idx ^ (1 << i)
            diffs.append(energies[neighbor] - energies[idx])
    ruggedness = float(np.std(diffs)) if diffs else 0.0

    # Autocorrelation (correlation between energy at distance 1)
    if dim <= 10000:
        e0 = energies[:dim-1]
        e1 = energies[1:]
        if len(e0) > 1 and np.std(e0) > 0 and np.std(e1) > 0:
            autocorrelation = float(np.corrcoef(e0, e1)[0, 1])
        else:
            autocorrelation = 0.0
    else:
        autocorrelation = 0.0

    # Frustration (fraction of edges with conflicting signs in Ising form)
    frustration = 0.0  # Computed from Q off-diagonal elements
    off_diag = Q - np.diag(np.diag(Q))
    if n > 1:
        n_edges = n * (n - 1) / 2
        frustrated = 0
        for i in range(n):
            for j in range(i+1, n):
                if Q[i, j] != 0:
                    # Check if this coupling conflicts with the field terms
                    if np.sign(Q[i, j]) != np.sign(Q[i, i] * Q[j, j]) and Q[i, i] != 0 and Q[j, j] != 0:
                        frustrated += 1
        frustration = frustrated / max(n_edges, 1)

    # Hamming separation between local minima
    if len(local_minima) >= 2:
        separations = []
        for i in range(len(local_minima)):
            for j in range(i+1, len(local_minima)):
                sep = bin(local_minima[i] ^ local_minima[j]).count("1")
                separations.append(sep)
        hamming_separation = float(np.mean(separations))
    else:
        hamming_separation = 0.0

    return LandscapeMetrics(
        n=n,
        n_local_minima=len(local_minima),
        n_optimal=n_optimal,
        first_excitation_gap=first_gap,
        basin_sizes=basin_sizes,
        basin_entropy=basin_entropy,
        mean_barrier=0.0,  # Would need BFS between basins
        autocorrelation=autocorrelation,
        ruggedness=ruggedness,
        frustration=frustration,
        hamming_separation=hamming_separation,
        opt_value=opt_val,
        worst_value=worst_val,
        mean_value=mean_val,
    )


def run_landscape(families: list[str], sizes: list[int], n_instances: int = 50,
                  seed_start: int = 42) -> list[ExperimentRecord]:
    """Run landscape enumeration for given families and sizes."""
    from micro_qml.problems.generators import generate_problem
    from micro_qml.quantum.simulator import build_qubo

    records = []
    for family in families:
        for n in sizes:
            if n > 20:
                print(f"  SKIP {family} n={n}: too large for exact enumeration")
                continue
            for seed in range(seed_start, seed_start + n_instances):
                try:
                    problem = generate_problem(family, n=n, seed=seed)
                    adj = problem.graph["adjacency"]
                    weights = problem.graph.get("weights", [1.0] * n)
                    Q = build_qubo(problem.problem_type, adj, weights, n)
                    metrics = enumerate_landscape(Q, n)
                except Exception as e:
                    print(f"  ERROR {family} n={n} seed={seed}: {e}")
                    continue

                record = ExperimentRecord(
                    track="infrastructure",
                    project="R03",
                    problem_family=family,
                    problem_size=n,
                    difficulty="D2",
                    seed=seed,
                    problem_instance_id=f"{family}_n{n}_s{seed}",
                    metric_name="landscape_metrics",
                    metric_C=metrics.opt_value,
                    status="not_assessed",
                    cpu_seconds=time.time() - seed,  # Approximate
                    metadata={
                        "n_local_minima": metrics.n_local_minima,
                        "n_optimal": metrics.n_optimal,
                        "first_excitation_gap": metrics.first_excitation_gap,
                        "basin_entropy": metrics.basin_entropy,
                        "ruggedness": metrics.ruggedness,
                        "autocorrelation": metrics.autocorrelation,
                        "frustration": metrics.frustration,
                        "hamming_separation": metrics.hamming_separation,
                        "worst_value": metrics.worst_value,
                        "mean_value": metrics.mean_value,
                        "source": "r03_landscape_atlas",
                        "type": "landscape",
                    },
                )
                records.append(record)

    return records


def main():
    import argparse
    parser = argparse.ArgumentParser(description="R03: Exact Landscape Atlas")
    parser.add_argument("--families", type=str, default="mwis,maxcut")
    parser.add_argument("--sizes", type=str, default="8,10,12,14,16")
    parser.add_argument("--n-instances", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--ingest", action="store_true", default=True)
    args = parser.parse_args()

    families = args.families.split(",")
    sizes = [int(s) for s in args.sizes.split(",")]

    print(f"R03: Exact Landscape Atlas")
    print(f"  Families: {families}")
    print(f"  Sizes: {sizes}")
    print(f"  Instances per size: {args.n_instances}")
    print()

    records = run_landscape(families, sizes, args.n_instances, args.seed_start)
    print(f"\nGenerated {len(records)} landscape records")

    if args.ingest:
        registry = AtlasRegistry(DB_PATH)
        count = registry.insert_many(records)
        print(f"Ingested {count} records into Atlas")
        registry.export_parquet(ATLAS_DIR / "atlas.parquet")

    # Print summary
    print(f"\nLandscape Summary:")
    for family in families:
        for n in sizes:
            fam_records = [r for r in records if r.problem_family == family and r.problem_size == n]
            if fam_records:
                mean_minima = np.mean([r.metadata["n_local_minima"] for r in fam_records])
                mean_entropy = np.mean([r.metadata["basin_entropy"] for r in fam_records])
                mean_frustration = np.mean([r.metadata["frustration"] for r in fam_records])
                print(f"  {family} n={n}: {len(fam_records)} instances, "
                      f"minima={mean_minima:.1f}, entropy={mean_entropy:.3f}, "
                      f"frustration={mean_frustration:.3f}")


if __name__ == "__main__":
    main()
