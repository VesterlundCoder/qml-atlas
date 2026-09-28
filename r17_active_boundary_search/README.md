# R17 — Active Boundary Search

**Track:** Infrastructure (cross-cutting)
**Wave:** 3 (Months 7-9)
**Status:** 🔲 Not started

## Question

Where in the parameter space is A(x) ≈ 0 (the quantum advantage boundary)?

## What This Project Does

Train a surrogate model on results from R06–R16:

```
Â(x) ≈ A(x)
```

Then use active learning to select the next experiment where:
- |Â(x)| ≈ 0 (near the boundary)
- Uncertainty is high (unexplored region)

## Acquisition Function

```
acquisition(x) = 1/|Â(x) + ε| × uncertainty(x)
```

## Constraint

Active learning may ONLY be used in discovery. No active-learning choices in confirmation (R18–R19).

## Why This Matters

The parameter space is too large to explore exhaustively. Active search focuses compute on the boundary region, which is where the scientifically interesting results lie.

## Dependencies

- R06–R16 must produce enough data to train the surrogate
