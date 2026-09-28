# Wave 2 Status Report — R06-R17 Local Discovery

**Date:** 2026-09-28
**Approach:** Multi-fidelity (L0-L3 + H1) — bred lokal discovery → selektiv scaling → frozen confirmation
**Status:** ✅ Three parallel pipelines implemented and running locally

## Multi-Fidelity Design Documented

`MULTI_FIDELITY_DESIGN.md` documents the corrected scope:

```
R01-R18: huvudsakligen lokal forskning
R19: lokal eller extern beroende på var boundary hamnar
R20: kräver externa QPU:er för slutgiltig validering
```

Five fidelity levels: L0 (exact, n≤20), L1 (selective exact, n=21-28), L2 (approximate, n=24-40+), L3 (frozen confirmation), H1 (external QPU).

## Three Parallel Pipelines

### Pipeline A: QML (R06 → R07 → R08 → R11)

**R06 — Quantum Feature Map Scaling:** ✅ Implemented and run
- 48 records generated (ry_rxx, heisenberg × n=8,12 × p=1,2 × m=1,2)
- Result: classical advantage everywhere (mean delta = +4.81)
- Simple QML features cannot beat greedy baseline — expected at this scale

### Pipeline B: Sampling (R12 → R13 → R14)

**R12 — Recovery-Basin Sampling:** ✅ Implemented and run
- 12 records generated (mwis × n=12 × r=0,1 × B=100)
- Exact basin enumeration optimized (mark from optimal states outward)
- Result: SA p_r=0.13, greedy p_r=0.04, QAOA p_r=0.00, uniform p_r≈basin_fraction
- Classical samplers dominate — consistent with GQO+QSS falsification

### Pipeline C: Optimization (R15 → R16)

**R16 — QAOA Family Boundary:** ✅ Implemented and run
- 6 records generated (mwis × n=8 × p=1)
- Result: all QAOA variants lose to classical frontier
  - standard_qaoa: delta = +95.4 (very poor)
  - optimized_qaoa: delta = +5.1 (poor)
  - warm_start_qaoa: delta = +1.1 (closest)
- Warm-start QAOA is the most promising variant — consistent with literature

### R17 — Active Boundary Search: ✅ Implemented and run
- Trained RF surrogate on 1842 Atlas records
- Suggests next experiments near |A(x)| ≈ 0 with high uncertainty
- Top suggestions: n=20-28, p=1-3, m=2-3 (near boundary region)
- Saved to `suggestions.json`

## Atlas After Wave 2

| Source | Records |
|--------|--------:|
| Wave 1 (R01-R05) | 450 |
| GQO+QSS seed | 805 |
| R01-R10 second wave | 18 |
| **R06 QML features** | **48** |
| **R12 Recovery basins** | **12** |
| **R16 QAOA boundary** | **6** |
| **Total** | **2282** |

## Status Distribution

| Status | Count | % |
|--------|------:|---:|
| not_assessed | 2044 | 89.5% |
| classical_advantage | 180 | 7.9% |
| unresolved | 50 | 2.2% |
| quantum_candidate | 8 | 0.4% |

## Key Findings So Far

1. **No quantum advantage found** at n=8-16 with simple circuits — consistent with GQO+QSS
2. **Warm-start QAOA** is the most promising QAOA variant (closest to classical)
3. **SA dominates** recovery-basin sampling at small scale
4. **Active boundary search** suggests n=20-28, p=1-3, m=2-3 as the interesting region
5. **All results are red/yellow** — no green from new experiments yet

## What's Next

1. **Scale R12 to n=16,20** with exact basins (the most promising local experiment)
2. **Run R07 surrogate attack** on R06 features (100% local)
3. **Run R08 sample efficiency** on cached R06 features (100% local)
4. **Scale R16 to n=12,16** with parameter transfer
5. **Feed R17 suggestions back** into R06/R12/R16
6. **Implement R09/R10** (reservoir computing) using QMT infrastructure
7. **Implement R11** (correlation order) with motif-aware correlators

## Files Created

```
projects/QAB/
├── MULTI_FIDELITY_DESIGN.md          # Multi-fidelity approach
├── r06_feature_map_scaling/run.py    # Pipeline A
├── r12_recovery_basin_sampling/run.py # Pipeline B
├── r16_qaoa_family_boundary/run.py    # Pipeline C
├── r17_active_boundary_search/run.py # Boundary search
├── r17_active_boundary_search/suggestions.json
└── reports/wave2_status.md           # This report
```
