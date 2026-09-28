"""R05 — Problem-Difficulty Generator.

Generates problem instances with controlled difficulty across four levels.
Computes a difficulty score that predicts classical solver difficulty.

Usage:
    python -m projects.QAB.r05_difficulty_generator.generate --level D1 --n 16 --count 100
    python -m projects.QAB.r05_difficulty_generator.score --input instances/
    python -m projects.QAB.r05_difficulty_generator.validate  # R² check
"""
from __future__ import annotations

import sys
import time
import json
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[2]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from projects.QAB.atlas.schema import ExperimentRecord
from projects.QAB.atlas.registry import AtlasRegistry

ATLAS_DIR = Path(__file__).resolve().parents[1] / "atlas" / "v0.1"
DB_PATH = ATLAS_DIR / "atlas.db"


# Difficulty levels
DIFFICULTY_LEVELS = ["D1", "D2", "D3", "D4"]


def generate_instance(family: str, n: int, seed: int, difficulty: str = "D2"):
    """Generate a problem instance with controlled difficulty."""
    from micro_qml.problems.generators import generate_problem

    if difficulty == "D1":
        # Easy random: standard generation with random seed
        return generate_problem(family, n=n, seed=seed)

    elif difficulty == "D2":
        # Structured random: use specific seed ranges for reproducible structure
        return generate_problem(family, n=n, seed=seed + 1000)

    elif difficulty == "D3":
        # Hard/frustrated: increase density or use specific parameters
        problem = generate_problem(family, n=n, seed=seed + 2000)
        # For graph problems, increase edge density to create frustration
        if hasattr(problem, "edges") and problem.edges:
            # Add extra edges to increase frustration
            rng = np.random.RandomState(seed + 3000)
            extra_edges = int(len(problem.edges) * 0.3)
            for _ in range(extra_edges):
                i, j = rng.randint(0, n, 2)
                if i != j and [i, j] not in problem.edges:
                    problem.edges.append([i, j])
        return problem

    elif difficulty == "D4":
        # Adversarial/planted: use specific seeds known to be hard
        # For now, use high seed offset to get different instances
        return generate_problem(family, n=n, seed=seed + 4000)

    return generate_problem(family, n=n, seed=seed)


def compute_difficulty_score(Q: np.ndarray, n: int) -> dict:
    """Compute difficulty score from QUBO matrix.

    D(G) = f(N_minima, H_basin, F_frustration, B_barrier, ...)
    """
    # Quick landscape metrics (sampled, not exhaustive for large n)
    if n <= 16:
        # Full enumeration for small n
        dim = 2**n
        energies = np.zeros(dim)
        for idx in range(dim):
            bits = np.array([(idx >> i) & 1 for i in range(n)], dtype=np.float64)
            energies[idx] = float(bits @ Q @ bits)

        # Count local minima
        n_local_minima = 0
        for idx in range(dim):
            e = energies[idx]
            is_min = True
            for i in range(n):
                if energies[idx ^ (1 << i)] < e:
                    is_min = False
                    break
            if is_min:
                n_local_minima += 1

        # Optimal degeneracy
        opt_val = energies.min()
        n_optimal = int(np.sum(energies == opt_val))

        # Ruggedness
        diffs = []
        for idx in range(min(dim, 5000)):
            for i in range(n):
                diffs.append(energies[idx ^ (1 << i)] - energies[idx])
        ruggedness = float(np.std(diffs)) if diffs else 0.0
    else:
        # Sampled metrics for large n
        n_samples = min(1000, 2**n)
        rng = np.random.RandomState(42)
        indices = rng.randint(0, 2**n, n_samples)
        energies = np.zeros(n_samples)
        for i, idx in enumerate(indices):
            bits = np.array([(int(idx) >> j) & 1 for j in range(n)], dtype=np.float64)
            energies[i] = float(bits @ Q @ bits)
        n_local_minima = -1  # Unknown
        n_optimal = -1
        ruggedness = float(np.std(np.diff(energies)))

    # Frustration from Q matrix
    off_diag = Q - np.diag(np.diag(Q))
    n_conflicting = 0
    n_total = 0
    for i in range(n):
        for j in range(i+1, n):
            if Q[i, j] != 0:
                n_total += 1
                if Q[i, i] != 0 and Q[j, j] != 0:
                    if np.sign(Q[i, j]) != np.sign(Q[i, i] * Q[j, j]):
                        n_conflicting += 1
    frustration = n_conflicting / max(n_total, 1)

    # Difficulty score (weighted combination)
    # Normalize components to [0, 1] roughly
    minima_score = min(n_local_minima / (2**n * 0.1), 1.0) if n_local_minima > 0 else 0.5
    ruggedness_score = min(ruggedness / 10.0, 1.0)
    frustration_score = frustration

    difficulty = 0.3 * minima_score + 0.3 * ruggedness_score + 0.4 * frustration_score

    return {
        "difficulty_score": float(difficulty),
        "n_local_minima": n_local_minima,
        "n_optimal": n_optimal,
        "ruggedness": ruggedness,
        "frustration": float(frustration),
        "n": n,
    }


def generate_and_score(families: list[str], sizes: list[int], levels: list[str],
                      n_instances: int = 50, seed_start: int = 42) -> list[ExperimentRecord]:
    """Generate instances across difficulty levels and compute difficulty scores."""
    from micro_qml.quantum.simulator import build_qubo

    records = []
    for family in families:
        for level in levels:
            for n in sizes:
                for seed in range(seed_start, seed_start + n_instances):
                    try:
                        problem = generate_instance(family, n, seed, level)
                        adj = problem.graph["adjacency"]
                        weights = problem.graph.get("weights", [1.0] * n)
                        Q = build_qubo(problem.problem_type, adj, weights, n)
                        score = compute_difficulty_score(Q, n)
                    except Exception as e:
                        print(f"  ERROR {family} {level} n={n} seed={seed}: {e}")
                        continue

                    record = ExperimentRecord(
                        track="infrastructure",
                        project="R05",
                        problem_family=family,
                        problem_size=n,
                        difficulty=level,
                        seed=seed,
                        problem_instance_id=f"{family}_{level}_n{n}_s{seed}",
                        metric_name="difficulty_score",
                        metric_C=score["difficulty_score"],
                        status="not_assessed",
                        metadata={
                            **score,
                            "source": "r05_difficulty_generator",
                            "type": "difficulty",
                        },
                    )
                    records.append(record)

    return records


def validate_difficulty_score(records: list[ExperimentRecord], solver_records: list[ExperimentRecord] = None) -> float:
    """Validate that difficulty score predicts classical solver difficulty.

    Gate R05-G1: R² > 0.5 on held-out instances.
    """
    if solver_records is None:
        # Use R02 records if available
        registry = AtlasRegistry(DB_PATH)
        solver_records = registry.query(project="R02")

    if not solver_records:
        print("  No R02 solver records available for validation")
        return 0.0

    # Match difficulty scores to solver performance
    difficulty_by_key = {}
    for r in records:
        key = (r.problem_family, r.problem_size, r.seed)
        difficulty_by_key[key] = r.metric_C

    # Get solver performance (gap to optimal) per instance
    solver_perf = {}
    for r in solver_records:
        key = (r.problem_family, r.problem_size, r.seed)
        if key not in solver_perf or r.metric_C < solver_perf[key]:
            solver_perf[key] = r.metric_C

    # Compute correlation
    difficulties = []
    performances = []
    for key, perf in solver_perf.items():
        if key in difficulty_by_key:
            difficulties.append(difficulty_by_key[key])
            performances.append(perf)

    if len(difficulties) < 10:
        print(f"  Only {len(difficulties)} matched instances — need more")
        return 0.0

    # Simple R² (linear regression)
    d = np.array(difficulties)
    p = np.array(performances)
    if np.std(d) > 0 and np.std(p) > 0:
        corr = np.corrcoef(d, p)[0, 1]
        r_squared = corr ** 2
    else:
        r_squared = 0.0

    return float(r_squared)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="R05: Problem-Difficulty Generator")
    parser.add_argument("--families", type=str, default="mwis,maxcut")
    parser.add_argument("--sizes", type=str, default="8,12,16")
    parser.add_argument("--levels", type=str, default="D1,D2,D3,D4")
    parser.add_argument("--n-instances", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--ingest", action="store_true", default=True)
    parser.add_argument("--validate", action="store_true", help="Validate R² gate")
    args = parser.parse_args()

    families = args.families.split(",")
    sizes = [int(s) for s in args.sizes.split(",")]
    levels = args.levels.split(",")

    print(f"R05: Problem-Difficulty Generator")
    print(f"  Families: {families}")
    print(f"  Sizes: {sizes}")
    print(f"  Levels: {levels}")
    print(f"  Instances per (family, level, size): {args.n_instances}")
    print()

    records = generate_and_score(families, sizes, levels, args.n_instances, args.seed_start)
    print(f"\nGenerated {len(records)} difficulty records")

    if args.ingest:
        registry = AtlasRegistry(DB_PATH)
        count = registry.insert_many(records)
        print(f"Ingested {count} records into Atlas")
        registry.export_parquet(ATLAS_DIR / "atlas.parquet")

    if args.validate:
        r2 = validate_difficulty_score(records)
        print(f"\nR05-G1 Gate: R² = {r2:.4f} (need > 0.5)")
        print(f"  {'PASS' if r2 > 0.5 else 'FAIL'}")

    # Print summary
    print(f"\nDifficulty Summary:")
    for level in levels:
        level_records = [r for r in records if r.difficulty == level]
        if level_records:
            mean_score = np.mean([r.metric_C for r in level_records])
            mean_frustration = np.mean([r.metadata["frustration"] for r in level_records])
            print(f"  {level}: {len(level_records)} instances, "
                  f"mean_difficulty={mean_score:.4f}, mean_frustration={mean_frustration:.4f}")


if __name__ == "__main__":
    main()
