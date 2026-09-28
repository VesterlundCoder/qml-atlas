# R13 — Quantum Sampling Sample Complexity

**Track:** B — Quantum Sampling
**Wave:** 3 (Months 7-9)
**Status:** 🔲 Not started

## Question

How many samples does a quantum sampler need to find the optimum, compared to classical?

## From R12

Compute the sample budget needed for success probability δ:

```
B_δ = log(δ) / log(1 - p_r)
```

## QA2 Gate

For δ = 0.05:

```
B_Q < 0.7 × B_C
```

This gives a clear sample-efficiency advantage.

## Why This Matters

Even if p_r(Q) ≈ p_r(C), a quantum sampler might achieve the same success probability with fewer total samples due to different variance structure.

## Dependencies

- R12 must complete first (provides p_r values)
