# R01 — Boundary Atlas Infrastructure

**Track:** Infrastructure (cross-cutting)
**Wave:** 1 (Months 1-3)
**Status:** ✅ Implemented (v0.1)

## Question

Can all experiments across R01-R20 be represented in a single schema without track-specific special fields?

## What This Project Builds

The **WestQuant Quantum Advantage Boundary Atlas** — a unified experiment registry that stores every result from every project in one schema, enabling cross-track analysis and the flagship phase diagram visualization.

### Components

| Component | File | Description |
|-----------|------|-------------|
| Schema | `atlas/schema.py` | `ExperimentRecord` dataclass with 40+ fields |
| Registry | `atlas/registry.py` | SQLite + Parquet backend, append-only |
| Ingestion | `atlas/ingest.py` | Converters for GQO/QMT/Q-SITE results |
| R01-R10 ingestion | `atlas/ingest_r01_r10.py` | Second-wave gate results |
| Query | `atlas/query.py` | Filter by track, size, method, QA level |
| Visualization | `atlas/visualize.py` | Phase diagrams, QA distribution, status pie |
| Reproduction | `reproduce_all.py` | Full reproduction pipeline |

### Data Model

Every experiment record contains:
- Identity: `experiment_id`, `timestamp`, `track`, `project`
- Problem: `problem_family`, `problem_size`, `difficulty`, `seed`, `problem_instance_id`
- Quantum: `quantum_method`, `circuit_family`, `qubits`, `depth`, `observable_order`, `shots`, `noise_model`, `hardware`
- Classical: `classical_method`, `classical_parameters`
- Data split: `training_size`, `test_size`
- Metrics: `metric_name`, `metric_Q`, `metric_C`, `delta`, `confidence_interval_low/high`, `effect_size`
- Resources: `cpu_seconds`, `gpu_seconds`, `qpu_seconds`, `memory_peak_mb`
- Classification: `qa_level`, `status`, `preregistered`
- Provenance: `code_commit`, `dataset_hash`
- Extensible: `metadata` dict for track-specific details

## Gate

**R01-G1:** 100% of future R02-R20 experiments can be logged without track-specific special fields outside the extensible metadata block.

**Status:** ✅ PASS — schema is track-agnostic, all track-specific data goes in `metadata`

## Output

Atlas v0.1 with seed records from:
- GQO+QSS final experiment (270 records)
- GQO basin statistics (372 records)
- Ground truth certificates (150 records)
- QMT reservoir computing (13 records)
- R01-R10 second wave gate results (18 records)

**Total:** 823+ records (target was ≥500)

## Compute

Negligible — runs on laptop.

## Usage

```bash
# Ingest all existing results
python -m projects.QAB.atlas.ingest --summary

# Ingest R01-R10 second wave
python -m projects.QAB.atlas.ingest_r01_r10

# Query the Atlas
python -m projects.QAB.atlas.query --track quantum_sampling --size 28
python -m projects.QAB.atlas.query --status classical_advantage --limit 20

# Visualize
python -m projects.QAB.atlas.visualize --output figures/

# Full reproduction
python projects/QAB/reproduce_all.py
```
