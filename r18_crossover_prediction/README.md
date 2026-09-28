# R18 — Frozen Crossover Prediction

**Track:** Infrastructure (cross-cutting)
**Wave:** 4 (Months 10-12)
**Status:** 🔲 Not started

## Question

Can we predict where the quantum advantage crossover lies and then freeze the prediction?

## What This Project Does

From the discovery phase (R06–R17), fit:

```
A(n, p, m, D, ε)
```

Make an explicit prediction: crossover expected near (n*, p*, m*).

Example: (n*, p*, m*) = (28, 4, 3)

## Preregistration

Before test evaluation:
- Crossover region
- Model specification
- Baseline
- Metric
- Hardware
- Test instances
- Statistical test

Then **lock everything**. No changes after this point.

## Why This Matters

This is the transition from discovery to confirmation. The prediction must be made before seeing test data, or the result is not valid.

## Dependencies

- R06–R17 must complete first
