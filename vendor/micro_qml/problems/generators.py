"""Graph problem generators for Micro-QML research.

7 combinatorial graph problems, each with:
- Random instance generation
- Exact classical solution for small instances (<=16 nodes)
- QUBO/QAOA encoding metadata
- Hardness characterization

Problems:
    1. balanced_partition    - Balanced graph partitioning / minimum bisection
    2. mwis                  - Maximum Weighted Independent Set
    3. maxcut                - Maximum Cut
    4. community_detection   - Community detection (modularity maximization)
    5. graph_coloring        - Graph coloring with k colors
    6. tsp                   - Traveling Salesman Problem
    7. min_vertex_cover      - Minimum Vertex Cover

Only depends on numpy + standard library (no networkx / external graph libs).
"""
from __future__ import annotations

import itertools
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------
@dataclass
class ProblemInstance:
    """A single problem instance."""

    problem_type: str
    graph: dict  # {n, edges, weights, family, adjacency, density}
    objective: str  # "minimize" or "maximize"
    constraints: dict
    classical_solution: dict  # {value, assignment, method, time_s}
    qubit_count: int
    metadata: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return self.graph["n"]

    @property
    def is_hard(self) -> bool:
        """Whether this instance is non-trivial (classical solver took time)."""
        return self.classical_solution.get("time_s", 0.0) > 0.01


# ---------------------------------------------------------------------------
# Graph generation
# ---------------------------------------------------------------------------
def generate_graph(
    n: int,
    family: str = "ER",
    p: float = 0.3,
    seed: int = 42,
    weighted: bool = False,
) -> dict:
    """Generate a random graph.

    Supported families:
        ER, BA, WS, SBM, grid, cycle, path, star, complete,
        bipartite, 3regular, geometric, wheel, circular_ladder, heavy_hex
    """
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)

    edges: List[List[int]] = []

    if family == "ER":
        for i in range(n):
            for j in range(i + 1, n):
                if np_rng.random() < p:
                    edges.append([i, j])

    elif family == "BA":
        m = 2
        if n > m:
            for i in range(m):
                for j in range(i + 1, m):
                    edges.append([i, j])
            for i in range(m, n):
                for _ in range(m):
                    j = rng.randint(0, i - 1)
                    edges.append([i, j])

    elif family == "WS":
        k = 4
        for i in range(n):
            for d in range(1, k // 2 + 1):
                edges.append([i, (i + d) % n])
        for idx in range(len(edges)):
            if np_rng.random() < 0.1:
                j = rng.randint(0, n - 1)
                if j != edges[idx][0]:
                    edges[idx][1] = j

    elif family == "SBM":
        # Stochastic block model with 2 communities
        k_comm = 2
        comm = [i % k_comm for i in range(n)]
        p_in, p_out = 0.6, 0.05
        for i in range(n):
            for j in range(i + 1, n):
                prob = p_in if comm[i] == comm[j] else p_out
                if np_rng.random() < prob:
                    edges.append([i, j])

    elif family == "grid":
        cols = int(math.isqrt(n))
        if cols < 1:
            cols = 1
        rows = (n + cols - 1) // cols
        for i in range(n):
            r, c = i // cols, i % cols
            if c + 1 < cols and i + 1 < n:
                edges.append([i, i + 1])
            if r + 1 < rows and i + cols < n:
                edges.append([i, i + cols])

    elif family == "cycle":
        if n >= 3:
            for i in range(n):
                edges.append([i, (i + 1) % n])
        elif n == 2:
            edges.append([0, 1])

    elif family == "path":
        for i in range(n - 1):
            edges.append([i, i + 1])

    elif family == "star":
        for i in range(1, n):
            edges.append([0, i])

    elif family == "complete":
        for i in range(n):
            for j in range(i + 1, n):
                edges.append([i, j])

    elif family == "bipartite":
        half = n // 2
        for i in range(half):
            for j in range(half, n):
                if np_rng.random() < 0.3:
                    edges.append([i, j])

    elif family == "3regular":
        # Simplified 3-regular-ish graph (cycle + chords)
        if n >= 3:
            for i in range(n):
                edges.append([i, (i + 1) % n])
        for i in range(n):
            if i + 2 < n:
                edges.append([i, i + 2])

    elif family == "heavy_hex":
        cols = 4
        for i in range(n):
            r, c = i // cols, i % cols
            if c + 1 < cols and i + 1 < n:
                edges.append([i, i + 1])
            if r + 1 < (n + cols - 1) // cols and i + cols < n:
                edges.append([i, i + cols])

    elif family == "geometric":
        points = np_rng.rand(n, 2)
        for i in range(n):
            for j in range(i + 1, n):
                d = float(np.linalg.norm(points[i] - points[j]))
                if d < 0.3:
                    edges.append([i, j])

    elif family == "wheel":
        if n >= 3:
            for i in range(1, n):
                edges.append([0, i])
                edges.append([i, (i + 1) % n if i + 1 < n else 1])

    elif family == "circular_ladder":
        half = n // 2
        if half >= 2:
            for i in range(half):
                edges.append([i, (i + 1) % half])
                edges.append([i, i + half])
                edges.append([i + half, (i + 1) % half + half])

    else:  # default: ER-like
        for i in range(n):
            for j in range(i + 1, n):
                if np_rng.random() < 0.2:
                    edges.append([i, j])

    # Deduplicate + remove self loops
    seen = set()
    unique_edges: List[List[int]] = []
    for e in edges:
        key = (min(e[0], e[1]), max(e[0], e[1]))
        if key not in seen and e[0] != e[1]:
            seen.add(key)
            unique_edges.append(list(key))

    # Build adjacency matrix
    adj = np.zeros((n, n), dtype=float)
    for i, j in unique_edges:
        w = float(np_rng.uniform(0.5, 2.0)) if weighted else 1.0
        adj[i][j] = w
        adj[j][i] = w

    weights = (
        np_rng.uniform(0.5, 2.0, n).tolist() if weighted else [1.0] * n
    )

    density = len(unique_edges) / max(n * (n - 1) / 2, 1)

    return {
        "n": n,
        "edges": unique_edges,
        "weights": weights,
        "family": family,
        "adjacency": adj,
        "density": round(density, 4),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _neighbors(n: int, edges: List[List[int]]) -> List[List[int]]:
    """Adjacency list from edge list."""
    adj_list: List[List[int]] = [[] for _ in range(n)]
    for i, j in edges:
        adj_list[i].append(j)
        adj_list[j].append(i)
    return adj_list


# ---------------------------------------------------------------------------
# 1. Balanced Graph Partitioning / Minimum Bisection
# ---------------------------------------------------------------------------
def generate_balanced_partition(
    n: int,
    family: str = "ER",
    seed: int = 42,
    weighted: bool = False,
    p: float = 0.3,
) -> ProblemInstance:
    """Balanced graph partitioning / minimum bisection.

    Partition V into V1, V2 with |V1| = |V2| (+/-1) minimizing cut weight.
    QUBO encoding: n qubits (one per vertex, 0=V1, 1=V2).
    Constraint: balance via penalty term.
    """
    graph = generate_graph(n, family, p=p, seed=seed, weighted=weighted)
    adj = graph["adjacency"]
    edges = graph["edges"]

    t0 = time.time()
    best_cut = float("inf")
    best_assign: Optional[List[int]] = None
    method = "heuristic"

    if n <= 14:
        method = "brute_force"
        size1 = n // 2
        for bits in itertools.combinations(range(n), size1):
            v1 = set(bits)
            assign = [1 if i in v1 else 0 for i in range(n)]
            cut = 0.0
            for i, j in edges:
                if assign[i] != assign[j]:
                    cut += adj[i][j]
            if cut < best_cut:
                best_cut = cut
                best_assign = assign
    else:
        # Heuristic: alternate by BFS ordering, then local search
        assign = [0] * n
        for i in range(n):
            assign[i] = i % 2
        # local flip search keeping balance
        improved = True
        while improved:
            improved = False
            for i in range(n):
                for j in range(i + 1, n):
                    if assign[i] == assign[j]:
                        continue
                    # swap i, j keeps balance
                    cur = sum(
                        adj[i][k] for k in range(n) if assign[k] != assign[i]
                    ) + sum(
                        adj[j][k] for k in range(n) if assign[k] != assign[j]
                    )
                    assign[i], assign[j] = assign[j], assign[i]
                    new = sum(
                        adj[i][k] for k in range(n) if assign[k] != assign[i]
                    ) + sum(
                        adj[j][k] for k in range(n) if assign[k] != assign[j]
                    )
                    if new < cur - 1e-12:
                        improved = True
                    else:
                        assign[i], assign[j] = assign[j], assign[i]
        cut = 0.0
        for i, j in edges:
            if assign[i] != assign[j]:
                cut += adj[i][j]
        best_cut = cut
        best_assign = assign

    classical_time = time.time() - t0

    return ProblemInstance(
        problem_type="balanced_partition",
        graph=graph,
        objective="minimize",
        constraints={
            "balance": True,
            "partition_sizes": [n // 2, n - n // 2],
        },
        classical_solution={
            "value": float(best_cut),
            "assignment": best_assign,
            "method": method,
            "time_s": classical_time,
        },
        qubit_count=n,
        metadata={"cut_weight": float(best_cut)},
    )


# ---------------------------------------------------------------------------
# 2. Maximum Weighted Independent Set (MWIS)
# ---------------------------------------------------------------------------
def generate_mwis(
    n: int,
    family: str = "ER",
    seed: int = 42,
    weighted: bool = True,
    p: float = 0.3,
) -> ProblemInstance:
    """Maximum Weighted Independent Set.

    Find S subset V with no edges between vertices in S, maximizing sum w_i.
    QUBO encoding: n qubits, penalty for adjacent vertices both selected.
    """
    graph = generate_graph(n, family, p=p, seed=seed, weighted=weighted)
    weights = graph["weights"]
    adj_list = _neighbors(n, graph["edges"])

    t0 = time.time()
    best_val = float("-inf")
    best_set: Optional[List[int]] = None
    method = "heuristic"

    if n <= 16:
        method = "brute_force"
        for mask in range(1 << n):
            # quick independence check
            ok = True
            for i in range(n):
                if not (mask >> i) & 1:
                    continue
                for j in adj_list[i]:
                    if j > i and (mask >> j) & 1:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue
            val = sum(weights[i] for i in range(n) if (mask >> i) & 1)
            if val > best_val:
                best_val = val
                best_set = [(mask >> i) & 1 for i in range(n)]
    else:
        # Greedy: sort by weight/degree ratio, add if no conflict
        order = sorted(
            range(n), key=lambda v: weights[v] / (len(adj_list[v]) + 1), reverse=True
        )
        selected = set()
        for v in order:
            if all(u not in selected for u in adj_list[v]):
                selected.add(v)
        best_val = sum(weights[v] for v in selected)
        best_set = [1 if i in selected else 0 for i in range(n)]

    classical_time = time.time() - t0

    return ProblemInstance(
        problem_type="mwis",
        graph=graph,
        objective="maximize",
        constraints={"independent": True},
        classical_solution={
            "value": float(best_val),
            "assignment": best_set,
            "method": method,
            "time_s": classical_time,
        },
        qubit_count=n,
        metadata={"set_size": int(sum(best_set)) if best_set else 0},
    )


# ---------------------------------------------------------------------------
# 3. MaxCut
# ---------------------------------------------------------------------------
def generate_maxcut(
    n: int,
    family: str = "ER",
    seed: int = 42,
    weighted: bool = False,
    p: float = 0.3,
) -> ProblemInstance:
    """Maximum Cut.

    Partition V into S, T maximizing cut weight.
    QUBO encoding: n qubits.
    """
    graph = generate_graph(n, family, p=p, seed=seed, weighted=weighted)
    adj = graph["adjacency"]
    edges = graph["edges"]

    t0 = time.time()
    best_val = float("-inf")
    best_assign: Optional[List[int]] = None
    method = "heuristic"

    if n <= 16:
        method = "brute_force"
        for mask in range(1 << (n - 1)):  # symmetry: fix last bit = 0
            assign = [(mask >> i) & 1 for i in range(n - 1)] + [0]
            cut = 0.0
            for i, j in edges:
                if assign[i] != assign[j]:
                    cut += adj[i][j]
            if cut > best_val:
                best_val = cut
                best_assign = assign
    else:
        # Local search
        assign = [i % 2 for i in range(n)]
        improved = True
        while improved:
            improved = False
            for i in range(n):
                same = sum(adj[i][j] for j in range(n) if assign[j] == assign[i])
                diff = sum(adj[i][j] for j in range(n) if assign[j] != assign[i])
                if same > diff:
                    assign[i] = 1 - assign[i]
                    improved = True
        cut = 0.0
        for i, j in edges:
            if assign[i] != assign[j]:
                cut += adj[i][j]
        best_val = cut
        best_assign = assign

    classical_time = time.time() - t0

    return ProblemInstance(
        problem_type="maxcut",
        graph=graph,
        objective="maximize",
        constraints={},
        classical_solution={
            "value": float(best_val),
            "assignment": best_assign,
            "method": method,
            "time_s": classical_time,
        },
        qubit_count=n,
        metadata={"cut_value": float(best_val)},
    )


# ---------------------------------------------------------------------------
# 4. Community Detection (modularity maximization)
# ---------------------------------------------------------------------------
def generate_community_detection(
    n: int,
    family: str = "SBM",
    seed: int = 42,
    k_communities: int = 2,
    p: float = 0.3,
) -> ProblemInstance:
    """Community detection via modularity maximization.

    Partition V into communities maximizing modularity Q.
    QUBO encoding: n * k qubits (one-hot community assignment).
    """
    graph = generate_graph(n, family, p=p, seed=seed, weighted=False)
    adj = graph["adjacency"]
    edges = graph["edges"]
    m = len(edges)
    two_m = 2.0 * m if m > 0 else 1.0

    degrees = [float(sum(adj[i])) for i in range(n)]

    def modularity(assign: List[int]) -> float:
        # assign[i] in [0, k)
        q = 0.0
        for i in range(n):
            for j in range(n):
                if assign[i] == assign[j]:
                    q += adj[i][j] - degrees[i] * degrees[j] / two_m
        return q / two_m

    t0 = time.time()
    best_q = float("-inf")
    best_assign: Optional[List[int]] = None
    method = "heuristic"

    if n <= 12 and k_communities == 2:
        method = "brute_force"
        for mask in range(1 << n):
            assign = [(mask >> i) & 1 for i in range(n)]
            q = modularity(assign)
            if q > best_q:
                best_q = q
                best_assign = assign
    else:
        # Greedy label propagation-ish
        rng = random.Random(seed)
        assign = [rng.randint(0, k_communities - 1) for _ in range(n)]
        improved = True
        iters = 0
        while improved and iters < 100:
            improved = False
            iters += 1
            for i in range(n):
                best_c = assign[i]
                best_gain = 0.0
                for c in range(k_communities):
                    gain = 0.0
                    for j in range(n):
                        if assign[j] == c:
                            gain += adj[i][j] - degrees[i] * degrees[j] / two_m
                    if gain > best_gain + 1e-12:
                        best_gain = gain
                        best_c = c
                if best_c != assign[i]:
                    assign[i] = best_c
                    improved = True
        best_q = modularity(assign)
        best_assign = assign

    classical_time = time.time() - t0

    return ProblemInstance(
        problem_type="community_detection",
        graph=graph,
        objective="maximize",
        constraints={"k_communities": k_communities},
        classical_solution={
            "value": float(best_q),
            "assignment": best_assign,
            "method": method,
            "time_s": classical_time,
        },
        qubit_count=n * k_communities,
        metadata={
            "modularity": float(best_q),
            "k_communities": k_communities,
        },
    )


# ---------------------------------------------------------------------------
# 5. Graph Coloring
# ---------------------------------------------------------------------------
def generate_graph_coloring(
    n: int,
    family: str = "ER",
    seed: int = 42,
    k_colors: int = 3,
    p: float = 0.3,
) -> ProblemInstance:
    """Graph coloring with k colors.

    Assign colors to vertices so no adjacent vertices share a color.
    Objective: minimize number of conflicts (0 = proper coloring).
    QUBO encoding: n * k qubits.
    """
    graph = generate_graph(n, family, p=p, seed=seed, weighted=False)
    adj_list = _neighbors(n, graph["edges"])
    edges = graph["edges"]

    t0 = time.time()
    best_val = float("inf")
    best_assign: Optional[List[int]] = None
    method = "heuristic"

    def conflicts(assign: List[int]) -> int:
        c = 0
        for i, j in edges:
            if assign[i] == assign[j]:
                c += 1
        return c

    if n <= 10 and k_colors <= 4:
        method = "brute_force"
        # iterate all k^n colorings
        for combo in itertools.product(range(k_colors), repeat=n):
            assign = list(combo)
            c = conflicts(assign)
            if c < best_val:
                best_val = c
                best_assign = assign
                if c == 0:
                    break
    else:
        # Greedy: color in order, pick first non-conflicting color
        assign = [0] * n
        for i in range(n):
            used = {assign[j] for j in adj_list[i] if j < i}
            for c in range(k_colors):
                if c not in used:
                    assign[i] = c
                    break
            else:
                assign[i] = 0
        best_val = conflicts(assign)
        best_assign = assign

    classical_time = time.time() - t0

    return ProblemInstance(
        problem_type="graph_coloring",
        graph=graph,
        objective="minimize",
        constraints={"k_colors": k_colors},
        classical_solution={
            "value": int(best_val),
            "assignment": best_assign,
            "method": method,
            "time_s": classical_time,
        },
        qubit_count=n * k_colors,
        metadata={
            "k_colors": k_colors,
            "conflicts": int(best_val),
            "proper": best_val == 0,
        },
    )


# ---------------------------------------------------------------------------
# 6. TSP
# ---------------------------------------------------------------------------
def generate_tsp(n: int, seed: int = 42) -> ProblemInstance:
    """Traveling Salesman Problem.

    Find shortest Hamiltonian cycle.
    QUBO encoding: n^2 qubits (n cities x n positions).
    """
    rng = np.random.RandomState(seed)
    coords = rng.rand(n, 2) * 10.0
    dist = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            dist[i][j] = float(np.linalg.norm(coords[i] - coords[j]))

    # Build a graph dict (complete graph with distance weights)
    edges = [[i, j] for i in range(n) for j in range(i + 1, n)]
    adj = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if i != j:
                adj[i][j] = dist[i][j]
    graph = {
        "n": n,
        "edges": edges,
        "weights": [1.0] * n,
        "family": "metric_complete",
        "adjacency": adj,
        "density": 1.0,
        "coords": coords.tolist(),
        "distance_matrix": dist,
    }

    t0 = time.time()
    best_len = float("inf")
    best_tour: Optional[List[int]] = None
    method = "heuristic"

    if n <= 10:
        method = "brute_force"
        # fix city 0, permute the rest
        for perm in itertools.permutations(range(1, n)):
            tour = [0] + list(perm)
            length = 0.0
            for i in range(n):
                length += dist[tour[i]][tour[(i + 1) % n]]
            if length < best_len:
                best_len = length
                best_tour = tour
    else:
        # Nearest neighbor heuristic
        tour = [0]
        visited = {0}
        cur = 0
        for _ in range(n - 1):
            nxt = min(
                (j for j in range(n) if j not in visited),
                key=lambda j: dist[cur][j],
            )
            tour.append(nxt)
            visited.add(nxt)
            cur = nxt
        length = 0.0
        for i in range(n):
            length += dist[tour[i]][tour[(i + 1) % n]]
        best_len = length
        best_tour = tour

    classical_time = time.time() - t0

    return ProblemInstance(
        problem_type="tsp",
        graph=graph,
        objective="minimize",
        constraints={"hamiltonian_cycle": True},
        classical_solution={
            "value": float(best_len),
            "assignment": best_tour,
            "method": method,
            "time_s": classical_time,
        },
        qubit_count=n * n,
        metadata={
            "tour_length": float(best_len),
            "coords": coords.tolist(),
        },
    )


# ---------------------------------------------------------------------------
# 7. Minimum Vertex Cover
# ---------------------------------------------------------------------------
def generate_min_vertex_cover(
    n: int,
    family: str = "ER",
    seed: int = 42,
    p: float = 0.3,
) -> ProblemInstance:
    """Minimum Vertex Cover.

    Find smallest S subset V such that every edge has at least one endpoint in S.
    QUBO encoding: n qubits.
    Note: MVC is the complement of MIS, so |MVC| + |MIS| = |V|.
    """
    graph = generate_graph(n, family, p=p, seed=seed, weighted=False)
    adj_list = _neighbors(n, graph["edges"])
    edges = graph["edges"]

    t0 = time.time()
    best_val = float("inf")
    best_set: Optional[List[int]] = None
    method = "heuristic"

    if n <= 16:
        method = "brute_force"
        # find smallest subset that covers all edges
        for mask in range(1 << n):
            # size check: skip if already >= best
            if bin(mask).count("1") >= best_val:
                continue
            ok = True
            for i, j in edges:
                if not ((mask >> i) & 1) and not ((mask >> j) & 1):
                    ok = False
                    break
            if ok:
                best_val = bin(mask).count("1")
                best_set = [(mask >> i) & 1 for i in range(n)]
    else:
        # Greedy: repeatedly pick vertex covering most uncovered edges
        uncovered = set(range(len(edges)))
        cover = set()
        edge_set = [tuple(e) for e in edges]
        while uncovered:
            counts: Dict[int, int] = {}
            for idx in uncovered:
                for v in edge_set[idx]:
                    counts[v] = counts.get(v, 0) + 1
            v = max(counts, key=counts.get)
            cover.add(v)
            uncovered = {
                idx for idx in uncovered if v not in edge_set[idx]
            }
        best_val = len(cover)
        best_set = [1 if i in cover else 0 for i in range(n)]

    classical_time = time.time() - t0

    return ProblemInstance(
        problem_type="min_vertex_cover",
        graph=graph,
        objective="minimize",
        constraints={"cover_all_edges": True},
        classical_solution={
            "value": int(best_val),
            "assignment": best_set,
            "method": method,
            "time_s": classical_time,
        },
        qubit_count=n,
        metadata={"cover_size": int(best_val)},
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
PROBLEM_GENERATORS = {
    "balanced_partition": generate_balanced_partition,
    "mwis": generate_mwis,
    "maxcut": generate_maxcut,
    "community_detection": generate_community_detection,
    "graph_coloring": generate_graph_coloring,
    "tsp": generate_tsp,
    "min_vertex_cover": generate_min_vertex_cover,
}


def list_problems() -> List[str]:
    """Return sorted list of available problem types."""
    return sorted(PROBLEM_GENERATORS.keys())


def generate_problem(problem_type: str, n: int = 8, **kwargs) -> ProblemInstance:
    """Generate a problem instance by type.

    Args:
        problem_type: one of list_problems()
        n: problem size (number of vertices / cities)
        **kwargs: passed to the specific generator (family, seed, weighted, etc.)

    Returns:
        ProblemInstance with classical_solution computed.
    """
    if problem_type not in PROBLEM_GENERATORS:
        raise ValueError(
            f"Unknown problem: {problem_type}. Available: {list_problems()}"
        )
    return PROBLEM_GENERATORS[problem_type](n, **kwargs)
