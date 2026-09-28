# Baseline Hierarchy — WestQuant QAB

Every R01-R20 experiment must include five baseline levels:

| Level | Name | Required |
|-------|------|----------|
| B0 | Reference | Exact solution / certified optimum where possible |
| B1 | Classical | Strongest reasonable modern classical solver |
| B2 | Canonical Quantum | Standard version of the algorithm |
| B3 | Published Frontier | Strong published variant relevant to the task |
| B4 | WestQuant | Our full method |

## Rules

1. **B0 is mandatory.** No experiment may proceed without certified ground truth (where computationally feasible).

2. **B1 must be strong.** Weak classical baselines are the most common failure mode in quantum advantage claims. Always include:
   - At minimum: SA, tabu search, and one learned classical method
   - For optimization: also include MILP/CP-SAT where possible
   - For ML: also include XGBoost, GNN, and a strong kernel method

3. **B2 is the vanilla quantum.** Standard QAOA p=1, standard VQE with UCCSD, standard QSCI with HF initial state.

4. **B3 is the published frontier.** This is frozen at preregistration. A literature sweep is done just before locking. If a better method is published during the project, it must be considered before B3 is frozen.

5. **B4 is WestQuant.** Our full-stack method: representation scheduling + learned policy + recovery.

## B3 Freezing Protocol

1. **Literature sweep:** Search for the strongest published method for the specific task and problem family.
2. **Implementation:** Implement or reproduce the B3 method.
3. **Verification:** Verify B3 reproduces published results on a small test.
4. **Freeze:** Record the exact B3 configuration, code commit, and paper reference in the preregistration.
5. **No changes after freezing.** B3 cannot be changed after test evaluation begins.

## Example B3 Methods (by track)

### Track A (Learning)
- Best published quantum kernel method
- Best published quantum feature map

### Track B (Sampling)
- Warm-start QAOA (Bucher et al.)
- Multi-angle QAOA
- ADAPT-QAOA

### Track C (Optimization)
- Distributed QAOA (DQAOA)
- Recursive QAOA
- Best published hybrid MaxCut solver

### Track D (Reservoir)
- Best published QRC result
- Classical reservoir computing SOTA
