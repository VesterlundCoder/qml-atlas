# R09 — Static Quantum Reservoir Boundary

**Track:** D — Quantum Reservoir Computing
**Wave:** 2 (Months 4-6)
**Status:** 🔲 Not started

## Question

Can a static quantum reservoir (fixed circuit, no training) provide useful features that classical reservoirs cannot?

## Axes

| Axis | Range |
|------|-------|
| n (qubits) | 8 → 32 |
| p (depth) | 1 → 6 |
| m (correlation order) | 1 → 4 |

## Comparison

| Method | Type |
|--------|------|
| Separable | No entanglement (quantum baseline) |
| Entangled | Fixed entangling circuit |
| Scrambled | Deep random circuit |
| Classical reservoir | Echo State Network |
| ESN | Standard reservoir computing |
| Random Fourier | Random Fourier features |
| GNN | Graph neural network |

## Primary Question

Does a crossover arise when high-order correlations (m ≥ 3) are introduced?

## Gate

**R09-G1:** A_Q > 0 on ≥2 problem families on frozen test data.

## Reuse

- QMT infrastructure (`qmt/experiments/`, `qmt/quantum/`, `qmt/classical/`)
- QMT falsification results (already in Atlas as seed data)
