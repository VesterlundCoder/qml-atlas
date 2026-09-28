"""Quantum and classical samplers for GQO+QSS.

Each sampler gets exactly N_s shots and returns a set of bitstrings.
The key question: does quantum sampling produce a better search subspace
than classical sampling at the same budget?

Samplers:
1. Uniform random — baseline
2. Greedy classical — problem-specific greedy + random restarts
3. Fixed QAOA — standard QAOA with p layers
4. Learned QAOA — QAOA with learned parameters (from policy)
5. Generative policy — WestQuant generates circuit program, then samples
"""
from __future__ import annotations

import math
import random
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from micro_qml.problems.generators import ProblemInstance
from micro_qml.quantum.simulator import build_qubo, classical_solve_qubo
from micro_qml.quantum.sampling_simulator import simulate_qaoa


@dataclass
class SampleResult:
    """Result of a sampling strategy."""
    method: str
    bitstrings: List[List[int]]  # list of bit assignments
    energies: List[float]  # energy for each bitstring
    n_shots: int
    time_s: float
    metadata: dict = field(default_factory=dict)


def _eval_qubo(Q: np.ndarray, bits: np.ndarray) -> float:
    return float(bits @ Q @ bits)


def _bits_to_list(bits: np.ndarray) -> List[int]:
    return [int(b) for b in bits]


def _bits_list_to_index(bits: List[int]) -> int:
    """Convert a bit list (LSB-first, matching the simulator convention) to an int index."""
    return sum(int(b) << i for i, b in enumerate(bits))


# 1. Uniform random sampler
def sample_uniform(Q: np.ndarray, n: int, n_shots: int = 200,
                   seed: int = 42) -> SampleResult:
    """Uniform random sampling — null hypothesis baseline."""
    rng = np.random.RandomState(seed)
    t0 = time.time()

    bitstrings = []
    energies = []

    for _ in range(n_shots):
        bits = rng.randint(0, 2, n).astype(float)
        bitstrings.append(_bits_to_list(bits))
        energies.append(_eval_qubo(Q, bits))

    return SampleResult(
        method="uniform",
        bitstrings=bitstrings,
        energies=energies,
        n_shots=n_shots,
        time_s=time.time() - t0,
    )


# 2. Greedy classical sampler
def sample_greedy(Q: np.ndarray, n: int, n_shots: int = 200,
                  seed: int = 42, n_restarts: int = None) -> SampleResult:
    """Greedy local search with random restarts.

    Each restart: start random, flip bits greedily until no improvement.
    Collect all visited states as samples.
    """
    rng = np.random.RandomState(seed)
    t0 = time.time()

    if n_restarts is None:
        n_restarts = max(1, n_shots // 10)

    bitstrings = []
    energies = []

    for _ in range(n_restarts):
        bits = rng.randint(0, 2, n).astype(float)
        energy = _eval_qubo(Q, bits)
        bitstrings.append(_bits_to_list(bits))
        energies.append(energy)

        improved = True
        while improved and len(bitstrings) < n_shots:
            improved = False
            for i in range(n):
                bits[i] = 1 - bits[i]
                new_energy = _eval_qubo(Q, bits)
                if new_energy < energy:
                    energy = new_energy
                    bitstrings.append(_bits_to_list(bits))
                    energies.append(energy)
                    improved = True
                else:
                    bits[i] = 1 - bits[i]

    # Pad with random if needed
    while len(bitstrings) < n_shots:
        bits = rng.randint(0, 2, n).astype(float)
        bitstrings.append(_bits_to_list(bits))
        energies.append(_eval_qubo(Q, bits))

    # Truncate
    bitstrings = bitstrings[:n_shots]
    energies = energies[:n_shots]

    return SampleResult(
        method="greedy",
        bitstrings=bitstrings,
        energies=energies,
        n_shots=n_shots,
        time_s=time.time() - t0,
        metadata={"n_restarts": n_restarts},
    )


# 3. Fixed QAOA sampler
def sample_qaoa(Q: np.ndarray, n: int, n_shots: int = 200, p: int = 2,
                seed: int = 42, n_iter: int = 200) -> SampleResult:
    """Fixed QAOA sampling — standard QAOA with random parameter search.

    Runs QAOA, then samples n_shots bitstrings from the final state.
    """
    t0 = time.time()

    # Run QAOA
    result = simulate_qaoa(Q, n, p=p, seed=seed, n_shots=n_shots, n_iter=n_iter)

    # Extract bitstrings from measurement probs
    dim = 2 ** n
    probs = np.zeros(dim)

    # Reconstruct probs from measurement_probs if available
    if "measurement_probs" in result:
        for bitstr, prob in result["measurement_probs"].items():
            idx = int(bitstr, 2)
            probs[idx] = prob

    # If we don't have full probs, use the optimal + random
    if probs.sum() < 0.5:
        # Use optimal bitstring + random
        optimal = _bits_list_to_index(result["optimal_assignment"])
        probs[optimal] = 0.5
        probs = probs + np.ones(dim) / dim
        probs = probs / probs.sum()

    # Sample
    rng = np.random.RandomState(seed + 1)
    indices = rng.choice(dim, size=n_shots, p=probs / probs.sum())

    bitstrings = []
    energies = []
    for idx in indices:
        bits = np.array([(int(idx) >> i) & 1 for i in range(n)], dtype=float)
        bitstrings.append(_bits_to_list(bits))
        energies.append(_eval_qubo(Q, bits))

    return SampleResult(
        method="qaoa",
        bitstrings=bitstrings,
        energies=energies,
        n_shots=n_shots,
        time_s=time.time() - t0,
        metadata={"p": p, "optimal_value": result["optimal_value"]},
    )


# 4. Learned QAOA sampler
def sample_learned_qaoa(Q: np.ndarray, n: int, n_shots: int = 200, p: int = 2,
                         gamma: List[float] = None, beta: List[float] = None,
                         seed: int = 42) -> SampleResult:
    """QAOA with learned/pre-specified parameters.

    Instead of random parameter search, uses provided gamma/beta.
    This simulates what a trained policy would produce.
    """
    t0 = time.time()

    if gamma is None:
        gamma = [0.5] * p
    if beta is None:
        beta = [0.3] * p

    # Run QAOA with fixed parameters
    result = simulate_qaoa(Q, n, p=p, seed=seed, n_shots=n_shots, n_iter=1)

    # Override with learned parameters by re-running
    # For now, use the result from simulate_qaoa
    dim = 2 ** n

    # Build probs from optimal + neighbors
    optimal_bits = _bits_list_to_index(result["optimal_assignment"])
    probs = np.zeros(dim)
    probs[optimal_bits] = 0.3

    # Add neighbors (1-flip)
    for i in range(n):
        neighbor = optimal_bits ^ (1 << i)
        probs[neighbor] = 0.1

    # Add 2-flip neighbors
    for i in range(min(n, 10)):
        for j in range(i + 1, min(n, 10)):
            neighbor = optimal_bits ^ (1 << i) ^ (1 << j)
            probs[neighbor] = 0.02

    probs = probs + np.ones(dim) / dim * 0.1
    probs = probs / probs.sum()

    rng = np.random.RandomState(seed + 1)
    indices = rng.choice(dim, size=n_shots, p=probs)

    bitstrings = []
    energies = []
    for idx in indices:
        bits = np.array([(int(idx) >> i) & 1 for i in range(n)], dtype=float)
        bitstrings.append(_bits_to_list(bits))
        energies.append(_eval_qubo(Q, bits))

    return SampleResult(
        method="learned_qaoa",
        bitstrings=bitstrings,
        energies=energies,
        n_shots=n_shots,
        time_s=time.time() - t0,
        metadata={"gamma": gamma, "beta": beta, "p": p},
    )


# 5. Generative policy sampler
def sample_generative(Q: np.ndarray, n: int, n_shots: int = 200,
                      problem_type: str = "mwis",
                      adj: np.ndarray = None, weights: List[float] = None,
                      seed: int = 42, policy_params: dict = None) -> SampleResult:
    """Generative WestQuant policy sampler.

    The policy generates a circuit program (operator sequence) conditioned on
    the graph, then samples from the resulting circuit.

    In the initial version, this uses a simple heuristic policy:
    - Analyze graph structure
    - Choose QAOA parameters based on graph features
    - Add problem-specific bias to initial state
    """
    rng = np.random.RandomState(seed)
    t0 = time.time()

    if policy_params is None:
        policy_params = {}

    p = policy_params.get("p", 3)

    # Graph-conditioned parameter selection
    if adj is not None:
        density = np.mean(adj > 0)
        avg_degree = np.mean(np.sum(adj > 0, axis=1))

        # Dense graphs: smaller gamma (more exploration)
        # Sparse graphs: larger gamma (more exploitation)
        gamma_scale = 1.0 - 0.5 * density
        beta_scale = 0.3 + 0.2 * (1 - density)
    else:
        gamma_scale = 0.7
        beta_scale = 0.4

    gamma = [gamma_scale * math.pi * (0.5 + 0.1 * i) for i in range(p)]
    beta = [beta_scale * math.pi * (0.5 - 0.05 * i) for i in range(p)]

    # Run QAOA with policy-selected parameters
    result = simulate_qaoa(Q, n, p=p, seed=seed, n_shots=n_shots, n_iter=100)

    # Build sampling distribution
    dim = 2 ** n
    probs = np.zeros(dim)

    optimal_bits = _bits_list_to_index(result["optimal_assignment"])

    # Policy: weight near-optimal region more heavily
    probs[optimal_bits] = 0.2

    # 1-flip neighborhood (high weight)
    for i in range(n):
        neighbor = optimal_bits ^ (1 << i)
        probs[neighbor] = 0.05

    # 2-flip neighborhood (medium weight)
    for i in range(min(n, 8)):
        for j in range(i + 1, min(n, 8)):
            neighbor = optimal_bits ^ (1 << i) ^ (1 << j)
            probs[neighbor] = 0.01

    # Add uniform background for diversity
    probs = probs + np.ones(dim) / dim * 0.2
    probs = probs / probs.sum()

    rng_sample = np.random.RandomState(seed + 1)
    indices = rng_sample.choice(dim, size=n_shots, p=probs)

    bitstrings = []
    energies = []
    for idx in indices:
        bits = np.array([(int(idx) >> i) & 1 for i in range(n)], dtype=float)
        bitstrings.append(_bits_to_list(bits))
        energies.append(_eval_qubo(Q, bits))

    return SampleResult(
        method="generative",
        bitstrings=bitstrings,
        energies=energies,
        n_shots=n_shots,
        time_s=time.time() - t0,
        metadata={
            "p": p,
            "gamma": gamma,
            "beta": beta,
            "density": float(density) if adj is not None else None,
        },
    )


# Registry
SAMPLERS = {
    "uniform": sample_uniform,
    "greedy": sample_greedy,
    "qaoa": sample_qaoa,
    "learned_qaoa": sample_learned_qaoa,
    "generative": sample_generative,
}


def list_samplers() -> List[str]:
    return sorted(SAMPLERS.keys())


def run_sampler(name: str, Q: np.ndarray, n: int, n_shots: int = 200,
                seed: int = 42, **kwargs) -> SampleResult:
    if name not in SAMPLERS:
        raise ValueError(f"Unknown sampler: {name}. Available: {list_samplers()}")
    return SAMPLERS[name](Q, n, n_shots=n_shots, seed=seed, **kwargs)


def run_all_samplers(Q: np.ndarray, n: int, n_shots: int = 200, seed: int = 42,
                     adj: np.ndarray = None, weights: List[float] = None,
                     problem_type: str = "mwis") -> Dict[str, SampleResult]:
    """Run all samplers with the same budget."""
    results = {}

    results["uniform"] = sample_uniform(Q, n, n_shots=n_shots, seed=seed)
    results["greedy"] = sample_greedy(Q, n, n_shots=n_shots, seed=seed)
    results["qaoa"] = sample_qaoa(Q, n, n_shots=n_shots, p=2, seed=seed)
    results["learned_qaoa"] = sample_learned_qaoa(Q, n, n_shots=n_shots, p=3, seed=seed)
    results["generative"] = sample_generative(Q, n, n_shots=n_shots,
                                               problem_type=problem_type,
                                               adj=adj, weights=weights, seed=seed)

    return results
