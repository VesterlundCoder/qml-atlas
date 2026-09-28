# Fairness Protocol A: Equal Proposal Budget

## Definition

Every sampler receives exactly **B proposals** per graph instance. A "proposal" means one candidate state passed into the exact same downstream repair/recovery pipeline.

## Rules

1. **No hidden local search.** No sampler receives additional local-search steps unless they are explicitly counted as part of the proposal budget.

2. **Same pipeline.** All proposals go through the same repair → r-flip expansion → restricted exact solve pipeline.

3. **Same budget.** B is fixed across all samplers for a given experiment. Typical values: B ∈ {25, 50, 100, 200, 500, 1000}.

4. **No warm-start leakage.** A sampler may use problem-specific information (e.g., warm-start QAOA uses LP relaxation), but the information cost must be reported.

5. **Stochastic samplers.** For stochastic methods, each proposal is independent. Multiple seeds are used to estimate variance.

6. **Quantum samplers.** Each quantum "proposal" is one shot from the quantum circuit. Circuit preparation cost is reported separately but does not count against the proposal budget.

## Reporting

For each (sampler, instance) pair:
- p_r (recovery-basin mass)
- P_success(B) = 1 - (1-p_r)^B
- B_δ for δ ∈ {0.5, 0.9, 0.95, 0.99}
- Post-recovery optimality gap
- Sampler entropy
- Unique samples
- Wall-clock time
