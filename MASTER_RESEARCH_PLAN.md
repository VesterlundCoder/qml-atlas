# Mapping the Quantum Advantage Boundary

## A Systematic Falsification Study Across Quantum Learning, Sampling, Optimization, and Reservoir Computing

**WestQuant 12-Month Master Research Plan (R01-R20)**

**Version:** v0.1.0
**Date:** 2026-09-28
**Author:** David Vesterlund (ORCID: 0009-0000-6455-1141)
**Status:** Active

---

## Scientific Thesis

> **We do not search for evidence of quantum advantage. We search for the boundary at which it becomes possible.**

Quantum advantage is treated as a **phase transition** in a high-dimensional parameter landscape. The advantage function:

```
A(x) = M_Q(x) - M_C*(x)
```

where `x = (n, p, m, B, ε, D, H, R, C_Q, C_C, ...)` and `M_C*` is the strongest classical method tested under matched information and resource regimes. The goal is to empirically map the surface `A(x) = 0` separating classical dominance (`A < 0`) from candidate quantum advantage regions (`A > 0`).

---

## Quantum Advantage Ladder

Used consistently across all R01-R20 projects. No project may jump from QA0 to "quantum advantage."

| Level | Definition |
|-------|-----------|
| QA0 | Quantum component changes representation/dynamics measurably |
| QA1 | Better prediction/solution quality on frozen held-out data |
| QA2 | Better sample efficiency: N_Q(τ) < N_C(τ) |
| QA3 | Better total resource efficiency: R_Q < R_C |
| QA4 | Advantage grows with problem size |
| QA5 | Formal/complexity-theoretic separation |

---

## Four Tracks

| Track | Question | Projects |
|-------|----------|----------|
| A: Quantum Learning | Can quantum feature maps/kernels extract predictive structure that strong classical ML cannot? | R06-R08, R11 |
| B: Quantum Sampling | Can quantum samplers place more probability mass in a useful recovery basin? | R12-R14 |
| C: Quantum Optimization | Can quantum improve solution quality or resource efficiency for combinatorial optimization? | R15-R16, R19 |
| D: Quantum Reservoir | Can quantum reservoirs (static + temporal) provide useful memory/dynamics? | R09-R10 |

Cross-cutting: R01 (Atlas), R02 (classical frontier), R03 (landscape), R04 (resources), R05 (difficulty), R17-R20 (boundary search + confirmation + hardware + synthesis).

---

## Wave Schedule

### Wave 1: Foundation (Months 1-3) — R01-R05

**Goal:** Build the map and establish the classical frontier.

#### R01: Boundary Atlas Infrastructure
- **Question:** Can all experiments be represented in one schema?
- **Implementation:** `atlas/schema.py` (ExperimentRecord), `atlas/registry.py` (SQLite + Parquet), `atlas/ingest.py` (converters), `atlas/query.py`, `atlas/visualize.py`
- **Seed data:** Ingest existing GQO final experiment (270 records), QMT results, Q-SITE results
- **Gate R01-G1:** 100% of future R02-R20 experiments can be logged without track-specific fields
- **Output:** Atlas v0.1 with ≥500 seed records
- **Compute:** Negligible

#### R02: Classical Frontier
- **Question:** What is the strongest classical performance for each problem family and size?
- **Problem families:** MaxCut, weighted MaxCut, MWIS, MIS, graph partitioning, Ising spin glass, frustrated loops, QUBO, scheduling, routing, planted, deceptive
- **Sizes:** n ∈ {8, 12, 16, 20, 32, 50, 100, 250, 500, 1000}
- **Classical suite:** exact enumeration, CP-SAT, SCIP/Gurobi, greedy, multistart, tabu, SA, parallel tempering, evolutionary, RF, XGBoost, MLP, GNN, autoregressive, tensor-network
- **Gate R02-G1:** No quantum result classified QA1 until it beats this frontier
- **Reuse:** `gqo_qss/strong_baselines.py`, `gqo_qss/samplers.py`
- **Compute:** 150k-300k CPU-core-hours, 1k-3k GPU-hours

#### R03: Exact Landscape Atlas
- **Question:** What landscape features predict quantum utility?
- **Sizes:** n ∈ {8, 10, 12, 14, 16, 18, 20}
- **Enumerate full 2^n solution space per instance**
- **Metrics:** local minima count, degeneracy, excitation gap, basin sizes, basin entropy, barrier heights, autocorrelation, ruggedness, frustration, Hamming separation, funnel structure
- **Dataset:** ≥1000 instances per problem family
- **Gate R03-G1:** ≥1 landscape variable explains significant variation in A(x) beyond problem size
- **Reuse:** `gqo_qss/ground_truth_and_basins.py`, `data/recovery_basins/` (359 masks)
- **Compute:** 50k-100k CPU-core-hours

#### R04: Resource Accounting Standard
- **Question:** Can quantum cost be honestly compared to classical cost?
- **Quantum cost:** R_Q = T_QPU + T_compile + T_mitigation + T_classical + T_training
- **Classical cost:** R_C = T_CPU + T_GPU + T_training + T_hyperparameter
- **Gate R04-G1:** QA3 only if M_Q ≥ M_C AND R_Q < R_C under preregistered resource definition
- **Reuse:** `qcsc/resource_model/`, `qcsc/qpu_budget.py`

#### R05: Problem-Difficulty Generator
- **Question:** Can we generate instances with controlled difficulty?
- **Levels:** D1 (easy random), D2 (structured random: SBM, regular, geometric, small-world), D3 (hard/frustrated: frustrated loops, spin-glass, deceptive planted, high degeneracy, narrow basins), D4 (real-world)
- **Difficulty score:** D(G) = f(N_minima, H_basin, F_frustration, B_barrier, ...)
- **Gate R05-G1:** Difficulty score predicts classical solver difficulty with R² > 0.5
- **Reuse:** `micro_qml/problems/generators.py`

### Wave 2: Broad Quantum Discovery (Months 4-6) — R06-R11

**Goal:** Find promising crossover regions.

#### R06: Quantum Feature Map Scaling (Track A)
- **Grid:** n ∈ {8, 12, 16, 20, 24, 32}, p ∈ {1, 2, 3, 4, 6}, m ∈ {1, 2, 3, 4}
- **Circuit families:** QAOA-like, RY-RXX, RY-RXX-RYY, Heisenberg, data reuploading, commutator-inspired, random entangling reservoir
- **Gate R06-G1:** Scale only if A(n+4) > A(n) in ≥2 consecutive steps
- **Compute:** 3k-8k GPU-hours

#### R07: Classical Surrogate Attack
- **Test both:** X→Q (surrogate quantum features) and X→Y (classical ML solves task directly)
- **Surrogates:** Ridge, polynomial, RBF, RF, ExtraTrees, XGBoost, MLP, GNN, Graph Transformer, tensor network
- **Gate R07-G1:** Proceed only if M_Q > M_C* or clear sample/resource separation
- **Reuse:** QMT classical attack suite

#### R08: Sample-Efficiency Boundary
- **Training sizes:** N ∈ {100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000}
- **Metric:** N_90 = samples to reach 90% of asymptotic performance
- **QA2 gate:** N_90,Q < 0.7 × N_90,C

#### R09: Static Quantum Reservoir Boundary (Track D)
- **Extends QMT directly**
- **Axes:** n = 8→32, p = 1→6, m = 1→4
- **Compare:** separable, entangled, scrambled, classical reservoir, ESN, random Fourier, GNN
- **Gate R09-G1:** A_Q > 0 on ≥2 problem families on frozen test data
- **Reuse:** QMT infrastructure (`qmt/experiments/`, `qmt/quantum/`, `qmt/classical/`)

#### R10: Temporal Quantum Reservoir
- **Feed optimizer trajectories:** s_1, ..., s_T, T ∈ {4, 8, 16, 32, 64}
- **Tasks:** predict future gap, stagnation, restart benefit, best next solver, remaining TTS
- **Baselines:** LSTM, GRU, Transformer, ESN, TCN, MLP
- **Gate R10-G1:** Quantum reservoir beats ESN AND Transformer on ≥1 preregistered temporal task

#### R11: Correlation-Order Transition (Track A)
- **Isolate role of higher-order quantum correlations: m = 1, 2, 3, 4**
- **Hypothesis:** dA/dm > 0
- **Strong gate R11-G1:** Quantum gain increases AND classical surrogate fidelity decreases

### Wave 3: Boundary Attack (Months 7-9) — R12-R17

**Goal:** Scale and attempt to falsify promising results.

#### R12: Recovery-Basin Sampling (Track B)
- **Cores:** n ∈ {12, 16, 20} with exact A_r(G)
- **Radii:** r = 0, 1, 2, 3, 4
- **Budgets:** B ∈ {25, 50, 100, 200, 500, 1000}
- **Quantum:** QAOA, learned QAOA, generative circuit
- **Classical:** uniform, Gibbs, SA, tabu, evolutionary, learned autoregressive
- **QA1 gate:** p_r(Q) > p_r(C*) with 95% CI entirely above zero
- **Reuse:** `gqo_qss/final_experiment.py`, `gqo_qss/recovery.py`, `data/recovery_basins/`

#### R13: Quantum Sampling Sample Complexity
- **From R12:** B_δ = log(δ) / log(1 - p_r)
- **QA2 gate:** For δ = 0.05, B_Q < 0.7 × B_C

#### R14: Generative Quantum Sampler
- **WestQuant model learns circuit selection: G → θ or G → circuit program**
- **Reward:** R = p_r - λC
- **Gate R14-G1:** Improvement must not come only from more hyperparameter search
- **Reuse:** `gqo_qss/generative_policy.py`, `gqo_qss/oracle_and_policy.py`

#### R15: Hybrid Hard-Core Optimization (Track C)
- **Large problems:** N ∈ {50, 100, 250, 500, 1000}, reduce to n_core = 12-32
- **Compare:** classical-only vs classical preprocessing + QPU core
- **QA3 gate:** Hybrid beats classical frontier in Pareto sense
- **Reuse:** QCSC decomposition, `qcsc/closed_loop.py`

#### R16: QAOA Family Boundary
- **Test:** standard, warm-start, recursive, parameter transfer, learned, representation-scheduled QAOA
- **Depth:** p ∈ {1, 2, 3, 4, 6, 8}, Size: n ∈ {12, 16, 20, 24, 28, 32}
- **Kill criterion:** >5% below frontier at 2 consecutive sizes → stop without mechanistic reason
- **Reuse:** `gqo_qss/fast_qaoa.py`, `gqo_qss/scaling_boundary.py`

#### R17: Active Boundary Search
- **Train surrogate Â(x) on R06-R16 results**
- **Acquisition:** Choose next experiment where |Â(x)| ≈ 0 and uncertainty is high
- **Constraint:** Active learning ONLY in discovery, never in confirmation

### Wave 4: Blind Confirmation + QPU (Months 10-12) — R18-R20

**Goal:** Freeze, confirm, validate on hardware, synthesize.

#### R18: Frozen Crossover Prediction
- **From discovery, fit A(n, p, m, D, ε)**
- **Make explicit prediction:** crossover near (n*, p*, m*)
- **Preregister everything, then lock**

#### R19: Blind Confirmation
- **New seed, new instances, new hidden test bank, no model selection, no tuning**
- **Minimum:** N_test ≥ 200 per primary condition
- **Primary gate:** H1: A > 0, with Holm or Benjamini-Hochberg correction
- **Outcome:** 🟢 confirmed, 🟡 unresolved, 🔴 falsified — all published

#### R20: Multi-QPU Boundary Validation
- **Test on ≥2 hardware classes:** trapped ion, superconducting, neutral atom
- **Question:** Is the boundary algorithmic or hardware-specific?
- **QA4 gate:** Same trend across ≥2 implementations
- **Reuse:** Piast-Q access, `gqo_qss/run_piastq.py`

---

## End-to-End Case Studies

Four case studies applying the full WHERE/HOW/RUN stack to specific algorithm families, running in parallel with Waves 3-4:

| Case Study | Algorithm | Application | Key Question |
|-----------|-----------|-------------|-------------|
| R19-CS | QAOA | MaxCut, MWIS, Portfolio, Scheduling | Does WestQuant pipeline beat strongest classical + published hybrid at matched budget? |
| R20-CS | VQE/ADAPT-VQE | ANNNI, LiH/BeH₂, N₂ stretch, Hubbard | Can WestQuant predict the right physical basin before VQE starts? |
| R21-CS | GQE+QSCI | N₂ stretch, SnO, aromatics, [2Fe-2S] | Is p_useful(Q) > p_useful(C) at same subspace budget? |
| R22-CS | QAE | Option pricing, CVA, reliability, UQ | When does C_total^QAE < C_total^classical at same accuracy? |

---

## Baseline Hierarchy (locked for all projects)

| Level | Required |
|-------|----------|
| B0 Reference | Exact solution / certified optimum where possible |
| B1 Classical | Strongest reasonable modern classical solver |
| B2 Canonical Quantum | Standard version of the algorithm |
| B3 Published Frontier | Strong published variant (frozen at preregistration) |
| B4 WestQuant | Our full method |

---

## Publication Plan (5 papers)

| Paper | Source | Content |
|-------|--------|---------|
| A | QMT (done) | When Do Entangling Gates Add Predictive Signal? |
| B | R12-R14 | Quantum-Selected Search Beyond Classical Recovery |
| C | R09-R11 | Temporal Quantum Reservoirs for Optimization Dynamics |
| D | R02, R04, R15, R16 | A Resource-Normalized Benchmark for Hybrid Quantum Optimization |
| E (flagship) | R01-R20 | Mapping the Quantum Advantage Boundary |

Flagship main figure: `A(n, p, m, D, B, ε)` as phase diagrams.

---

## Compute Budget

| Tier | CPU-core-hours | GPU-hours | QPU-hours | Storage |
|------|---------------|-----------|-----------|--------|
| Minimum viable | 300k-500k | 8k-15k | 15-30 | 5 TB |
| Recommended | 0.8-1.5M | 20k-40k | 40-80 | 10 TB |
| Stretch (post-R18) | — | 50k-100k+ | 100-200 | 15 TB |

Simulator scaling: 8-20 qubits (exhaustive), 24 (medium), 28 (selective), 32+ (frozen only), 36+ (tensor-network/QPU).

---

## Key Discovery Signals to Watch

1. **Sampling crossover before prediction crossover** — quantum more natural as sampler than predictor
2. **Correlation-order transition** — A < 0 for m=1,2 but A → 0 for m=3,4
3. **Landscape-dependent advantage** — A ≈ 0 on ER but A > 0 on frustrated/high-barrier instances

---

## What We Absolutely Do Not Do

- Weak classical baselines
- Post-hoc metric selection
- Cherry-picked QPU instances
- Larger hyperparameter budget for quantum than classical
- Using "quantum advantage" for QA0
- Publishing only green points

**All red points go into the Atlas.**

---

## End State

After 12 months: **WestQuant Quantum Advantage Boundary Atlas v1.0** — a public map of:
- Which methods have been tested
- Where classical still wins
- Where results are unresolved
- Which mechanisms appear promising
- What compute is required
- Which parameter regimes are worth the next QPU-dollar

This is potentially more valuable than a single quantum-advantage demonstration, because it shows the field where to look next.
