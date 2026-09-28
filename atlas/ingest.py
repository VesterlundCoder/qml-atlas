"""Atlas ingestion: convert existing experiment results to ExperimentRecords.

Supports:
  - GQO+QSS final experiment (logs/gqo_qss_final_experiment.json)
  - GQO+QSS basin statistics (results/gqo_basin_statistics.json)
  - QMT falsification results (if available)
  - Q-SITE results (if available)

Usage:
    python -m projects.QAB.atlas.ingest              # Ingest all
    python -m projects.QAB.atlas.ingest --gqo-only   # Just GQO
    python -m projects.QAB.atlas.ingest --summary   # Print summary
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from projects.QAB.atlas.schema import ExperimentRecord
from projects.QAB.atlas.registry import AtlasRegistry

BASE = Path(__file__).resolve().parents[3]  # westquant/
ATLAS_DIR = Path(__file__).resolve().parent / "v0.1"
ATLAS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = ATLAS_DIR / "atlas.db"


def _safe_get(d: dict, *keys, default=0.0):
    """Safely traverse nested dict."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d


def ingest_gqo_final_experiment(registry: AtlasRegistry) -> int:
    """Ingest GQO+QSS final experiment results.

    Produces paired records: one per (instance, sampler) pair.
    Classical baseline for delta computation is SA (strongest non-tabu classical).
    """
    path = BASE / "logs" / "gqo_qss_final_experiment.json"
    if not path.exists():
        print(f"  [SKIP] {path} not found")
        return 0

    with open(path) as f:
        data = json.load(f)

    records = []
    # results is a dict keyed by size string -> list of instance dicts
    results = data.get("results", {})
    instances = []
    if isinstance(results, dict):
        for size_key, inst_list in results.items():
            if isinstance(inst_list, list):
                instances.extend(inst_list)
    elif isinstance(results, list):
        instances = results

    # Build SA lookup for paired delta
    sa_results = {}
    for inst in instances:
        n = inst.get("n", inst.get("size", 0))
        seed = inst.get("seed", 0)
        samplers = inst.get("samplers", inst.get("results", {}))
        for name, result in samplers.items():
            if name == "simulated_annealing":
                key = (n, seed)
                sa_results[key] = result.get("p_r", result.get("mean_p_r", 0.0))

    for inst in instances:
        n = inst.get("n", inst.get("size", 0))
        seed = inst.get("seed", 0)
        instance_id = inst.get("graph_id", inst.get("instance_id", f"mwis_n{n}_s{seed}"))
        samplers = inst.get("samplers", inst.get("results", {}))

        sa_p_r = sa_results.get((n, seed), 0.0)

        for sampler_name, result in samplers.items():
            p_r = result.get("p_r", result.get("mean_p_r", 0.0))
            ci_low = result.get("ci_low", result.get("confidence_interval_low", 0.0))
            ci_high = result.get("ci_high", result.get("confidence_interval_high", 0.0))
            b_delta = result.get("b_delta_95", result.get("B_delta_95", 0.0))

            # Determine track and classification
            is_quantum = sampler_name in ("oracle_qaoa", "warm_start_qaoa", "learned_qaoa",
                                           "generative_policy", "qaoa")
            track = "quantum_sampling" if is_quantum else "infrastructure"
            classical_method = "simulated_annealing" if is_quantum else ""

            # QA level assessment
            delta = p_r - sa_p_r if is_quantum else 0.0
            if is_quantum:
                if delta > 0 and ci_low > 0:
                    status = "quantum_candidate"
                    qa_level = 1
                elif delta < 0:
                    status = "classical_advantage"
                    qa_level = 0 if p_r > 0 else -1
                else:
                    status = "unresolved"
                    qa_level = 0
            else:
                status = "not_assessed"
                qa_level = -1

            record = ExperimentRecord(
                track=track,
                project="R12",
                problem_family="mwis",
                problem_size=n,
                difficulty="D2",
                seed=seed,
                problem_instance_id=instance_id,
                quantum_method=sampler_name if is_quantum else "",
                qubits=n,
                depth=1 if "qaoa" in sampler_name else 0,
                shots=200,
                noise_model="ideal",
                hardware="simulator",
                classical_method=sampler_name if not is_quantum else "simulated_annealing",
                test_size=6,
                metric_name="p_r",
                metric_Q=p_r if is_quantum else 0.0,
                metric_C=p_r if not is_quantum else sa_p_r,
                delta=delta,
                confidence_interval_low=ci_low,
                confidence_interval_high=ci_high,
                qa_level=qa_level,
                status=status,
                preregistered=True,
                metadata={
                    "sampler": sampler_name,
                    "b_delta_95": b_delta,
                    "radius": 2,
                    "budget": 200,
                    "source": "gqo_qss_final_experiment",
                },
            )
            records.append(record)

    count = registry.insert_many(records)
    print(f"  [GQO] Ingested {count} records from final experiment")
    return count


def ingest_gqo_basin_statistics(registry: AtlasRegistry) -> int:
    """Ingest GQO+QSS basin statistics as landscape records."""
    path = BASE / "results" / "gqo_basin_statistics.json"
    if not path.exists():
        print(f"  [SKIP] {path} not found")
        return 0

    with open(path) as f:
        data = json.load(f)

    records = []

    # data is a flat list of per-instance per-radius records
    if isinstance(data, list):
        for entry in data:
            n = entry.get("n", 0)
            seed = entry.get("seed", 0)
            r = entry.get("radius", 0)
            basin_size = entry.get("basin_size", 0)
            basin_fraction = entry.get("basin_fraction", 0.0)
            graph_id = entry.get("graph_id", f"mwis_n{n}_s{seed}")

            record = ExperimentRecord(
                track="infrastructure",
                project="R03",
                problem_family="mwis",
                problem_size=n,
                difficulty="D2",
                seed=seed,
                problem_instance_id=graph_id,
                metric_name="basin_fraction",
                metric_C=basin_fraction,
                status="not_assessed",
                metadata={
                    "radius": r,
                    "basin_size": basin_size,
                    "n_optimal": entry.get("n_optimal", 0),
                    "dim": entry.get("dim", 2**n),
                    "opt_value": entry.get("opt_value", 0.0),
                    "source": "gqo_basin_statistics",
                    "type": "landscape",
                },
            )
            records.append(record)

    # Also compute aggregate phase diagram (mean P_recover by n, r)
    if records:
        from collections import defaultdict
        import numpy as np
        phase_data = defaultdict(list)
        for r in records:
            n = r.problem_size
            radius = r.metadata.get("radius", 0)
            phase_data[(n, radius)].append(r.metric_C)

        for (n, radius), fractions in phase_data.items():
            mean_p = float(np.mean(fractions))
            # P_recover for uniform sampling at B=200
            p_recover = 1 - (1 - mean_p) ** 200

            phase_record = ExperimentRecord(
                track="infrastructure",
                project="R01",
                problem_family="mwis",
                problem_size=n,
                difficulty="D2",
                quantum_method="uniform",
                qubits=n,
                shots=200,
                noise_model="ideal",
                hardware="simulator",
                classical_method="uniform",
                metric_name="p_recover",
                metric_C=p_recover,
                metric_Q=p_recover,
                status="not_assessed",
                metadata={
                    "radius": radius,
                    "budget": 200,
                    "mean_basin_fraction": mean_p,
                    "n_instances": len(fractions),
                    "source": "gqo_basin_statistics",
                    "type": "phase_diagram",
                },
            )
            records.append(phase_record)

    count = registry.insert_many(records)
    print(f"  [GQO-Basin] Ingested {count} records from basin statistics")
    return count


def ingest_gqo_ground_truth(registry: AtlasRegistry) -> int:
    """Ingest ground truth certificates as reference records."""
    cert_dir = BASE / "data" / "ground_truth_certificates"
    if not cert_dir.exists():
        print(f"  [SKIP] {cert_dir} not found")
        return 0

    records = []
    for cert_path in sorted(cert_dir.glob("*.json")):
        with open(cert_path) as f:
            cert = json.load(f)

        n = cert.get("n", 0)
        seed = cert.get("seed", 0)
        instance_id = cert.get("instance_id", f"mwis_n{n}_s{seed}")

        record = ExperimentRecord(
            track="infrastructure",
            project="R01",
            problem_family="mwis",
            problem_size=n,
            difficulty="D2",
            seed=seed,
            problem_instance_id=instance_id,
            classical_method="cbc_bruteforce",
            metric_name="optimal_value",
            metric_C=cert.get("opt_value", 0.0),
            status="not_assessed",
            metadata={
                "solver_status": cert.get("solver_status", "OPTIMAL"),
                "solver_version": cert.get("solver_version", ""),
                "runtime": cert.get("runtime", 0.0),
                "brute_force_verified": cert.get("brute_force_verified", False),
                "source": "ground_truth_certificates",
                "type": "certification",
            },
        )
        records.append(record)

    count = registry.insert_many(records)
    print(f"  [GQO-Cert] Ingested {count} ground truth certificates")
    return count


def ingest_qmt_results(registry: AtlasRegistry) -> int:
    """Ingest QMT falsification results if available."""
    qmt_path = BASE / "projects" / "QAB" / "links" / "qmt" / "results"
    if not qmt_path.exists():
        # Try absolute path
        qmt_path = Path("/Users/davidvesterlund/freedomcode/freedomcode/stringtheory/quantum_micro_teacher/quantum_micro_teacher/qmt/results")
    if not qmt_path.exists():
        print(f"  [SKIP] QMT results not found")
        return 0

    records = []
    for result_file in sorted(qmt_path.glob("*.json")):
        with open(result_file) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue

        # QMT results vary in format; extract what we can
        n = data.get("n_qubits", data.get("n", 8))
        method = data.get("method", data.get("quantum_method", "qrc"))
        classical = data.get("classical_method", data.get("baseline", "random_forest"))
        metric_q = data.get("quantum_score", data.get("metric_Q", 0.0))
        metric_c = data.get("classical_score", data.get("metric_C", 0.0))

        record = ExperimentRecord(
            track="quantum_reservoir",
            project="R09",
            problem_family=data.get("problem_family", "synthetic"),
            problem_size=n,
            quantum_method=method,
            qubits=n,
            depth=data.get("depth", data.get("p", 1)),
            classical_method=classical,
            metric_name=data.get("metric_name", "r2_score"),
            metric_Q=metric_q,
            metric_C=metric_c,
            delta=metric_q - metric_c,
            status="classical_advantage" if metric_q < metric_c else "unresolved",
            qa_level=0 if metric_q != metric_c else -1,
            metadata={
                "source": "qmt_results",
                **{k: v for k, v in data.items() if k not in
                   ("n_qubits", "n", "method", "quantum_method", "classical_method",
                    "baseline", "quantum_score", "classical_score", "metric_Q", "metric_C")}
            },
        )
        records.append(record)

    count = registry.insert_many(records)
    print(f"  [QMT] Ingested {count} reservoir computing records")
    return count


def ingest_qsite_results(registry: AtlasRegistry) -> int:
    """Ingest Q-SITE results if available."""
    qsite_path = BASE / "projects" / "QAB" / "links" / "qsite" / "reports"
    if not qsite_path.exists():
        qsite_path = Path("/Users/davidvesterlund/freedomcode/freedomcode/stringtheory/qla_studio_v0.2/qla_representation_lab/qsite_westquant/reports")
    if not qsite_path.exists():
        print(f"  [SKIP] Q-SITE results not found")
        return 0

    records = []
    for result_file in sorted(qsite_path.glob("*.json")):
        with open(result_file) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue

        record = ExperimentRecord(
            track="quantum_optimization",
            project="R20",
            problem_family=data.get("problem_family", "vqe"),
            problem_size=data.get("n_qubits", data.get("n", 0)),
            quantum_method=data.get("ansatz", data.get("quantum_method", "hva")),
            qubits=data.get("n_qubits", 0),
            depth=data.get("depth", 0),
            classical_method=data.get("classical_method", "pyscf"),
            metric_name=data.get("metric_name", "energy_error_mha"),
            metric_Q=data.get("quantum_energy_error", data.get("metric_Q", 0.0)),
            metric_C=data.get("classical_energy_error", data.get("metric_C", 0.0)),
            delta=data.get("delta", 0.0),
            status="not_assessed",
            metadata={"source": "qsite_results", **data},
        )
        records.append(record)

    count = registry.insert_many(records)
    print(f"  [Q-SITE] Ingested {count} VQE records")
    return count


def ingest_all(registry: AtlasRegistry) -> dict[str, int]:
    """Ingest all available existing results."""
    counts = {}
    print("Ingesting existing experiment results into Atlas...")
    counts["gqo_final"] = ingest_gqo_final_experiment(registry)
    counts["gqo_basin"] = ingest_gqo_basin_statistics(registry)
    counts["gqo_cert"] = ingest_gqo_ground_truth(registry)
    counts["qmt"] = ingest_qmt_results(registry)
    counts["qsite"] = ingest_qsite_results(registry)
    total = sum(counts.values())
    print(f"\nTotal: {total} records ingested")
    return counts


def main():
    parser = argparse.ArgumentParser(description="Ingest existing results into Atlas")
    parser.add_argument("--gqo-only", action="store_true", help="Only ingest GQO results")
    parser.add_argument("--summary", action="store_true", help="Print Atlas summary after ingestion")
    args = parser.parse_args()

    registry = AtlasRegistry(DB_PATH)

    if args.gqo_only:
        ingest_gqo_final_experiment(registry)
        ingest_gqo_basin_statistics(registry)
        ingest_gqo_ground_truth(registry)
    else:
        ingest_all(registry)

    if args.summary:
        s = registry.summary()
        print(f"\nAtlas Summary:")
        print(f"  Total records: {s['total_records']}")
        print(f"  By status: {s['by_status']}")
        print(f"  By track: {s['by_track']}")
        print(f"  DB: {s['db_path']}")

    # Export
    parquet_path = ATLAS_DIR / "atlas.parquet"
    n = registry.export_parquet(parquet_path)
    print(f"  Exported {n} records to {parquet_path}")


if __name__ == "__main__":
    main()
