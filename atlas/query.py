"""Atlas query API: filter and aggregate experiment records.

Usage:
    python -m projects.QAB.atlas.query --track quantum_sampling
    python -m projects.QAB.atlas.query --size 28 --status classical_advantage
    python -m projects.QAB.atlas.query --summary
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from projects.QAB.atlas.registry import AtlasRegistry

ATLAS_DIR = Path(__file__).resolve().parent / "v0.1"
DB_PATH = ATLAS_DIR / "atlas.db"


def main():
    parser = argparse.ArgumentParser(description="Query the Atlas")
    parser.add_argument("--track", type=str, default=None)
    parser.add_argument("--project", type=str, default=None)
    parser.add_argument("--family", type=str, default=None)
    parser.add_argument("--size", type=int, default=None)
    parser.add_argument("--quantum-method", type=str, default=None)
    parser.add_argument("--classical-method", type=str, default=None)
    parser.add_argument("--qa-level", type=int, default=None)
    parser.add_argument("--status", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    registry = AtlasRegistry(DB_PATH)

    if args.summary:
        s = registry.summary()
        print(f"Atlas Summary")
        print(f"  Total records: {s['total_records']}")
        print(f"  By status: {json.dumps(s['by_status'], indent=2)}")
        print(f"  By track: {json.dumps(s['by_track'], indent=2)}")
        print(f"  DB: {s['db_path']}")
        return

    records = registry.query(
        track=args.track,
        project=args.project,
        problem_family=args.family,
        problem_size=args.size,
        quantum_method=args.quantum_method,
        classical_method=args.classical_method,
        qa_level=args.qa_level,
        status=args.status,
        limit=args.limit,
    )

    if args.json:
        print(json.dumps([r.to_dict() for r in records], indent=2, default=str))
    else:
        print(f"Found {len(records)} records:")
        for r in records[:50]:
            print(f"  [{r.project}] {r.problem_instance_id} | Q={r.quantum_method or r.classical_method} "
                  f"| {r.metric_name}={r.metric_Q or r.metric_C:.4f} "
                  f"| delta={r.delta:+.4f} | QA{r.qa_level} | {r.status}")
        if len(records) > 50:
            print(f"  ... and {len(records) - 50} more")


if __name__ == "__main__":
    main()
