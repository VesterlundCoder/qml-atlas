# R04 — Resource Accounting Standard

**Track:** Infrastructure (cross-cutting)
**Wave:** 1 (Months 1-3)
**Status:** 🔲 Not started

## Question

Can quantum cost be honestly compared to classical cost?

## What This Project Builds

A standardized resource accounting framework that all R01-R20 projects must use. Without this, QA3 (resource advantage) claims are meaningless.

## Cost Models

### Quantum Cost

```
R_Q = T_QPU + T_compile + T_mitigation + T_classical_preprocessing + T_training
```

| Component | Description |
|-----------|-------------|
| T_QPU | Actual QPU execution time (shots × circuit time) |
| T_compile | Circuit compilation and transpilation |
| T_mitigation | Error mitigation overhead (ZNE, PEC, etc.) |
| T_classical_preprocessing | Classical preprocessing (LP relaxation, decomposition, etc.) |
| T_training | Training time for learned quantum methods |

### Classical Cost

```
R_C = T_CPU + T_GPU + T_training + T_hyperparameter_search
```

| Component | Description |
|-----------|-------------|
| T_CPU | CPU computation time |
| T_GPU | GPU computation time |
| T_training | Training time for learned classical methods |
| T_hyperparameter_search | Hyperparameter optimization cost |

### Reported Separately

- Wall-clock time
- Energy proxy (kWh estimate)
- Accelerator time (GPU/MI250X hours)
- Peak memory
- Dollar-equivalent (if relevant)

## Gate

**R04-G1:** QA3 may only be declared if:
1. M_Q ≥ M_C (quality at least as good)
2. R_Q < R_C (lower total resource cost)
3. Under a preregistered resource definition
4. With bootstrap CI for the cost ratio not crossing 1.0

## Implementation

```python
from projects.QAB.r04_resource_accounting import ResourceRecord, compare_resources

record = ResourceRecord(
    method="learned_qaoa",
    qpu_seconds=12.5,
    compile_seconds=3.2,
    mitigation_seconds=0.0,
    classical_preprocessing_seconds=1.1,
    training_seconds=45.0,
)
```

## Reuse

- `qcsc/resource_model/` — existing cost model
- `qcsc/qpu_budget.py` — QPU budget estimation
