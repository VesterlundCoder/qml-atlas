# R05 — Problem-Difficulty Generator

**Track:** Infrastructure (cross-cutting)
**Wave:** 1 (Months 1-3)
**Status:** 🔲 Not started

## Question

Can we generate problem instances with controlled difficulty?

## What This Project Builds

A difficulty generator that produces instances across four difficulty levels, with a difficulty score that predicts classical solver difficulty.

## Four Difficulty Levels

| Level | Name | Description |
|-------|------|-------------|
| D1 | Easy random | Random instances (sanity checks, baseline) |
| D2 | Structured random | SBM, regular, geometric, small-world graphs |
| D3 | Hard/frustrated | Frustrated loops, spin-glass-like, deceptive planted, high degeneracy, narrow basins |
| D4 | Adversarial/planted | Planted solutions with deceptive landscapes |

## Difficulty Score

```
D(G) = f(N_minima, H_basin, F_frustration, B_barrier, ...)
```

Where:
- N_minima: number of local minima
- H_basin: basin entropy
- F_frustration: frustration fraction
- B_barrier: mean barrier height

## Gate

**R05-G1:** Difficulty score predicts classical solver difficulty with R² > 0.5 on held-out instances.

If the score cannot predict difficulty, the scale is not informative enough.

## Implementation

```bash
python -m projects.QAB.r05_difficulty_generator.generate --level D1 --n 16 --count 100
python -m projects.QAB.r05_difficulty_generator.score --input instances/
python -m projects.QAB.r05_difficulty_generator.validate  # R² check
```

## Reuse

- `micro_qml/problems/generators.py` — existing MWIS generator
- `gqo_qss/ground_truth_and_basins.py` — for computing landscape metrics
