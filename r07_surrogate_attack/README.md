# R07 — Classical Surrogate Attack

**Track:** A — Quantum Learning
**Wave:** 2 (Months 4-6)
**Status:** 🔲 Not started

## Question

Can a classical surrogate approximate quantum features (X→Q)? Can classical ML solve the task directly without quantum features (X→Y)?

## Two Distinct Questions

| Question | Test | Importance |
|----------|------|------------|
| X→Q | Can classical surrogate approximate Q? | Lower — shows quantum features are simulable |
| X→Y | Can classical ML solve task directly? | **Higher** — the real comparison |

## Surrogates

Ridge, polynomial (degree 2–4), RBF, RF, ExtraTrees, XGBoost, MLP, GNN, Graph Transformer, tensor network

## Critical Metrics

```
E_Q = ‖Q - Q̂_C‖     (surrogate reconstruction error)
M_C(X→Y)            (classical task performance)
```

## Gate

**R07-G1:** A QML result proceeds only if M_Q > M_C* OR there is a clear sample/resource-efficiency separation.

## Reuse

- QMT classical attack suite (RF, XGBoost already implemented)
