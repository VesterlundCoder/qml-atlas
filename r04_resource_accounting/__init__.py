"""R04 — Resource Accounting Standard.

Standardized resource accounting for all R01-R20 projects.
QA3 may only be declared if M_Q >= M_C AND R_Q < R_C under a preregistered resource definition.

Usage:
    from projects.QAB.r04_resource_accounting import ResourceRecord, compare_resources
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResourceRecord:
    """Resource cost for a single method run."""
    method: str = ""
    method_type: str = ""  # "quantum" or "classical"

    # Quantum costs (seconds)
    qpu_seconds: float = 0.0
    compile_seconds: float = 0.0
    mitigation_seconds: float = 0.0
    classical_preprocessing_seconds: float = 0.0
    training_seconds: float = 0.0

    # Classical costs (seconds)
    cpu_seconds: float = 0.0
    gpu_seconds: float = 0.0
    hyperparameter_search_seconds: float = 0.0

    # Memory
    memory_peak_mb: float = 0.0

    # Wall clock
    wall_seconds: float = 0.0

    @property
    def total_quantum(self) -> float:
        """R_Q = T_QPU + T_compile + T_mitigation + T_classical_preprocessing + T_training"""
        return (self.qpu_seconds + self.compile_seconds +
                self.mitigation_seconds + self.classical_preprocessing_seconds +
                self.training_seconds)

    @property
    def total_classical(self) -> float:
        """R_C = T_CPU + T_GPU + T_training + T_hyperparameter_search"""
        return (self.cpu_seconds + self.gpu_seconds +
                self.training_seconds + self.hyperparameter_search_seconds)

    @property
    def total(self) -> float:
        """Total resource cost."""
        if self.method_type == "quantum":
            return self.total_quantum
        return self.total_classical

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "method_type": self.method_type,
            "qpu_seconds": self.qpu_seconds,
            "compile_seconds": self.compile_seconds,
            "mitigation_seconds": self.mitigation_seconds,
            "classical_preprocessing_seconds": self.classical_preprocessing_seconds,
            "training_seconds": self.training_seconds,
            "cpu_seconds": self.cpu_seconds,
            "gpu_seconds": self.gpu_seconds,
            "hyperparameter_search_seconds": self.hyperparameter_search_seconds,
            "memory_peak_mb": self.memory_peak_mb,
            "wall_seconds": self.wall_seconds,
            "total_quantum": self.total_quantum,
            "total_classical": self.total_classical,
            "total": self.total,
        }


@dataclass
class ResourceComparison:
    """Result of comparing quantum vs classical resources."""
    quantum: ResourceRecord
    classical: ResourceRecord
    metric_Q: float = 0.0
    metric_C: float = 0.0
    quality_passes: bool = False  # M_Q >= M_C
    resource_passes: bool = False  # R_Q < R_C
    qa3_eligible: bool = False

    def __post_init__(self):
        self.quality_passes = self.metric_Q >= self.metric_C
        self.resource_passes = self.quantum.total < self.classical.total
        self.qa3_eligible = self.quality_passes and self.resource_passes

    def summary(self) -> str:
        lines = [
            f"Resource Comparison: {self.quantum.method} vs {self.classical.method}",
            f"  Quality:  M_Q={self.metric_Q:.4f}  M_C={self.metric_C:.4f}  {'PASS' if self.quality_passes else 'FAIL'}",
            f"  Resource: R_Q={self.quantum.total:.2f}s  R_C={self.classical.total:.2f}s  {'PASS' if self.resource_passes else 'FAIL'}",
            f"  QA3 eligible: {'YES' if self.qa3_eligible else 'NO'}",
        ]
        return "\n".join(lines)


def compare_resources(quantum: ResourceRecord, classical: ResourceRecord,
                       metric_Q: float, metric_C: float) -> ResourceComparison:
    """Compare quantum vs classical under resource-normalized evaluation."""
    return ResourceComparison(quantum=quantum, classical=classical,
                             metric_Q=metric_Q, metric_C=metric_C)


class ResourceTimer:
    """Context manager for timing resource usage."""
    def __init__(self, record: ResourceRecord, category: str = "cpu_seconds"):
        self.record = record
        self.category = category
        self.t0 = 0.0

    def __enter__(self):
        self.t0 = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.t0
        setattr(self.record, self.category,
                getattr(self.record, self.category) + elapsed)
