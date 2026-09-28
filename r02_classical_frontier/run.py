"""R02 — Classical Frontier.

Establishes the strongest classical performance for each problem family and size.
No quantum result may be classified QA1 until it beats this frontier.

Usage:
    python -m projects.QAB.r02_classical_frontier.run --sizes 8,12,16,20,32
    python -m projects.QAB.r02_classical_frontier.run --families mwis,maxcut --sizes 8,16
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure westquant root is on path
BASE = Path(__file__).resolve().parents[2]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import numpy as np

from projects.QAB.atlas.schema import ExperimentRecord
from projects.QAB.atlas.registry import AtlasRegistry
from projects.QAB.r04_resource_accounting import ResourceRecord

ATLAS_DIR = Path(__file__).resolve().parents[1] / "atlas" / "v0.1"
DB_PATH = ATLAS_DIR / "atlas.db"


# Problem families supported by existing generators
PROBLEM_FAMILIES = ["mwis", "maxcut", "min_vertex_cover", "graph_coloring", "tsp"]


def generate_problem(family: str, n: int, seed: int):
    """Generate a problem instance using existing generators."""
    from micro_qml.problems.generators import generate_problem
    return generate_problem(family, n=n, seed=seed)


def problem_to_qubo(problem) -> np.ndarray:
    """Convert a ProblemInstance to QUBO matrix."""
    from micro_qml.quantum.simulator import build_qubo
    adj = problem.graph["adjacency"]
    weights = problem.graph.get("weights", [1.0] * problem.n)
    return build_qubo(problem.problem_type, adj, weights, problem.n)


def solve_exact(Q: np.ndarray, n: int) -> tuple[int, float, float]:
    """Exact enumeration. Returns (best_bits, best_value, time_s)."""
    t0 = time.time()
    if n > 22:
        return 0, float("inf"), time.time() - t0
    best_val = float("inf")
    best_bits = 0
    for idx in range(2**n):
        bits = np.array([(idx >> i) & 1 for i in range(n)], dtype=np.float64)
        val = float(bits @ Q @ bits)
        if val < best_val:
            best_val = val
            best_bits = idx
    return best_bits, best_val, time.time() - t0


def solve_greedy(Q: np.ndarray, n: int, seed: int = 42) -> tuple[int, float, float]:
    """Greedy: start from all-zero, flip bits that improve."""
    t0 = time.time()
    rng = np.random.RandomState(seed)
    bits = np.zeros(n, dtype=np.float64)
    val = float(bits @ Q @ bits)
    improved = True
    while improved:
        improved = False
        order = rng.permutation(n)
        for i in order:
            bits[i] = 1 - bits[i]
            new_val = float(bits @ Q @ bits)
            if new_val < val:
                val = new_val
                improved = True
            else:
                bits[i] = 1 - bits[i]
    bits_int = int("".join(str(int(b)) for b in bits[::-1]), 2)
    return bits_int, val, time.time() - t0


def solve_multistart(Q: np.ndarray, n: int, n_restarts: int = 20, seed: int = 42) -> tuple[int, float, float]:
    """Multi-start greedy from random initializations."""
    t0 = time.time()
    rng = np.random.RandomState(seed)
    best_val = float("inf")
    best_bits = 0
    for _ in range(n_restarts):
        bits = rng.randint(0, 2, n).astype(np.float64)
        val = float(bits @ Q @ bits)
        improved = True
        while improved:
            improved = False
            for i in range(n):
                bits[i] = 1 - bits[i]
                new_val = float(bits @ Q @ bits)
                if new_val < val:
                    val = new_val
                    improved = True
                else:
                    bits[i] = 1 - bits[i]
        if val < best_val:
            best_val = val
            best_bits = int("".join(str(int(b)) for b in bits[::-1]), 2)
    return best_bits, best_val, time.time() - t0


def solve_sa(Q: np.ndarray, n: int, n_iter: int = 5000, seed: int = 42) -> tuple[int, float, float]:
    """Simulated annealing."""
    t0 = time.time()
    rng = np.random.RandomState(seed)
    bits = rng.randint(0, 2, n).astype(np.float64)
    val = float(bits @ Q @ bits)
    best_val = val
    best_bits = bits.copy()
    T = 2.0
    for it in range(n_iter):
        i = rng.randint(n)
        bits[i] = 1 - bits[i]
        new_val = float(bits @ Q @ bits)
        delta = new_val - val
        if delta < 0 or rng.random() < np.exp(-delta / max(T, 1e-10)):
            val = new_val
            if val < best_val:
                best_val = val
                best_bits = bits.copy()
        else:
            bits[i] = 1 - bits[i]
        T *= 0.999
    bits_int = int("".join(str(int(b)) for b in best_bits[::-1]), 2)
    return bits_int, best_val, time.time() - t0


def solve_tabu(Q: np.ndarray, n: int, max_iter: int = 1000, seed: int = 42) -> tuple[int, float, float]:
    """Tabu search."""
    t0 = time.time()
    rng = np.random.RandomState(seed)
    bits = rng.randint(0, 2, n).astype(np.float64)
    val = float(bits @ Q @ bits)
    best_val = val
    best_bits = bits.copy()
    tabu = set()
    tabu_size = min(10, n)
    for it in range(max_iter):
        best_neighbor_val = float("inf")
        best_flip = -1
        for i in range(n):
            if i in tabu:
                continue
            bits[i] = 1 - bits[i]
            nval = float(bits @ Q @ bits)
            if nval < best_neighbor_val:
                best_neighbor_val = nval
                best_flip = i
            bits[i] = 1 - bits[i]
        if best_flip == -1:
            break
        bits[best_flip] = 1 - bits[best_flip]
        val = best_neighbor_val
        if val < best_val:
            best_val = val
            best_bits = bits.copy()
        tabu.add(best_flip)
        if len(tabu) > tabu_size:
            tabu.pop()
    bits_int = int("".join(str(int(b)) for b in best_bits[::-1]), 2)
    return bits_int, best_val, time.time() - t0


SOLVERS = {
    "exact": solve_exact,
    "greedy": solve_greedy,
    "multistart": solve_multistart,
    "sa": solve_sa,
    "tabu": solve_tabu,
}


def run_frontier(families: list[str], sizes: list[int], n_instances: int = 10,
                 seed_start: int = 42) -> list[ExperimentRecord]:
    """Run classical frontier for given families and sizes."""
    records = []
    for family in families:
        for n in sizes:
            for seed in range(seed_start, seed_start + n_instances):
                try:
                    problem = generate_problem(family, n, seed)
                    Q = problem_to_qubo(problem)
                except Exception as e:
                    print(f"  SKIP {family} n={n} seed={seed}: {e}")
                    continue

                for solver_name, solver_fn in SOLVERS.items():
                    if solver_name == "exact" and n > 22:
                        continue
                    try:
                        t0 = time.time()
                        if solver_name == "exact":
                            best_bits, best_val, solve_time = solver_fn(Q, n)
                        else:
                            best_bits, best_val, solve_time = solver_fn(Q, n, seed=seed)
                        wall = time.time() - t0
                    except Exception as e:
                        print(f"  ERROR {solver_name} {family} n={n} seed={seed}: {e}")
                        continue

                    record = ExperimentRecord(
                        track="infrastructure",
                        project="R02",
                        problem_family=family,
                        problem_size=n,
                        difficulty="D2",
                        seed=seed,
                        problem_instance_id=f"{family}_n{n}_s{seed}",
                        classical_method=solver_name,
                        metric_name="qubo_objective",
                        metric_C=best_val,
                        cpu_seconds=solve_time,
                        status="not_assessed",
                        metadata={
                            "solver": solver_name,
                            "best_bits": best_bits,
                            "wall_time": wall,
                            "source": "r02_classical_frontier",
                        },
                    )
                    records.append(record)

    return records


def compute_frontier(records: list[ExperimentRecord]) -> dict[tuple, float]:
    """Compute M_C*(x) = best classical value per (family, size, seed)."""
    frontier = {}
    for r in records:
        key = (r.problem_family, r.problem_size, r.seed)
        if key not in frontier or r.metric_C < frontier[key]:
            frontier[key] = r.metric_C
    return frontier


def main():
    import argparse
    parser = argparse.ArgumentParser(description="R02: Classical Frontier")
    parser.add_argument("--families", type=str, default="mwis,maxcut",
                        help="Comma-separated problem families")
    parser.add_argument("--sizes", type=str, default="8,12,16,20",
                        help="Comma-separated sizes")
    parser.add_argument("--n-instances", type=int, default=10,
                        help="Number of instances per size")
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--ingest", action="store_true", default=True,
                        help="Ingest results into Atlas")
    args = parser.parse_args()

    families = args.families.split(",")
    sizes = [int(s) for s in args.sizes.split(",")]

    print(f"R02: Classical Frontier")
    print(f"  Families: {families}")
    print(f"  Sizes: {sizes}")
    print(f"  Instances per size: {args.n_instances}")
    print()

    records = run_frontier(families, sizes, args.n_instances, args.seed_start)
    print(f"\nGenerated {len(records)} records")

    # Compute frontier
    frontier = compute_frontier(records)
    print(f"Frontier computed for {len(frontier)} (family, size, seed) combinations")

    if args.ingest:
        registry = AtlasRegistry(DB_PATH)
        count = registry.insert_many(records)
        print(f"Ingested {count} records into Atlas")

        # Export
        parquet_path = ATLAS_DIR / "atlas.parquet"
        registry.export_parquet(parquet_path)

        s = registry.summary()
        print(f"\nAtlas: {s['total_records']} total records")

    # Print frontier summary
    print(f"\nClassical Frontier Summary:")
    print(f"  {'Family':<15} {'Size':<6} {'Best':<12} {'Solver':<12}")
    print(f"  {'-'*50}")
    for key, val in sorted(frontier.items()):
        family, n, seed = key
        best_solver = min(
            (r for r in records if r.problem_family == family and r.problem_size == n and r.seed == seed),
            key=lambda r: r.metric_C,
            default=None,
        )
        solver_name = best_solver.classical_method if best_solver else "?"
        print(f"  {family:<15} {n:<6} {val:<12.4f} {solver_name:<12}")


if __name__ == "__main__":
    main()
