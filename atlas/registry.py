"""Atlas registry: SQLite + Parquet backend for experiment records.

Append-only with provenance tracking. Supports querying by track, size,
method, QA level, and status.
"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

from projects.QAB.atlas.schema import ExperimentRecord


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    track TEXT NOT NULL DEFAULT '',
    project TEXT NOT NULL DEFAULT '',
    problem_family TEXT NOT NULL DEFAULT '',
    problem_size INTEGER NOT NULL DEFAULT 0,
    difficulty TEXT NOT NULL DEFAULT '',
    seed INTEGER NOT NULL DEFAULT 0,
    problem_instance_id TEXT NOT NULL DEFAULT '',
    quantum_method TEXT NOT NULL DEFAULT '',
    circuit_family TEXT NOT NULL DEFAULT '',
    qubits INTEGER NOT NULL DEFAULT 0,
    depth INTEGER NOT NULL DEFAULT 0,
    observable_order INTEGER NOT NULL DEFAULT 0,
    shots INTEGER NOT NULL DEFAULT 0,
    noise_model TEXT NOT NULL DEFAULT '',
    hardware TEXT NOT NULL DEFAULT '',
    classical_method TEXT NOT NULL DEFAULT '',
    classical_parameters TEXT NOT NULL DEFAULT '',
    training_size INTEGER NOT NULL DEFAULT 0,
    test_size INTEGER NOT NULL DEFAULT 0,
    metric_name TEXT NOT NULL DEFAULT '',
    metric_Q REAL NOT NULL DEFAULT 0.0,
    metric_C REAL NOT NULL DEFAULT 0.0,
    delta REAL NOT NULL DEFAULT 0.0,
    confidence_interval_low REAL NOT NULL DEFAULT 0.0,
    confidence_interval_high REAL NOT NULL DEFAULT 0.0,
    effect_size REAL NOT NULL DEFAULT 0.0,
    cpu_seconds REAL NOT NULL DEFAULT 0.0,
    gpu_seconds REAL NOT NULL DEFAULT 0.0,
    qpu_seconds REAL NOT NULL DEFAULT 0.0,
    memory_peak_mb REAL NOT NULL DEFAULT 0.0,
    qa_level INTEGER NOT NULL DEFAULT -1,
    status TEXT NOT NULL DEFAULT 'not_assessed',
    preregistered INTEGER NOT NULL DEFAULT 0,
    code_commit TEXT NOT NULL DEFAULT '',
    dataset_hash TEXT NOT NULL DEFAULT '',
    content_hash TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_track ON experiments(track);
CREATE INDEX IF NOT EXISTS idx_project ON experiments(project);
CREATE INDEX IF NOT EXISTS idx_size ON experiments(problem_size);
CREATE INDEX IF NOT EXISTS idx_qa ON experiments(qa_level);
CREATE INDEX IF NOT EXISTS idx_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_quantum_method ON experiments(quantum_method);
CREATE INDEX IF NOT EXISTS idx_classical_method ON experiments(classical_method);
CREATE INDEX IF NOT EXISTS idx_instance ON experiments(problem_instance_id);
"""


class AtlasRegistry:
    """SQLite-backed experiment registry."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)

    def insert(self, record: ExperimentRecord) -> str:
        """Insert a single record. Returns experiment_id."""
        d = record.to_dict()
        d["content_hash"] = record.content_hash()
        d["metadata_json"] = json.dumps(d.pop("metadata", {}), default=str)
        d["preregistered"] = int(d["preregistered"])
        cols = ", ".join(d.keys())
        placeholders = ", ".join(["?"] * len(d))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"INSERT OR REPLACE INTO experiments ({cols}) VALUES ({placeholders})",
                list(d.values())
            )
        return record.experiment_id

    def insert_many(self, records: list[ExperimentRecord]) -> int:
        """Insert multiple records. Returns count."""
        count = 0
        for r in records:
            self.insert(r)
            count += 1
        return count

    def query(
        self,
        track: Optional[str] = None,
        project: Optional[str] = None,
        problem_family: Optional[str] = None,
        problem_size: Optional[int] = None,
        quantum_method: Optional[str] = None,
        classical_method: Optional[str] = None,
        qa_level: Optional[int] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[ExperimentRecord]:
        """Query records by filters."""
        conditions = []
        params = []
        if track:
            conditions.append("track = ?")
            params.append(track)
        if project:
            conditions.append("project = ?")
            params.append(project)
        if problem_family:
            conditions.append("problem_family = ?")
            params.append(problem_family)
        if problem_size is not None:
            conditions.append("problem_size = ?")
            params.append(problem_size)
        if quantum_method:
            conditions.append("quantum_method = ?")
            params.append(quantum_method)
        if classical_method:
            conditions.append("classical_method = ?")
            params.append(classical_method)
        if qa_level is not None:
            conditions.append("qa_level = ?")
            params.append(qa_level)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM experiments{where} ORDER BY timestamp"
        if limit:
            sql += f" LIMIT {limit}"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()

        records = []
        for row in rows:
            d = dict(row)
            d["metadata"] = json.loads(d.pop("metadata_json", "{}"))
            d["preregistered"] = bool(d["preregistered"])
            records.append(ExperimentRecord.from_dict(d))
        return records

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0]

    def count_by_status(self) -> dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM experiments GROUP BY status"
            ).fetchall()
        return {row[0]: row[1] for row in rows}

    def count_by_track(self) -> dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT track, COUNT(*) FROM experiments GROUP BY track"
            ).fetchall()
        return {row[0]: row[1] for row in rows}

    def summary(self) -> dict[str, Any]:
        return {
            "total_records": self.count(),
            "by_status": self.count_by_status(),
            "by_track": self.count_by_track(),
            "db_path": str(self.db_path),
        }

    def export_parquet(self, path: str | Path) -> int:
        """Export all records to Parquet. Returns count."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            # Fallback: export as JSON
            records = self.query()
            path = Path(path).with_suffix(".json")
            with open(path, "w") as f:
                json.dump([r.to_dict() for r in records], f, indent=2, default=str)
            return len(records)

        records = self.query()
        if not records:
            return 0
        # Flatten metadata to JSON string to avoid mixed-type issues
        data = []
        for r in records:
            d = r.to_dict()
            d["metadata"] = json.dumps(d.get("metadata", {}), default=str)
            data.append(d)
        table = pa.Table.from_pylist(data)
        pq.write_table(table, str(path))
        return len(records)
