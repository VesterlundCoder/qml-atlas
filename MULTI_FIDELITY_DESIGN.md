# Multi-Fidelity Research Design — R06-R20

**Principle:** bred lokal discovery → selektiv lokal scaling → frozen external confirmation

The local 128GB machine is a **boundary-finder**, not a full-scale QPU. We use it to find where quantum advantage might lie, then send only the most informative points to expensive compute.

## Five Fidelity Levels

| Level | Name | Range | Method | Purpose |
|-------|------|-------|--------|---------|
| L0 | Exact local | n ≤ 20 | Full statevector | Broad search, 10^4–10^6 circuits |
| L1 | Selective exact local | n = 21–28 | Statevector, winners only | Scale promising families |
| L2 | Approximate local scaling | n = 24–40+ | MPS, tensor networks, surrogates, lightcones | Find boundary (no advantage claim) |
| L3 | Frozen local confirmation | n ≤ 28 | Exact simulation, new instances, no tuning | Confirm boundary locally |
| H1 | External confirmation | any | LUMI, BlueQBit, Piast-Q, QPU | Only when R18 predicts something worth testing |

**Rule:** Approximate MPS/TN may be used for screening. If approximation error ≈ advantage magnitude (ε_TN ~ A), it may NOT be used for confirmation — exact/QPU required.

## Local Feasibility Assessment

| Project | Local? | Local Workaround | External Need |
|---------|:------:|-------------------|---------------|
| R06 Feature-map scaling | ~85% | Exact + MPS/tensor networks | Largest n |
| R07 Surrogate attack | 100% | RF/XGB/GNN locally | None |
| R08 Sample efficiency | 100% | Reuse quantum features | None |
| R09 Static QRC | ~90% | Exact/MPS + selected correlators | Large QPU validation |
| R10 Temporal QRC | ~85% | Simulated reservoir + trajectory batching | Final hardware test |
| R11 Correlation order | ~90% | Shadows/motif correlators | Very large m,n |
| R12 Recovery basins | ~95% | Exact small cores + approximate basins | Large hardware validation only |
| R13 Sampling complexity | 100% | Statistics on R12 data | None |
| R14 Generative sampler | ~80% | Simulator + surrogate/policy optimization | Large-scale validation |
| R15 Hybrid hard cores | ~80% | Large problem → small core → simulation | Real QPU resource claim |
| R16 QAOA boundary | ~75-85% | Lightcones/MPS/parameter transfer | 28-40+ hard circuits |
| R17 Active boundary search | 100% | Classical surrogate | None |
| R18 Crossover prediction | 100% | Scaling model + prereg | Verification, not prediction |
| R19 Blind confirmation | Depends | Hidden local instance bank | If crossover beyond local capacity |
| R20 Multi-QPU validation | Prep yes | Noise/backend emulation | Actual QPUs |

**Only R20 definitionally requires external QPU hardware. R19 may, depending on where the crossover lies.**

## Memory Budget (128 GB machine)

Full statevector (complex128, 16 × 2^n bytes):
- 20 qubits: 16 MB
- 24 qubits: 256 MB
- 28 qubits: 4 GB
- 29 qubits: 8 GB
- 30 qubits: 16 GB
- 31 qubits: 32 GB
- 32 qubits: 64 GB (extreme, controlled only)

**Working regime:**
- 8–20 qubits: exhaustive/broad
- 24 qubits: medium-wide
- 28 qubits: selective
- 30+: frozen candidates only
- 32+: tensor-network/QPU/few selected

## Three Parallel Pipelines

### Pipeline A: QML (R06 → R07 → R08 → R11)
- Start: n ∈ {8,12,16,20}, p ∈ {1,2,3}, m ∈ {1,2,3}
- Generate quantum features once, cache
- Attack with classical surrogates
- Test sample efficiency
- Isolate correlation order

### Pipeline B: Sampling (R12 → R13 → R14)
- Start: n ∈ {12,16,20} with exact A_r(G)
- Compute p_r for all samplers
- Analyze sample complexity
- Train generative sampler

### Pipeline C: Optimization (R15 → R16)
- Large parent graphs (N=50–1000)
- Reduce to small quantum cores (n=12–32)
- Test QAOA family systematically

All three feed into R17 (active boundary search).

## Multi-Fidelity Boundary Modelling

Train a model that learns the relation between fidelity levels:

```
A_{k+1} = f(A_k, x)
```

Where:
- A_0(x) = 12-qubit information (cheap)
- A_1(x) = 16-qubit
- A_2(x) = 20-qubit
- A_3(x) = MPS 28-qubit
- A_4(x) = real QPU

This lets us use small experiments to select which larger experiments are informative.

## R20 Hardware Emulation (Local Preparation)

Before QPU runs, emulate locally:
- **Trapped ion:** all-to-all connectivity, native RXX, trapped-ion noise
- **Superconducting:** sparse coupling map, SWAP overhead, CX/ECR errors, readout errors
- **Neutral atom:** geometric connectivity, Rydberg constraints, loss/noise

Compute: Q_ideal, Q_ion-sim, Q_SC-sim, Q_neutral-sim

Preregister hardware predictions before QPU runs. Example:
> "We predict trapped-ion hardware will preserve 82-90% of the ideal effect,
> while superconducting topology will reduce it to 55-70%."

Then run QPU. This is scientifically much stronger than just sending circuits to three machines.

## Corrected Scope

```
R01-R18: huvudsakligen lokal forskning
R19: lokal eller extern beroende på var boundary hamnar
R20: kräver externa QPU:er för slutgiltig validering
```

Hundratusentals lokala experiment reduceras till kanske några hundra frozen QPU-circuits.
