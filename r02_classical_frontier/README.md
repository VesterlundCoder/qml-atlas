# R02 — Classical Frontier

**Track:** Infrastructure (cross-cutting)
**Wave:** 1 (Months 1-3)
**Status:** 🔲 Not started

## Question

What is the strongest classical performance for each problem family and size?

## Why This Matters

This is one of the most important projects of the year. No quantum result may be classified QA1 until it beats this frontier. Weak classical baselines are the most common failure mode in quantum advantage claims.

## Problem Families

| Family | Description | Sizes |
|--------|-------------|-------|
| MaxCut | Unweighted graph bisection | 8–1000 |
| weighted MaxCut | Weighted graph bisection | 8–1000 |
| MWIS | Maximum weighted independent set | 8–500 |
| MIS | Maximum independent set | 8–500 |
| graph partitioning | Balanced graph partition | 8–250 |
| Ising spin glass | Ising ground state | 8–100 |
| frustrated loops | Frustrated loop minimization | 8–100 |
| QUBO | General QUBO | 8–250 |
| small scheduling | Job scheduling | 8–100 |
| routing | Vehicle routing | 8–100 |
| planted-solution | Planted optimum instances | 8–100 |
| deceptive landscapes | Deceptive trap functions | 8–50 |

## Classical Suite

| Solver | Type | Sizes |
|--------|------|-------|
| Exact enumeration | Brute force | n ≤ 20 |
| CP-SAT | Constraint programming | n ≤ 100 |
| SCIP/Gurobi | MILP | n ≤ 500 (if licensed) |
| Greedy | Local heuristic | All |
| Multistart | Multi-seed greedy | All |
| Tabu search | Local search with memory | All |
| Simulated annealing | Stochastic local search | All |
| Parallel tempering | Multi-temperature SA | n ≥ 20 |
| Evolutionary search | GA/DE | n ≥ 20 |
| Random Forest | ML predictor | All |
| XGBoost | ML predictor | All |
| MLP | Neural predictor | All |
| GNN | Graph neural network | All |
| Autoregressive sampler | Learned sampler | n ≥ 16 |
| Tensor-network | TN contraction | n ≤ 32 |

## Primary Output

```
M_C*(x) = max over all classical methods of metric(x, method)
```

for every (problem_family, size, difficulty, seed) combination.

## Gate

**R02-G1:** No quantum result may be classified QA1 until it beats this frontier.

## Implementation

```bash
python -m projects.QAB.r02_classical_frontier.run --sizes 8,12,16,20,32,50,100
```

## Compute

- 150k–300k CPU-core-hours
- 1k–3k GPU-hours

## Reuse

- `gqo_qss/strong_baselines.py` — tabu, multistart, metropolis
- `gqo_qss/samplers.py` — uniform, greedy, SA
- QMT classical attack suite — RF, XGBoost
