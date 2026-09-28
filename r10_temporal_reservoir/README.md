# R10 — Temporal Quantum Reservoir

**Track:** D — Quantum Reservoir Computing
**Wave:** 2 (Months 4-6)
**Status:** 🔲 Not started

## Question

Can a quantum reservoir processing optimizer trajectories predict future dynamics better than classical sequence models?

## What This Project Does

Feed optimizer trajectories (s_1, ..., s_T) into a quantum reservoir and predict:
- Future optimality gap
- Stagnation detection
- Restart benefit
- Best next solver
- Remaining time-to-target

## Trajectory Lengths

T ∈ {4, 8, 16, 32, 64}

## Baselines

| Model | Type |
|-------|------|
| LSTM | Recurrent neural network |
| GRU | Gated recurrent unit |
| Transformer | Self-attention sequence model |
| ESN | Echo State Network |
| TCN | Temporal convolutional network |
| MLP-on-summary | MLP on trajectory summary statistics |

## Gate

**R10-G1:** Quantum reservoir must beat both ESN AND Transformer on ≥1 preregistered temporal task.

## Why This Matters

This is a potentially much stronger track than static reservoir computing. Optimization dynamics have temporal structure that quantum reservoirs might exploit.

## Reuse

- QMT reservoir infrastructure
- GQO+QSS optimizer trajectories (from final experiment logs)
