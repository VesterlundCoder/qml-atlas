"""R12 — Recovery-Basin Sampling.

For small cores, compute exact A_r(G) and p_r(q, G) for all samplers.
This is the most promising local candidate because basin ground truth is exact.

Multi-fidelity:
  L0: n=12-20, exact basin enumeration
  L1: n=24-28, approximate basins via Monte Carlo
  L2: n=28+, MPS/tensor network for quantum state

Usage:
    python -m projects.QAB.r12_recovery_basin_sampling.run --sizes 12,16,20 --radii 0,1,2,3 --budgets 100,200,500
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parents[2]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from projects.QAB.atlas.schema import ExperimentRecord
from projects.QAB.atlas.registry import AtlasRegistry

ATLAS_DIR = Path(__file__).resolve().parents[1] / "atlas" / "v0.1"
DB_PATH = ATLAS_DIR / "atlas.db"


def compute_exact_basin(Q: np.ndarray, n: int, radius: int) -> dict:
    """Compute exact recovery basin A_r(G) for small n.

    A_r(G) = { x : E_r(R(x)) ∩ X*(G) ≠ ∅ }
    where E_r(R(x)) is the r-flip expansion of the repaired state.

    Optimized: precompute optimal states, then check each state's r-neighborhood.
    """
    dim = 2**n

    # Compute all energies
    energies = np.zeros(dim)
    for idx in range(dim):
        bits = np.array([(idx >> i) & 1 for i in range(n)], dtype=np.float64)
        energies[idx] = float(bits @ Q @ bits)

    opt_val = energies.min()
    opt_states = set(np.where(energies == opt_val)[0])

    # For each state, check if r-flip neighborhood contains an optimal state
    # Optimization: for each optimal state, mark all states within Hamming distance r
    basin = np.zeros(dim, dtype=bool)
    from itertools import combinations
    for opt in opt_states:
        # Mark the optimal state itself
        basin[opt] = True
        # Mark all states within Hamming distance r
        for r in range(1, radius + 1):
            for flip_bits in combinations(range(n), r):
                neighbor = opt
                for b in flip_bits:
                    neighbor ^= (1 << b)
                basin[neighbor] = True

    return {
        "basin_mask": basin,
        "basin_size": int(basin.sum()),
        "basin_fraction": float(basin.sum()) / dim,
        "opt_val": float(opt_val),
        "n_optimal": len(opt_states),
        "dim": dim,
    }


def _generate_flips(n: int, r: int):
    """Generate all r-element subsets of {0, ..., n-1}."""
    from itertools import combinations
    return combinations(range(n), r)


def sample_uniform_basin(basin_mask: np.ndarray, n_shots: int, seed: int) -> float:
    """Estimate p_r for uniform sampling."""
    dim = len(basin_mask)
    rng = np.random.RandomState(seed)
    samples = rng.randint(0, dim, n_shots)
    return float(np.mean(basin_mask[samples]))


def sample_greedy_basin(Q: np.ndarray, basin_mask: np.ndarray, n: int,
                         n_shots: int, seed: int) -> float:
    """Estimate p_r for greedy sampling."""
    rng = np.random.RandomState(seed)
    hits = 0
    for _ in range(n_shots):
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
        idx = int("".join(str(int(b)) for b in bits[::-1]), 2)
        if basin_mask[idx]:
            hits += 1
    return hits / n_shots


def sample_sa_basin(Q: np.ndarray, basin_mask: np.ndarray, n: int,
                     n_shots: int, seed: int, n_iter: int = 1000) -> float:
    """Estimate p_r for simulated annealing."""
    rng = np.random.RandomState(seed)
    hits = 0
    for _ in range(n_shots):
        bits = rng.randint(0, 2, n).astype(np.float64)
        val = float(bits @ Q @ bits)
        T = 2.0
        for it in range(n_iter):
            i = rng.randint(n)
            bits[i] = 1 - bits[i]
            new_val = float(bits @ Q @ bits)
            delta = new_val - val
            if delta < 0 or rng.random() < np.exp(-delta / max(T, 1e-10)):
                val = new_val
            else:
                bits[i] = 1 - bits[i]
            T *= 0.999
        idx = int("".join(str(int(b)) for b in bits[::-1]), 2)
        if basin_mask[idx]:
            hits += 1
    return hits / n_shots


def sample_qaoa_basin(Q: np.ndarray, basin_mask: np.ndarray, n: int,
                       n_shots: int, seed: int, p: int = 1) -> float:
    """Estimate p_r for QAOA sampling (simplified)."""
    # Use the R06 circuit simulator to generate samples
    from projects.QAB.r06_feature_map_scaling.run import simulate_circuit_expectations
    rng = np.random.RandomState(seed)
    hits = 0

    # Simulate QAOA state
    features = simulate_circuit_expectations(Q, n, p, "qaoa", seed)
    # Use <Z_i> to determine bitstring
    z_exp = features["z"]
    bits = (z_exp < 0).astype(float)
    idx = int("".join(str(int(b)) for b in bits[::-1]), 2)
    if basin_mask[idx]:
        hits += 1

    # Add some random samples for the rest
    for _ in range(n_shots - 1):
        sample = rng.randint(0, 2**n)
        if basin_mask[sample]:
            hits += 1

    return hits / n_shots


SAMPLERS = {
    "uniform": lambda Q, bm, n, ns, s: sample_uniform_basin(bm, ns, s),
    "greedy": sample_greedy_basin,
    "sa": sample_sa_basin,
    "qaoa_p1": lambda Q, bm, n, ns, s: sample_qaoa_basin(Q, bm, n, ns, s, p=1),
}


def run_recovery_basin(families: list[str], sizes: list[int], radii: list[int],
                       budgets: list[int], n_instances: int = 5,
                       seed_start: int = 42) -> list[ExperimentRecord]:
    """Run recovery-basin sampling experiment."""
    from micro_qml.problems.generators import generate_problem
    from micro_qml.quantum.simulator import build_qubo

    records = []

    for family in families:
        for n in sizes:
            if n > 20:
                print(f"  SKIP {family} n={n}: too large for exact basin (use L1)")
                continue
            for seed in range(seed_start, seed_start + n_instances):
                try:
                    problem = generate_problem(family, n=n, seed=seed)
                    adj = problem.graph["adjacency"]
                    weights = problem.graph.get("weights", [1.0] * n)
                    Q = build_qubo(problem.problem_type, adj, weights, n)
                except Exception as e:
                    print(f"  ERROR generating {family} n={n} seed={seed}: {e}")
                    continue

                for r in radii:
                    try:
                        t0 = time.time()
                        basin = compute_exact_basin(Q, n, r)
                        basin_time = time.time() - t0
                    except Exception as e:
                        print(f"  ERROR basin {family} n={n} r={r} seed={seed}: {e}")
                        continue

                    for budget in budgets:
                        for sampler_name, sampler_fn in SAMPLERS.items():
                            try:
                                t0 = time.time()
                                p_r = sampler_fn(Q, basin["basin_mask"], n, budget, seed)
                                sample_time = time.time() - t0

                                is_quantum = "qaoa" in sampler_name
                                # Classical baseline for delta: SA
                                if is_quantum and "sa" in SAMPLERS:
                                    p_r_sa = sample_sa_basin(Q, basin["basin_mask"], n, budget, seed)
                                    delta = p_r - p_r_sa
                                else:
                                    delta = 0.0

                                if is_quantum:
                                    if delta > 0:
                                        status = "quantum_candidate"
                                        qa = 1
                                    elif delta < 0:
                                        status = "classical_advantage"
                                        qa = 0
                                    else:
                                        status = "unresolved"
                                        qa = 0
                                else:
                                    status = "not_assessed"
                                    qa = -1

                                record = ExperimentRecord(
                                    track="quantum_sampling" if is_quantum else "infrastructure",
                                    project="R12",
                                    problem_family=family,
                                    problem_size=n,
                                    difficulty="D2",
                                    seed=seed,
                                    problem_instance_id=f"{family}_n{n}_s{seed}",
                                    quantum_method=sampler_name if is_quantum else "",
                                    qubits=n,
                                    depth=1 if "qaoa" in sampler_name else 0,
                                    shots=budget,
                                    noise_model="ideal",
                                    hardware="simulator",
                                    classical_method=sampler_name if not is_quantum else "sa",
                                    metric_name="p_r",
                                    metric_Q=p_r if is_quantum else 0.0,
                                    metric_C=p_r if not is_quantum else 0.0,
                                    delta=delta,
                                    cpu_seconds=basin_time + sample_time,
                                    status=status,
                                    qa_level=qa,
                                    metadata={
                                        "radius": r,
                                        "budget": budget,
                                        "basin_size": basin["basin_size"],
                                        "basin_fraction": basin["basin_fraction"],
                                        "n_optimal": basin["n_optimal"],
                                        "sampler": sampler_name,
                                        "source": "r12_recovery_basin_sampling",
                                    },
                                )
                                records.append(record)
                            except Exception as e:
                                print(f"  ERROR sampler {sampler_name}: {e}")

    return records


def main():
    import argparse
    parser = argparse.ArgumentParser(description="R12: Recovery-Basin Sampling")
    parser.add_argument("--families", type=str, default="mwis,maxcut")
    parser.add_argument("--sizes", type=str, default="12,16")
    parser.add_argument("--radii", type=str, default="0,1,2,3")
    parser.add_argument("--budgets", type=str, default="100,200")
    parser.add_argument("--n-instances", type=int, default=3)
    parser.add_argument("--seed-start", type=int, default=42)
    parser.add_argument("--ingest", action="store_true", default=True)
    args = parser.parse_args()

    families = args.families.split(",")
    sizes = [int(s) for s in args.sizes.split(",")]
    radii = [int(s) for s in args.radii.split(",")]
    budgets = [int(s) for s in args.budgets.split(",")]

    print(f"R12: Recovery-Basin Sampling")
    print(f"  Families: {families}")
    print(f"  Sizes: {sizes}")
    print(f"  Radii: {radii}")
    print(f"  Budgets: {budgets}")
    print(f"  Instances per size: {args.n_instances}")
    print()

    records = run_recovery_basin(families, sizes, radii, budgets, args.n_instances, args.seed_start)
    print(f"\nGenerated {len(records)} records")

    if args.ingest:
        registry = AtlasRegistry(DB_PATH)
        count = registry.insert_many(records)
        print(f"Ingested {count} records into Atlas")
        registry.export_parquet(ATLAS_DIR / "atlas.parquet")

    # Summary
    print(f"\nR12 Summary:")
    for sampler in SAMPLERS:
        s_records = [r for r in records if r.metadata.get("sampler") == sampler]
        if s_records:
            mean_p_r = np.mean([r.metric_Q or r.metric_C for r in s_records])
            print(f"  {sampler}: {len(s_records)} configs, mean p_r={mean_p_r:.4f}")


if __name__ == "__main__":
    main()
