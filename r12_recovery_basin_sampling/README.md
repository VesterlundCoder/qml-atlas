# R12 — Recovery-Basin Sampling

**Track:** B — Quantum Sampling
**Wave:** 3 (Months 7-9)
**Status:** 🟡 Seed data exists (GQO+QSS, 270 records in Atlas)

## Question

Can a quantum sampler place more probability mass in a useful classical recovery basin than strong classical samplers?

## Core Formulation

For small cores, compute exactly:

```
A_r(G) = { x : E_r(R(x)) ∩ X*(G) ≠ ∅ }
```

Recovery-basin mass:

```
p_r(q, G) = Pr_{x~q}[x ∈ A_r(G)]
```

## Cores

n ∈ {12, 16, 20} with exact A_r(G) enumeration

## Recovery Radii

r = 0, 1, 2, 3, 4

## Shot Budgets

B ∈ {25, 50, 100, 200, 500, 1000}

## Samplers

| Quantum | Classical |
|---------|----------|
| QAOA | Uniform |
| Learned QAOA | Gibbs |
| Generative circuit | SA |
| | Tabu |
| | Evolutionary |
| | Learned autoregressive |

## Main Metric

```
p_r(q, G)
```

## QA1 Sampling Gate

```
p_r(Q) > p_r(C*)
```

with preregistered 95% CI entirely above zero for paired difference.

## Existing Results

GQO+QSS final experiment (270 records) already in Atlas:
- 9 samplers × 30 instances
- n ∈ {16, 18, 20, 24, 28}
- 200 samples per sampler
- Result: classical advantage (tabu dominates)

## Reuse

- `gqo_qss/final_experiment.py`
- `gqo_qss/recovery.py`
- `data/recovery_basins/` — 360 basin masks
- `gqo_qss/samplers.py`
