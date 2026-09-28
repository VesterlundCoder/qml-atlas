# R14 — Generative Quantum Sampler

**Track:** B — Quantum Sampling
**Wave:** 3 (Months 7-9)
**Status:** 🔲 Not started

## Question

Can a learned generative quantum sampler outperform both fixed QAOA and classical generative samplers?

## What This Project Does

The WestQuant model learns circuit selection:

```
G → θ        (learn parameters for fixed circuit)
G → circuit   (learn circuit architecture)
```

## Reward

```
R = p_r - λC
```

Where C is the total compute cost (including search cost).

## Comparison

| Method | Description |
|--------|-------------|
| Fixed QAOA | Standard QAOA with fixed p |
| Optimized QAOA | Classical optimization of θ |
| Learned parameters | WestQuant predicts θ from G |
| Learned circuit architecture | WestQuant predicts circuit structure |
| Classical generative sampler | Learned classical sampler |

## Gate

**R14-G1:** Generative quantum may not proceed if improvement comes only from more hyperparameter search. Search cost must be counted.

## Reuse

- `gqo_qss/generative_policy.py`
- `gqo_qss/oracle_and_policy.py`
- WQT20 model for circuit selection
