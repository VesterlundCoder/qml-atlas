# R15 — Hybrid Hard-Core Optimization

**Track:** C — Quantum Optimization
**Wave:** 3 (Months 7-9)
**Status:** 🔲 Not started

## Question

Can classical preprocessing + QPU core beat classical-only on large problems?

## What This Project Does

Take large problems and reduce them to small cores solvable on QPU:

```
N ∈ {50, 100, 250, 500, 1000}  →  n_core = 12-32
```

## Comparison

| Approach | Description |
|----------|-------------|
| Classical only | Full classical solve |
| Classical preprocessing + QPU core | Reduce → QPU solve core → expand |

## Metrics

- Final objective value
- Optimality gap
- Success probability
- Time-to-target
- Total resource cost

## QA3 Gate

Hybrid must beat classical frontier in **Pareto sense** — not just on a single metric.

## Reuse

- QCSC decomposition (`qcsc/decomposition.py`)
- QCSC closed loop (`qcsc/closed_loop.py`)
- R02 classical frontier as baseline
