# WestQuant Quantum Advantage Boundary (QAB)

> **We do not search for evidence of quantum advantage. We search for the boundary at which it becomes possible.**

A 12-month systematic falsification program across quantum learning, sampling, optimization, and reservoir computing, producing the **WestQuant Quantum Advantage Boundary Atlas**.

## Quick Start

```bash
# Ingest existing results into Atlas v0.1
python -m projects.QAB.atlas.ingest

# Query the Atlas
python -m projects.QAB.atlas.query --track sampling --size 28

# Visualize phase diagrams
python -m projects.QAB.atlas.visualize --output figures/

# Full reproduction pipeline
python projects/QAB/reproduce_all.py
```

## Structure

```
projects/QAB/
├── MASTER_RESEARCH_PLAN.md    # Full R01-R20 plan
├── atlas/                      # Experiment registry (R01)
├── config/                     # QA ladder, resource model, gates
├── protocols/                  # Preregistration, fairness, baselines
├── links/                      # Symlinks to existing code
├── r01-r20/                    # Project directories
├── reports/                    # Status reports
└── reproduce_all.py            # Reproduction pipeline
```

## Quantum Advantage Ladder

| Level | Definition |
|-------|-----------|
| QA0 | Quantum changes representation/dynamics measurably |
| QA1 | Better quality on frozen held-out data |
| QA2 | Better sample efficiency |
| QA3 | Better total resource efficiency |
| QA4 | Advantage grows with scale |
| QA5 | Complexity-theoretic separation |

## Four Waves

1. **Wave 1 (Months 1-3):** Foundation — R01-R05 (Atlas, classical frontier, landscape, resources, difficulty)
2. **Wave 2 (Months 4-6):** Discovery — R06-R11 (feature maps, surrogate attack, sample efficiency, reservoirs, correlation order)
3. **Wave 3 (Months 7-9):** Boundary Attack — R12-R17 (recovery basin, sample complexity, generative sampler, hard cores, QAOA family, active search)
4. **Wave 4 (Months 10-12):** Confirmation — R18-R20 (crossover prediction, blind confirmation, multi-QPU validation)

## Existing Results in Atlas v0.1

- **GQO+QSS:** 270 records (9 samplers × 30 instances, falsification study)
- **QMT:** Reservoir computing falsification records
- **Q-SITE:** VQE reference-state records
- **GQO basin statistics:** Phase diagram records

## Links to Existing Infrastructure

- `links/gqo_qss` → MWIS sampling, recovery basins, QAOA
- `links/qmt` → Quantum reservoir computing
- `links/qsite` → VQE reference-state optimization
- `links/wqt20` → Representation scheduling model
- `links/qcsc` → Quantum-centric supercomputing orchestrator

## License

MIT
