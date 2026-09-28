"""Micro-QML quantum simulation: QAOA/VQE on small cores (up to 12 qubits).

This is Layer 4 of the WestQuant Micro-QML architecture:
    H_i → Micro-QML → Q(H_i)

For each hard core, we:
1. Build a QUBO formulation of the subproblem
2. Run QAOA (Quantum Approximate Optimization Algorithm) with p=1-3 layers
3. Extract quantum features (expectation values, amplitudes, measurement stats)
4. Compare quantum vs classical feature quality

Simulations run locally up to 12 qubits using:
- Exact statevector simulation (small cores ≤ 8 qubits)
- Sampling-based simulation (larger cores ≤ 12 qubits)
"""
from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class QuantumResult:
    """Result of a quantum simulation on a core."""
    core_id: str
    problem_type: str
    n_qubits: int
    method: str  # "qaoa_exact", "qaoa_sampled", "vqe"
    optimal_value: float  # best objective found
    optimal_assignment: List[int]  # best bitstring
    quantum_features: Dict[str, float]  # features for ML
    measurement_probs: Dict[str, float]  # bitstring → probability
    expectation_value: float  # <ψ|H|ψ>
    approximation_ratio: float  # optimal_value / classical_optimal
    n_shots: int = 0
    time_s: float = 0.0
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# QUBO formulations for each problem type
# ---------------------------------------------------------------------------

def build_qubo_balanced_partition(adj: np.ndarray, n: int, penalty: float = 10.0) -> np.ndarray:
    """QUBO for balanced graph partitioning (minimum bisection).
    
    Objective: minimize cut weight
    Constraint: |V1| = |V2| (balance)
    
    Q_ij where x_i ∈ {0,1}, 0=V1, 1=V2:
    - Cut weight: Σ w_ij * (x_i + x_j - 2*x_i*x_j) for edges
    - Balance: penalty * (Σ x_i - n/2)^2
    """
    Q = np.zeros((n, n))
    
    # Cut weight (minimize edges crossing)
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i][j] > 0:
                Q[i][i] += adj[i][j]
                Q[j][j] += adj[i][j]
                Q[i][j] -= 2 * adj[i][j]
    
    # Balance constraint
    for i in range(n):
        Q[i][i] += penalty * (1 - n / 2)  # diagonal
        for j in range(i + 1, n):
            Q[i][j] += penalty  # off-diagonal
    
    return Q


def build_qubo_mwis(adj: np.ndarray, weights: List[float], n: int, penalty: float = 10.0) -> np.ndarray:
    """QUBO for Maximum Weighted Independent Set.
    
    Maximize Σ w_i * x_i
    Subject to: x_i + x_j ≤ 1 for all edges (i,j)
    
    As minimization: minimize -Σ w_i * x_i + penalty * Σ_{(i,j)} x_i * x_j
    """
    Q = np.zeros((n, n))
    
    # Objective: maximize weights (minimize negative)
    for i in range(n):
        Q[i][i] -= weights[i]
    
    # Penalty for adjacent vertices both selected
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i][j] > 0:
                Q[i][j] += penalty
    
    return Q


def build_qubo_maxcut(adj: np.ndarray, n: int) -> np.ndarray:
    """QUBO for MaxCut.
    
    Maximize Σ w_ij * (x_i + x_j - 2*x_i*x_j)
    As minimization: minimize -Σ w_ij * (x_i + x_j - 2*x_i*x_j)
    """
    Q = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i][j] > 0:
                Q[i][i] -= adj[i][j]
                Q[j][j] -= adj[i][j]
                Q[i][j] += 2 * adj[i][j]
    
    return Q


def build_qubo_min_vertex_cover(adj: np.ndarray, n: int, penalty: float = 10.0) -> np.ndarray:
    """QUBO for Minimum Vertex Cover.
    
    Minimize Σ x_i
    Subject to: x_i + x_j ≥ 1 for all edges (i,j)
    
    As minimization: minimize Σ x_i + penalty * Σ_{(i,j)} (1 - x_i - x_j + x_i*x_j)
    """
    Q = np.zeros((n, n))
    
    # Objective: minimize number of selected vertices
    for i in range(n):
        Q[i][i] += 1.0
    
    # Penalty for uncovered edges
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i][j] > 0:
                Q[i][i] -= penalty
                Q[j][j] -= penalty
                Q[i][j] += penalty
    
    return Q


def build_qubo_graph_coloring(adj: np.ndarray, n: int, k: int, penalty: float = 10.0) -> np.ndarray:
    """QUBO for graph coloring with k colors.
    
    Variables: x_{i,c} = 1 if vertex i has color c
    Constraints:
    - Each vertex has exactly one color: Σ_c x_{i,c} = 1
    - No adjacent vertices share a color: x_{i,c} * x_{j,c} = 0 for edges
    
    QUBO size: n * k
    """
    size = n * k
    Q = np.zeros((size, size))
    
    # One color per vertex
    for i in range(n):
        for c1 in range(k):
            idx1 = i * k + c1
            Q[idx1][idx1] += penalty
            for c2 in range(c1 + 1, k):
                idx2 = i * k + c2
                Q[idx1][idx2] += penalty
    
    # No adjacent same color
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i][j] > 0:
                for c in range(k):
                    idx1 = i * k + c
                    idx2 = j * k + c
                    Q[idx1][idx2] += penalty
    
    return Q


def build_qubo(problem_type: str, adj: np.ndarray, weights: List[float], n: int, **kwargs) -> np.ndarray:
    """Build QUBO matrix for a problem type."""
    if problem_type == "balanced_partition":
        return build_qubo_balanced_partition(adj, n, kwargs.get("penalty", 10.0))
    elif problem_type == "mwis":
        return build_qubo_mwis(adj, weights, n, kwargs.get("penalty", 10.0))
    elif problem_type == "maxcut":
        return build_qubo_maxcut(adj, n)
    elif problem_type == "min_vertex_cover":
        return build_qubo_min_vertex_cover(adj, n, kwargs.get("penalty", 10.0))
    elif problem_type == "graph_coloring":
        return build_qubo_graph_coloring(adj, n, kwargs.get("k_colors", 3), kwargs.get("penalty", 10.0))
    elif problem_type == "community_detection":
        return build_qubo_balanced_partition(adj, n, kwargs.get("penalty", 10.0))
    else:
        raise ValueError(f"Unknown problem type: {problem_type}")


# ---------------------------------------------------------------------------
# QAOA simulation (exact statevector)
# ---------------------------------------------------------------------------

def qaoa_exact(Q: np.ndarray, n: int, p: int = 2, n_iter: int = 100, seed: int = 42) -> Dict:
    """Run QAOA with exact statevector simulation.
    
    For small n (≤ 12), we can simulate the full 2^n statevector.
    
    Args:
        Q: QUBO matrix
        n: number of qubits
        p: QAOA depth
        n_iter: optimization iterations for parameters
        seed: random seed
    
    Returns:
        Dict with optimal_value, optimal_assignment, measurement_probs, expectation_value
    """
    rng = np.random.RandomState(seed)
    dim = 2 ** n
    
    # Build Hamiltonian H = Σ Q_ij * z_i * z_j (as diagonal matrix)
    hamiltonian = np.zeros(dim)
    for state in range(dim):
        bits = [(state >> i) & 1 for i in range(n)]
        energy = 0.0
        for i in range(n):
            for j in range(n):
                if i == j:
                    energy += Q[i][i] * bits[i]
                elif i < j:
                    energy += Q[i][j] * bits[i] * bits[j]
        hamiltonian[state] = energy
    
    # Cost Hamiltonian as diagonal
    H_C = np.diag(hamiltonian)
    
    # Mixer Hamiltonian: H_M = Σ X_i
    H_M = np.zeros((dim, dim), dtype=complex)
    for i in range(n):
        for state in range(dim):
            flipped = state ^ (1 << i)
            H_M[flipped][state] += 1.0
    
    # Initial state: |+>^n
    plus = np.array([1, 1]) / np.sqrt(2)
    psi0 = np.ones(dim, dtype=complex) / np.sqrt(dim)
    
    # Optimize QAOA parameters
    best_energy = float('inf')
    best_state = 0
    best_params = None
    
    def run_qaoa(gamma, beta):
        """Run QAOA circuit with given parameters."""
        psi = psi0.copy()
        
        for layer in range(p):
            # Apply e^{-i * gamma * H_C}
            psi = np.exp(-1j * gamma[layer] * hamiltonian) * psi
            
            # Apply e^{-i * beta * H_M}
            # H_M is sum of X_i, so e^{-i*beta*H_M} = prod e^{-i*beta*X_i}
            for i in range(n):
                new_psi = psi.copy()
                for state in range(dim):
                    flipped = state ^ (1 << i)
                    c = np.cos(beta[layer])
                    s = -1j * np.sin(beta[layer])
                    psi[state] = c * new_psi[state] + s * new_psi[flipped]
                    psi[flipped] = s * new_psi[state] + c * new_psi[flipped]
        
        # Compute expectation
        probs = np.abs(psi) ** 2
        energy = np.sum(probs * hamiltonian)
        
        return energy, probs
    
    # Grid search + random search for parameters
    for _ in range(n_iter):
        gamma = rng.uniform(0, 2 * np.pi, p)
        beta = rng.uniform(0, np.pi, p)
        
        energy, probs = run_qaoa(gamma, beta)
        
        if energy < best_energy:
            best_energy = energy
            best_state = int(np.argmax(probs))
            best_params = (gamma, beta)
            best_probs = probs
    
    # Local refinement
    if best_params is not None:
        gamma, beta = best_params
        for _ in range(n_iter):
            # Perturb
            new_gamma = gamma + rng.uniform(-0.1, 0.1, p)
            new_beta = beta + rng.uniform(-0.1, 0.1, p)
            energy, probs = run_qaoa(new_gamma, new_beta)
            if energy < best_energy:
                best_energy = energy
                best_state = int(np.argmax(probs))
                gamma, beta = new_gamma, new_beta
                best_probs = probs
    
    # Extract features
    bits = [(best_state >> i) & 1 for i in range(n)]
    
    # Top-k measurement probabilities
    top_k = 8
    top_indices = np.argsort(best_probs)[::-1][:top_k]
    measurement_probs = {
        format(idx, f'0{n}b'): float(best_probs[idx])
        for idx in top_indices
    }
    
    # Quantum features for ML
    features = {
        "expectation_value": float(best_energy),
        "optimal_bitstring_entropy": float(-np.sum(best_probs * np.log(best_probs + 1e-10))),
        "top1_probability": float(best_probs[best_state]),
        "top2_probability": float(sorted(best_probs, reverse=True)[1]) if n > 1 else 0.0,
        "energy_variance": float(np.sum(best_probs * (hamiltonian - best_energy) ** 2)),
        "n_local_minima": int(np.sum([
            1 for s in range(dim)
            if all(hamiltonian[s] <= hamiltonian[s ^ (1 << i)] for i in range(n))
        ])),
    }
    
    return {
        "optimal_value": float(best_energy),
        "optimal_assignment": bits,
        "measurement_probs": measurement_probs,
        "expectation_value": float(best_energy),
        "quantum_features": features,
        "best_params": best_params,
    }


# ---------------------------------------------------------------------------
# Classical baseline (greedy + random)
# ---------------------------------------------------------------------------

def classical_solve_qubo(Q: np.ndarray, n: int, n_samples: int = 1000, seed: int = 42) -> Dict:
    """Classical baseline: random search + greedy local search."""
    rng = np.random.RandomState(seed)
    
    best_energy = float('inf')
    best_bits = None
    
    for _ in range(n_samples):
        # Random initial
        bits = rng.randint(0, 2, n)
        
        # Greedy local search
        improved = True
        while improved:
            improved = False
            for i in range(n):
                bits[i] = 1 - bits[i]
                energy = _eval_qubo(Q, bits)
                if energy < best_energy:
                    best_energy = energy
                    best_bits = bits.copy()
                    improved = True
                else:
                    bits[i] = 1 - bits[i]
        
        if best_bits is None:
            energy = _eval_qubo(Q, bits)
            if energy < best_energy:
                best_energy = energy
                best_bits = bits.copy()
    
    return {
        "optimal_value": float(best_energy),
        "optimal_assignment": best_bits.tolist(),
        "method": "greedy_random",
    }


def _eval_qubo(Q: np.ndarray, bits: np.ndarray) -> float:
    """Evaluate QUBO for a bit assignment."""
    return float(bits @ Q @ bits)


# ---------------------------------------------------------------------------
# Full Micro-QML simulation
# ---------------------------------------------------------------------------

def simulate_core(core, classical_optimal: float, p: int = 2, seed: int = 42) -> QuantumResult:
    """Run quantum simulation on a core.
    
    Args:
        core: Core object from classical reducer
        classical_optimal: Known classical optimal value
        p: QAOA depth
        seed: Random seed
    
    Returns:
        QuantumResult with quantum features
    """
    n = core.n
    adj = core.subgraph["adjacency"]
    weights = core.subgraph["weights"]
    
    t0 = time.time()
    
    # Build QUBO
    Q = build_qubo(core.problem_type, adj, weights, n)
    
    # Run QAOA
    if n <= 12:
        qaoa_result = qaoa_exact(Q, n, p=p, n_iter=200, seed=seed)
    else:
        # Fallback to classical for large cores
        qaoa_result = classical_solve_qubo(Q, n, seed=seed)
        qaoa_result["quantum_features"] = {}
        qaoa_result["measurement_probs"] = {}
        qaoa_result["expectation_value"] = qaoa_result["optimal_value"]
    
    # Also run classical baseline
    classical_result = classical_solve_qubo(Q, n, seed=seed)
    
    # Approximation ratio
    approx_ratio = qaoa_result["optimal_value"] / max(abs(classical_optimal), 1e-10)
    
    dt = time.time() - t0
    
    return QuantumResult(
        core_id=core.core_id,
        problem_type=core.problem_type,
        n_qubits=n,
        method=f"qaoa_exact_p{p}" if n <= 12 else "classical",
        optimal_value=qaoa_result["optimal_value"],
        optimal_assignment=qaoa_result["optimal_assignment"],
        quantum_features=qaoa_result.get("quantum_features", {}),
        measurement_probs=qaoa_result.get("measurement_probs", {}),
        expectation_value=qaoa_result.get("expectation_value", 0.0),
        approximation_ratio=approx_ratio,
        n_shots=0,
        time_s=dt,
        metadata={
            "classical_baseline": classical_result["optimal_value"],
            "classical_optimal": classical_optimal,
            "qaoa_depth": p,
        },
    )


def simulate_all_cores(cores: List, classical_optimal: float, p: int = 2, seed: int = 42) -> List[QuantumResult]:
    """Run quantum simulation on all quantum-eligible cores."""
    results = []
    for core in cores:
        if not core.quantum_eligible:
            continue
        result = simulate_core(core, classical_optimal, p=p, seed=seed)
        results.append(result)
    return results
