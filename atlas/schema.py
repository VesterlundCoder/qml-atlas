"""Atlas schema: ExperimentRecord and enums.

Every experiment across R01-R20 produces one or more ExperimentRecords.
The schema is track-agnostic; track-specific details go in the
extensible ``metadata`` dict.
"""
from __future__ import annotations

import enum
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


class QALevel(enum.IntEnum):
    """Quantum Advantage Ladder — used consistently across all projects."""
    NONE = -1      # not assessed
    QA0 = 0        # quantum changes representation/dynamics measurably
    QA1 = 1        # better quality on frozen held-out data
    QA2 = 2        # better sample efficiency
    QA3 = 3        # better total resource efficiency
    QA4 = 4        # advantage grows with scale
    QA5 = 5        # complexity-theoretic separation


class ExperimentStatus(enum.Enum):
    """Outcome classification for each experiment."""
    RED = "classical_advantage"       # A < 0, classical wins
    YELLOW = "unresolved"             # A ≈ 0, inconclusive
    GREEN = "quantum_candidate"       # A > 0, quantum candidate
    NOT_ASSESSED = "not_assessed"     # baseline/reference data


class Track(enum.Enum):
    """Four experimental tracks plus cross-cutting infrastructure."""
    INFRA = "infrastructure"
    LEARNING = "quantum_learning"     # Track A
    SAMPLING = "quantum_sampling"     # Track B
    OPTIMIZATION = "quantum_optimization"  # Track C
    RESERVOIR = "quantum_reservoir"   # Track D


@dataclass
class ExperimentRecord:
    """A single experiment result, track-agnostic.

    Fields follow the R01 specification. Track-specific details go in
    ``metadata`` so the schema never needs track-specific top-level fields.
    """
    # Identity
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    # Track and project
    track: str = ""           # Track enum value
    project: str = ""         # e.g. "R01", "R12"

    # Problem
    problem_family: str = ""  # e.g. "mwis", "maxcut", "ising_spin_glass"
    problem_size: int = 0     # n (qubits or variables)
    difficulty: str = ""      # D1, D2, D3, D4
    seed: int = 0
    problem_instance_id: str = ""  # e.g. "mwis_n28_s66"

    # Quantum method
    quantum_method: str = ""  # e.g. "qaoa", "learned_qaoa", "generative_policy"
    circuit_family: str = "" # e.g. "qaoa", "ry_rxx", "heisenberg"
    qubits: int = 0
    depth: int = 0            # circuit depth p
    observable_order: int = 0 # correlation order m
    shots: int = 0
    noise_model: str = ""     # e.g. "ideal", "depolarizing_1e-3"
    hardware: str = ""        # e.g. "simulator", "piast_q", "ibm_kyiv"

    # Classical baseline
    classical_method: str = ""  # e.g. "sa", "tabu", "xgboost"
    classical_parameters: str = ""  # JSON string of params

    # Data split
    training_size: int = 0
    test_size: int = 0

    # Metrics
    metric_name: str = ""     # e.g. "p_r", "accuracy", "energy_error_mha"
    metric_Q: float = 0.0     # quantum metric value
    metric_C: float = 0.0     # classical metric value
    delta: float = 0.0        # M_Q - M_C
    confidence_interval_low: float = 0.0
    confidence_interval_high: float = 0.0
    effect_size: float = 0.0  # Cohen's d or similar

    # Resources
    cpu_seconds: float = 0.0
    gpu_seconds: float = 0.0
    qpu_seconds: float = 0.0
    memory_peak_mb: float = 0.0

    # Classification
    qa_level: int = -1       # QALevel enum value
    status: str = "not_assessed"  # ExperimentStatus value
    preregistered: bool = False

    # Provenance
    code_commit: str = ""
    dataset_hash: str = ""

    # Extensible metadata (track-specific details)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.problem_instance_id and self.problem_family and self.problem_size and self.seed:
            self.problem_instance_id = f"{self.problem_family}_n{self.problem_size}_s{self.seed}"
        if self.delta == 0.0 and (self.metric_Q != 0.0 or self.metric_C != 0.0):
            self.delta = self.metric_Q - self.metric_C

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExperimentRecord:
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return cls(**filtered)

    def content_hash(self) -> str:
        """Stable hash of the record content (excluding experiment_id and timestamp)."""
        d = self.to_dict()
        d.pop("experiment_id", None)
        d.pop("timestamp", None)
        return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]
