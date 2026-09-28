# R20 — Multi-QPU Boundary Validation

**Track:** Infrastructure (cross-cutting)
**Wave:** 4 (Months 10-12)
**Status:** 🔲 Not started

## Question

Is the quantum advantage boundary algorithmic or hardware-specific?

## What This Project Does

Test the same frozen experiment from R18–R19 on at least two hardware classes:

| Hardware | Type |
|----------|------|
| Trapped ion | Piast-Q (available) |
| Superconducting | IBM/Google (if accessible) |
| Neutral atom | QuEra/Pasqal (if accessible) |

All three are not required — minimum two.

## Metrics

```
A_ideal, A_ion, A_superconducting, A_neutral
```

## Gate

**R20-G1 (QA4):** Same trend (not necessarily same absolute results) across ≥2 implementations.

## Why This Matters

If the boundary only appears on one hardware class, it is hardware-specific, not algorithmic. A true quantum advantage should be robust to hardware platform.

## Reuse

- Piast-Q access (`gqo_qss/run_piastq.py`)
- R18 frozen experiment specification
- R19 blind confirmation protocol
