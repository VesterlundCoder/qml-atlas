# R08 — Sample-Efficiency Boundary

**Track:** A — Quantum Learning
**Wave:** 2 (Months 4-6)
**Status:** 🔲 Not started

## Question

Can quantum methods reach a target quality with fewer samples than classical methods?

## Training Sizes

N ∈ {100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000}

## Metric

For each method, estimate:

```
N_90 = number of samples to reach 90% of asymptotic performance
```

## QA2 Gate

```
N_90,Q < 0.7 × N_90,C
```

At least 30% improvement to be considered practically interesting.

## Why This Matters

Sample efficiency may be an easier quantum advantage to find than prediction advantage. A quantum method that learns from fewer examples could be useful even if its asymptotic quality matches classical methods.

## Implementation

```bash
python -m projects.QAB.r08_sample_efficiency.run --sizes 100,250,500,1000,2500,5000
python -m projects.QAB.r08_sample_efficiency.analyze  # Compute N_90 for each method
```
