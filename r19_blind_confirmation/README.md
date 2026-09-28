# R19 — Blind Confirmation

**Track:** Infrastructure (cross-cutting)
**Wave:** 4 (Months 10-12)
**Status:** 🔲 Not started

## Question

Does the predicted crossover from R18 hold on completely new, unseen data?

## What This Project Does

The most rigorous test in the programme:
- New seed
- New problem instances
- New hidden test bank
- No model selection
- No hyperparameter tuning

## Minimum

```
N_test ≥ 200 per primary condition
```

## Primary Gate

```
H1: A > 0
```

## Multiple Testing

Use Holm or Benjamini-Hochberg correction depending on hypothesis structure.

## Outcome

| Result | Symbol | Action |
|--------|:------:|--------|
| Confirmed | 🟢 | Publish as quantum candidate |
| Unresolved | 🟡 | Publish as inconclusive |
| Falsified | 🔴 | Publish as negative result |

**All three outcomes are published.** Negative results go into the Atlas.

## Why This Matters

This is what separates a falsification study from a fishing expedition. The prediction was frozen in R18; the test is blind.
