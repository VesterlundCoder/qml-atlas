# R03 — Exact Landscape Atlas

**Track:** Infrastructure (cross-cutting)
**Wave:** 1 (Months 1-3)
**Status:** 🔲 Not started

## Question

What landscape features predict quantum utility?

## What This Project Builds

Mechanistic ground truth: for small instances, enumerate the entire 2^n solution space and compute landscape metrics that may predict where quantum methods are useful.

## Sizes

n ∈ {8, 10, 12, 14, 16, 18, 20}

For each instance, enumerate all 2^n bitstrings and compute:

| Metric | Definition |
|--------|-----------|
| Local minima count | Number of states with no better Hamming-1 neighbour |
| Optimal degeneracy | Number of optimal solutions |
| First excitation gap | Energy gap to first excited state |
| Basin sizes | Size of each local minimum's basin |
| Basin entropy | H = -Σ p_i log p_i over basins |
| Barrier heights | Minimum barrier between basins |
| Autocorrelation length | Correlation length of energy landscape |
| Ruggedness | Variance of energy differences |
| Frustration | Fraction of conflicting constraints |
| Hamming separation | Distance between local minima |
| Funnel structure | Whether basins form a funnel |

## Dataset

≥1000 instances per problem family, across difficulty levels D1–D4.

## Hypothesis

Quantum performance is better explained by landscape metrics than by n alone.

## Gate

**R03-G1:** At least one landscape variable explains significant variation in A(x) beyond problem size.

## Implementation

```bash
python -m projects.QAB.r03_landscape_atlas.enumerate --sizes 8,10,12,14,16,18,20 --families mwis,maxcut,ising
python -m projects.QAB.r03_landscape_atlas.analyze  # Correlation with A(x)
```

## Compute

50k–100k CPU-core-hours

## Reuse

- `gqo_qss/ground_truth_and_basins.py` — basin enumeration
- `data/recovery_basins/` — 359 existing basin masks (n=16, r=0–3)
- `data/ground_truth_certificates/` — 150 certified instances
