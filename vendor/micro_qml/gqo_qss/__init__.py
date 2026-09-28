"""GQO+QSS: Generative Quantum Optimization + Quantum-Selected Search.

Ports the GQE+QSCI architecture from quantum chemistry (arXiv:2607.23988)
to combinatorial graph optimization.

Architecture:
    G_large → HPC → H_hard → generative policy → circuits → QPU/sim → S_Q
           → classical recovery → S_Q+ → restricted solver → x* → reward → policy update

Key principle: QPU doesn't solve the problem. It finds a small valuable subspace.
"""
from micro_qml.gqo_qss.samplers import (
    SampleResult,
    sample_uniform,
    sample_greedy,
    sample_qaoa,
    sample_learned_qaoa,
    sample_generative,
    run_all_samplers,
    list_samplers,
)
from micro_qml.gqo_qss.recovery import (
    RecoveryResult,
    recover,
    repair_solution,
    repair_mwis,
    repair_maxcut,
    repair_balanced_partition,
    repair_vertex_cover,
)
from micro_qml.gqo_qss.metrics import (
    SampleMetrics,
    compute_metrics,
    compare_samplers,
    compute_scaling_law,
)
from micro_qml.gqo_qss.pipeline import (
    GQOQSSResult,
    run_gqo_qss,
    compute_reward,
    print_result_table,
)
from micro_qml.gqo_qss.experiment import (
    run_qubit_ladder,
    run_noise_as_exploration,
)
