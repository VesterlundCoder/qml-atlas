# R06 — Quantum Feature Map Scaling

**Track:** A — Quantum Learning
**Wave:** 2 (Months 4-6)
**Status:** 🔲 Not started

## Question

Can quantum feature maps extract predictive structure that strong classical ML cannot?

## Grid

| Axis | Values |
|------|--------|
| n (qubits) | 8, 12, 16, 20, 24, 32 |
| p (depth/reupload layers) | 1, 2, 3, 4, 6 |
| m (correlation order) | 1, 2, 3, 4 |

## Circuit Families

| Family | Description |
|--------|-------------|
| QAOA-like | Standard QAOA mixer+cost layers |
| RY-RXX | Rotation + XX entangling |
| RY-RXX-RYY | Rotation + XX + YY entangling |
| Heisenberg | XYZ interactions |
| Data reuploading | Single-qubit reuploading with entangling |
| Commutator-inspired | Commutator-based ansatz |
| Random entangling reservoir | Random fixed entangling circuit |

## Outputs

Observable expectation values:
- ⟨Z_i⟩, ⟨X_i⟩ — 1-body
- ⟨Z_iZ_j⟩, ⟨X_iX_j⟩ — 2-body
- Up to selected 4-body correlators

## Gate

**R06-G1:** Scale circuit families only if A(n+4) > A(n) in ≥2 consecutive steps, or if surrogate difficulty increases clearly.

## Compute

3k–8k GPU-hours
