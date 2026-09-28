# Preregistration Template — WestQuant Quantum Advantage Boundary

**Project:** R__ — [Project Name]
**Date:** YYYY-MM-DD
**Preregistration ID:** WQ-QAB-R__-YYYYMMDD
**Author:** David Vesterlund (ORCID: 0009-0000-6455-1141)

---

## 1. Research Question

[State the specific question this project answers, in the form of a testable hypothesis]

## 2. Primary Hypothesis

H1: [Primary hypothesis, e.g., E[p_r(Q)] > E[p_r(C*)]]

## 3. Secondary Hypotheses

H2: [e.g., sample efficiency]
H3: [e.g., scaling with n]

## 4. Benchmark

- **Problem family:** [e.g., MWIS, MaxCut]
- **Difficulty level:** [D1-D4]
- **Instance count:** [N train, N val, N test]
- **Sizes:** [n values]
- **Seeds:** [train/val/test seed ranges]

## 5. Frozen Split

- **Train:** seeds XX-XX (XX%)
- **Validation:** seeds XX-XX (XX%)
- **Test:** seeds XX-XX (XX%)

## 6. Primary Metric

[metric name, e.g., p_r at r=2]

## 7. Secondary Metrics

[List all secondary metrics]

## 8. Samplers / Methods

[List all quantum and classical methods to be compared]

## 9. Fairness Protocol

- [ ] Protocol A: Equal proposal budget (B=___)
- [ ] Protocol B: Equal compute budget

## 10. Baseline Hierarchy

- B0: [reference/exact]
- B1: [strongest classical]
- B2: [canonical quantum]
- B3: [published frontier — frozen at this preregistration]
- B4: [WestQuant method]

## 11. Resource Budget

- **Quantum:** [shots, QPU seconds, circuit depth]
- **Classical:** [CPU seconds, GPU seconds, training time]
- **Hyperparameter search:** [budget for each method]

## 12. Statistical Test

- **Primary:** [e.g., paired permutation test, α=0.05]
- **Multiple comparison correction:** [e.g., Holm, Benjamini-Hochberg]
- **Effect size:** [e.g., Cohen's d]
- **Bootstrap CI:** [B=10000]

## 13. QA Level Target

[Target QA level: QA0/QA1/QA2/QA3/QA4]

## 14. Gate Criteria

- **Pass:** [criteria for passing the gate]
- **Fail:** [criteria for failing — what constitutes falsification]
- **Kill:** [criteria for killing the track early]

## 15. Exclusion Rules

[When can an instance or result be excluded?]

## 16. Hardware Subset Selection Rule

[If hardware is used, how is the subset selected? Must be independent of quantum-vs-classical outcome]

## 17. Deviations

[Any known deviations from the master protocol, with justification]

---

## Signature

I confirm that this protocol is frozen before test evaluation.

**Date:** YYYY-MM-DD
**Commit:** [git commit hash]
