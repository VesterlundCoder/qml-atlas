# Fairness Protocol B: Equal Compute Budget

## Definition

All samplers are compared under a **matched total compute budget**, not just matched proposal count. This protocol is stricter than Protocol A and is required for QA3 (resource advantage) claims.

## Resource Categories

### Quantum Cost
```
R_Q = T_QPU + T_compile + T_mitigation + T_classical_preprocessing + T_training
```

### Classical Cost
```
R_C = T_CPU + T_GPU + T_training + T_hyperparameter_search
```

## Rules

1. **All costs counted.** No cost category may be hidden or omitted.

2. **Hyperparameter search.** For learned methods (quantum or classical), the hyperparameter search cost is included in the total. A quantum method with 1000 config evaluations cannot be compared to a classical method with 10 config evaluations without accounting for this.

3. **Preprocessing.** Classical preprocessing (e.g., LP relaxation for warm-start) is counted.

4. **Training.** For learned methods, training time is amortized over the test set.

5. **Wall-clock.** Wall-clock time is reported alongside normalized compute.

## Pareto Comparison

Under Protocol B, a method "wins" only if it achieves:
- Same quality at lower cost, OR
- Better quality at same cost, OR
- A statistically better Pareto front over quality and cost.

## Reporting

For each (sampler, instance) pair:
- Total compute cost (CPU-seconds, GPU-seconds, QPU-seconds)
- Memory peak
- Energy proxy (if available)
- Quality metric (p_r, gap, accuracy)
- Pareto rank

## QA3 Declaration

QA3 (resource advantage) may only be declared if:
1. M_Q ≥ M_C (quality at least as good)
2. R_Q < R_C (lower total resource cost)
3. Under a preregistered resource definition
4. With bootstrap CI for the cost ratio not crossing 1.0
