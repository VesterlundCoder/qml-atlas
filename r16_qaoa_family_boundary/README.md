# R16 — QAOA Family Boundary

**Track:** C — Quantum Optimization
**Wave:** 3 (Months 7-9)
**Status:** 🔲 Not started

## Question

Which QAOA variant, if any, approaches the classical frontier, and at what depth/size?

## What This Project Tests

Systematic evaluation of the QAOA family:

| Variant | Description |
|---------|-------------|
| Standard QAOA | Fixed mixer, optimized θ |
| Warm-start QAOA | LP-relaxation initialization |
| Recursive QAOA | Recursive QAOA decomposition |
| Parameter transfer | θ transferred from smaller instances |
| Learned QAOA | WestQuant predicts θ |
| Representation-scheduled QAOA | WQT20 selects representation |

## Depth

p ∈ {1, 2, 3, 4, 6, 8}

## Size

n ∈ {12, 16, 20, 24, 28, 32}

## Kill Criterion

If a variant is >5% below classical frontier at two consecutive sizes, do not scale further without a mechanistic reason.

## Reuse

- `gqo_qss/fast_qaoa.py`
- `gqo_qss/scaling_boundary.py`
- GQO+QSS final experiment results (already in Atlas)
