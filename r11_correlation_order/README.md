# R11 — Correlation-Order Transition

**Track:** A — Quantum Learning
**Wave:** 2 (Months 4-6)
**Status:** 🔲 Not started

## Question

Does quantum advantage emerge at a specific correlation order m?

## What This Project Isolates

The role of higher-order quantum correlations, separated from entanglement depth and circuit family.

## Comparison

```
m = 1:  ⟨Z_i⟩, ⟨X_i⟩
m = 2:  ⟨Z_iZ_j⟩, ⟨X_iX_j⟩
m = 3:  ⟨Z_iZ_jZ_k⟩
m = 4:  ⟨Z_iZ_jZ_kZ_l⟩
```

Measure A(m) and classical simulation/surrogate cost for each order.

## Key Hypothesis

```
dA/dm > 0
```

Quantum gain increases with correlation order.

## Strong Gate

**R11-G1:** Quantum gain must increase AND classical surrogate fidelity must decrease simultaneously. This is much stronger than just higher accuracy.

## Discovery Signal

A possible finding: m=1,2 → A<0, but m=3,4 → A→0 or positive. This would be a very important mechanistic observation.
