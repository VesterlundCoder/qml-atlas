"""Ingest R01-R10 upgraded results from second wave (2026-09-26).

These results come from a separate machine and represent the original
WestQuant R01-R10 research projects (representation scheduling, reservoir
computing, QEC, etc.), not the QAB R01-R20 program. They are ingested as
seed records with track="infrastructure" and project="R01".."R10" (original).

Usage:
    python -m projects.QAB.atlas.ingest_r01_r10
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure westquant root is on path
BASE = Path(__file__).resolve().parents[3]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from projects.QAB.atlas.schema import ExperimentRecord
from projects.QAB.atlas.registry import AtlasRegistry

ATLAS_DIR = Path(__file__).resolve().parent / "v0.1"
DB_PATH = ATLAS_DIR / "atlas.db"


# R01-R10 upgraded results data (from second wave, 2026-09-26)
R01_R10_RESULTS = [
    {
        "project": "R01",
        "name": "Config Prediction (Direct)",
        "track": "quantum_learning",
        "status": "classical_advantage",  # RED
        "qa_level": 0,
        "gates": [
            {"name": "Generalization score", "threshold": 0.03, "value": 0.000, "pass": False},
            {"name": "Win rate", "threshold": 0.55, "value": 0.000, "pass": False},
        ],
        "gates_passed": 0,
        "gates_total": 2,
        "upgrade": "Direct config prediction, 68 circuits",
        "metadata": {
            "root_cause": "Only 4 circuit features (depth, one_q, two_q, n_qubits) — insufficient information",
            "best_config": "Almost always (0, trivial, basic, translator) — trivial prediction task",
        },
    },
    {
        "project": "R02",
        "name": "Zero-Shot Transfer",
        "track": "quantum_learning",
        "status": "unresolved",  # YELLOW
        "qa_level": 0,
        "gates": [
            {"name": "Zero-shot transfer", "threshold": 0.95, "value": 0.438, "pass": False},
            {"name": "Framework variance reduction", "threshold": 0.20, "value": 0.998, "pass": True},
        ],
        "gates_passed": 1,
        "gates_total": 2,
        "upgrade": "Needs real multi-framework data",
        "metadata": {
            "issue": "Only Qiskit data is real. Need real PyTKET and PennyLane compilation trajectories.",
        },
    },
    {
        "project": "R03",
        "name": "Distillation + Inference Acceleration",
        "track": "quantum_learning",
        "status": "unresolved",  # YELLOW (improved — G1 now passes)
        "qa_level": 1,
        "gates": [
            {"name": "Distillation retention", "threshold": 0.90, "value": 0.9999, "pass": True},
            {"name": "Inference acceleration", "threshold": 10.0, "value": 170.7, "pass": True},
        ],
        "gates_passed": 2,
        "gates_total": 2,
        "upgrade": "Direct config prediction (was 8-action abstraction), 68 circuits (was 64)",
        "metadata": {
            "note": "policy_vs_search_score = 99.99% (was 18.75%) — now passes G1",
            "caveat": "R01 still fails because best config is almost always the simplest one",
        },
    },
    {
        "project": "R04",
        "name": "Quantum Reservoir for Solver Selection (Negative Result)",
        "track": "quantum_reservoir",
        "status": "classical_advantage",  # CLOSED
        "qa_level": -1,
        "gates": [],
        "gates_passed": 0,
        "gates_total": 0,
        "upgrade": "Documented and closed",
        "metadata": {
            "finding": "Quantum reservoir features don't add predictive value for solver selection",
            "negative_result": True,
            "report": "reports/R04_NEGATIVE_RESULT.md",
        },
    },
    {
        "project": "R05",
        "name": "Boundary Predictability (Honest Controls)",
        "track": "quantum_learning",
        "status": "unresolved",  # YELLOW
        "qa_level": 0,
        "gates": [
            {"name": "Boundary predictability", "threshold": 0.70, "value": 1.000, "pass": True},
            {"name": "OOD boundary transfer", "threshold": 0.65, "value": 0.500, "pass": False},
        ],
        "gates_passed": 1,
        "gates_total": 2,
        "upgrade": "5k graphs + honest controls (random Fourier, random NN, random quantum params)",
        "metadata": {
            "finding": "Quantum delta R2 = +0.0024, but Random NN delta = +0.0046 (better!)",
            "conclusion": "Quantum features don't add quantum-specific information — they just add random dimensions",
        },
    },
    {
        "project": "R06",
        "name": "Regret Reduction (Honest Controls)",
        "track": "quantum_learning",
        "status": "unresolved",  # YELLOW
        "qa_level": 0,
        "gates": [
            {"name": "Regret reduction", "threshold": 0.10, "value": 0.044, "pass": False},
            {"name": "OOD regret reduction", "threshold": 0.05, "value": 0.068, "pass": True},
        ],
        "gates_passed": 1,
        "gates_total": 2,
        "upgrade": "5k graphs + honest controls",
        "metadata": {
            "finding": "Quantum regret reduction = 4.4%, but Random Quantum = 6.0% (better!)",
            "conclusion": "Quantum features don't outperform matched classical controls",
        },
    },
    {
        "project": "R07",
        "name": "8q/12q INDEP+MAPPED Evaluation",
        "track": "quantum_learning",
        "status": "not_assessed",  # PENDING
        "qa_level": -1,
        "gates": [],
        "gates_passed": 0,
        "gates_total": 0,
        "upgrade": "Running 8q/12q circuits at INDEP/MAPPED levels",
        "metadata": {
            "status": "running",
            "description": "Deeper circuits where representation choice matters more",
        },
    },
    {
        "project": "R08",
        "name": "Adaptive Drift Control (GREEN, Preregistered)",
        "track": "quantum_reservoir",
        "status": "quantum_candidate",  # GREEN
        "qa_level": 1,
        "gates": [
            {"name": "Control improvement", "threshold": 0.15, "value": 0.8615, "pass": True},
            {"name": "Recovery latency", "threshold": 0.10, "value": 0.9991, "pass": True},
        ],
        "gates_passed": 2,
        "gates_total": 2,
        "upgrade": "10,000 scenarios (was 200), 3-seed study (seeds 11, 23, 37)",
        "metadata": {
            "error_reduction": "86.15% ± 0.14%",
            "latency_reduction": "99.91% ± 0.05%",
            "seeds": [11, 23, 37],
            "all_seeds_pass": True,
            "preregistration": "projects/R08/preregistration.json",
            "ready_for": "Full-scale study (10k+ scenarios, held-out dynamics)",
        },
    },
    {
        "project": "R09",
        "name": "Trainable SNN Pareto (YELLOW)",
        "track": "quantum_reservoir",
        "status": "unresolved",  # YELLOW
        "qa_level": 0,
        "gates": [
            {"name": "Pareto efficiency", "threshold": 0.10, "value": 3.658, "pass": True},
            {"name": "Accuracy floor", "threshold": 0.98, "value": 0.754, "pass": False},
        ],
        "gates_passed": 1,
        "gates_total": 2,
        "upgrade": "PyTorch LIF SNN with surrogate gradient (was hand-crafted event statistics)",
        "metadata": {
            "snn_accuracy": 0.51,
            "dense_mlp_accuracy": 0.68,
            "randomforest_accuracy": 0.86,
            "pareto_efficiency": 3.658,
            "accuracy_ratio": 0.754,
            "finding": "SNN better than hand-crafted encoding but still can't match dense baselines",
        },
    },
    {
        "project": "R10",
        "name": "Neuromorphic QEC (GREEN, Upgraded)",
        "track": "quantum_reservoir",
        "status": "quantum_candidate",  # GREEN
        "qa_level": 1,
        "gates": [
            {"name": "Event sparsity", "threshold": 0.30, "value": 0.847, "pass": True},
            {"name": "Predictive retention", "threshold": 0.98, "value": 0.9927, "pass": True},
        ],
        "gates_passed": 2,
        "gates_total": 2,
        "upgrade": "20,000 shots (was 5,000), +autocorrelation, +transitions, +spectral, +spatial correlation features",
        "metadata": {
            "compute_reduction": 0.847,
            "predictive_retention": 0.9927,
            "n_shots": 20000,
            "models": ["RandomForest", "MLP"],
            "both_models_achieve": "99.27% retention ratio",
            "ready_for": "Publication",
        },
    },
]


def ingest_r01_r10_results(registry: AtlasRegistry) -> int:
    """Ingest R01-R10 upgraded results from second wave."""
    records = []

    for result in R01_R10_RESULTS:
        project = result["project"]
        track = result["track"]

        # Create one record per gate result
        if result["gates"]:
            for gate in result["gates"]:
                record = ExperimentRecord(
                    track=track,
                    project=f"orig_{project}",  # prefix to distinguish from QAB R01-R20
                    problem_family="circuit_optimization",
                    problem_size=0,  # varies
                    quantum_method="westquant_policy" if "quantum" in track else "",
                    classical_method=gate.get("name", "").lower().replace(" ", "_"),
                    metric_name=gate["name"].lower().replace(" ", "_"),
                    metric_Q=gate["value"],
                    metric_C=gate["threshold"],
                    delta=gate["value"] - gate["threshold"],
                    status=result["status"],
                    qa_level=result["qa_level"],
                    preregistered=result["project"] == "R08",  # R08 is preregistered
                    metadata={
                        "project_name": result["name"],
                        "gate_name": gate["name"],
                        "gate_threshold": gate["threshold"],
                        "gate_value": gate["value"],
                        "gate_pass": gate["pass"],
                        "gates_passed": result["gates_passed"],
                        "gates_total": result["gates_total"],
                        "upgrade": result["upgrade"],
                        "source": "r01_r10_second_wave",
                        "date": "2026-09-26",
                        **result.get("metadata", {}),
                    },
                )
                records.append(record)
        else:
            # No gates (PENDING or CLOSED) — create a summary record
            record = ExperimentRecord(
                track=track,
                project=f"orig_{project}",
                problem_family="circuit_optimization",
                quantum_method="westquant_policy" if "quantum" in track else "",
                metric_name="summary",
                metric_Q=float(result["gates_passed"]),
                metric_C=float(result["gates_total"]),
                delta=float(result["gates_passed"]) - float(result["gates_total"]),
                status=result["status"],
                qa_level=result["qa_level"],
                metadata={
                    "project_name": result["name"],
                    "gates_passed": result["gates_passed"],
                    "gates_total": result["gates_total"],
                    "upgrade": result["upgrade"],
                    "source": "r01_r10_second_wave",
                    "date": "2026-09-26",
                    **result.get("metadata", {}),
                },
            )
            records.append(record)

    count = registry.insert_many(records)
    print(f"  [R01-R10] Ingested {count} records from second wave (2026-09-26)")
    return count


def main():
    registry = AtlasRegistry(DB_PATH)
    print("Ingesting R01-R10 upgraded results from second wave...")
    count = ingest_r01_r10_results(registry)

    s = registry.summary()
    print(f"\nAtlas Summary:")
    print(f"  Total records: {s['total_records']}")
    print(f"  By status: {s['by_status']}")
    print(f"  By track: {s['by_track']}")

    # Export updated parquet
    parquet_path = ATLAS_DIR / "atlas.parquet"
    n = registry.export_parquet(parquet_path)
    print(f"  Exported {n} records to {parquet_path}")

    # Print R01-R10 summary
    print(f"\nR01-R10 Second Wave Summary:")
    print(f"  {'Project':<8} {'Status':<20} {'Gates':<8} {'QA':<4} {'Name'}")
    print(f"  {'-'*70}")
    for result in R01_R10_RESULTS:
        status_emoji = {
            "quantum_candidate": "GREEN",
            "unresolved": "YELLOW",
            "classical_advantage": "RED",
            "not_assessed": "PENDING",
        }.get(result["status"], result["status"])
        print(f"  {result['project']:<8} {status_emoji:<20} {result['gates_passed']}/{result['gates_total']:<6} QA{result['qa_level']:<2} {result['name']}")


if __name__ == "__main__":
    main()
