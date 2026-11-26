"""Scoped mini-compiler producing DQCJob.qpu_demand/epr_demand/exec_time_ns.

Faithful to ref [8] (Ferrari/Carretta/Amoretti, arXiv:2305.02969) Sec.3.1:
build the circuit's qubit-interaction graph (edge weight = #2-qubit gates
between that pair), partition it with METIS into the requested QPU count.

Simplification vs. the full ref [8] pipeline (see docs/assumptions_register.md
A3): we implement TeleGate-only remote-gate handling, not the TeleData/
TeleGate cost comparison of their Algorithm 1. Ref [8] itself evaluates a
TeleGate-only mode as one of its two tested configurations (Sec.4), so this
is a source-described simplification, not an invented one: every cross-
partition 2-qubit gate costs exactly one EPR pair (Cat-Ent primitive, ref[8]
Fig.1b), with no TeleData migration/cost optimization. Also out of scope:
ref [8]'s local SWAP-routing pass (needs a per-QPU coupling map the 2026
paper never specifies) — T_j's local-gate contribution uses a placeholder
constant (see LOCAL_GATE_TIME_NS) since neither paper gives trapped-ion
local-gate timings (ASSUMPTION A3, still open). Label any DQCJob built here
as SCHEDULER_MODEL_REPRODUCTION, never PAPER_REPRODUCTION.
"""
from __future__ import annotations

from collections import Counter

import pymetis

from dqc.domain import DQCJob
from dqc.network import T_CYCLE_NS, LINK_QUALITIES, entanglement_success_probability, state_delay_ns

# ponytail: no trapped-ion local-gate timing constant exists in either source
# paper (A3). Borrowed from ref [7] Table I (color-center 2-qubit gate, a
# DIFFERENT hardware platform) as the least-arbitrary stand-in available.
# Upgrade path: replace once a trapped-ion local-gate time is sourced.
LOCAL_GATE_TIME_NS = 500_000.0


def circuit_two_qubit_gates(circuit_type: str, n_qubits: int) -> list[tuple[int, int]]:
    """2-qubit gate pairs per Appendix A (A.1-A.5). 1-qubit gates (H, R_Y/R_Z
    single-qubit rotations) don't affect the interaction graph and are
    dropped, matching ref [8]'s own graph model (Sec.3.1: vertices=qubits,
    edges=2-qubit-gate counts)."""
    if n_qubits < 2:
        return []
    if circuit_type == "ghz":
        # Eq.34: CNOT_{1,2}...CNOT_{1,n} -- star from qubit 0.
        return [(0, i) for i in range(1, n_qubits)]
    if circuit_type == "graph":
        # Eq.35: ring graph, CZ per edge (i, i+1 mod n).
        return [(i, (i + 1) % n_qubits) for i in range(n_qubits)]
    if circuit_type == "qaoa":
        # Fig.11: cost unitary on a ring graph, one repetition (r=1).
        return [(i, (i + 1) % n_qubits) for i in range(n_qubits)]
    if circuit_type == "qft":
        # Eq.40/Fig.12: controlled-phase rotation between every qubit pair i<j.
        return [(i, j) for i in range(n_qubits) for j in range(i + 1, n_qubits)]
    if circuit_type == "vqe":
        # Fig.13: linear nearest-neighbor CNOT, one repetition.
        return [(i, i + 1) for i in range(n_qubits - 1)]
    raise ValueError(f"unknown circuit_type {circuit_type!r}")


def _partition(n_qubits: int, gate_pairs: list[tuple[int, int]], n_qpus: int) -> list[int]:
    """METIS k-way partition of the qubit-interaction graph (ref[8] Sec.3.1)."""
    if n_qpus <= 1:
        return [0] * n_qubits
    weight = Counter(gate_pairs)
    neighbors: list[list[int]] = [[] for _ in range(n_qubits)]
    eweights: list[list[int]] = [[] for _ in range(n_qubits)]
    for (a, b), w in weight.items():
        neighbors[a].append(b)
        eweights[a].append(w)
        neighbors[b].append(a)
        eweights[b].append(w)
    flat_eweights = [w for row in eweights for w in row]
    _, membership = pymetis.part_graph(n_qpus, adjacency=neighbors, eweights=flat_eweights)
    return list(membership)


def compile_job(
    job_id: str,
    circuit_type: str,
    n_qubits: int,
    n_qpus: int,
    arrival_slot: int,
    link_quality: str = "Medium",
) -> DQCJob:
    """Produce a DQCJob's R_j/E_j/T_j via the scoped ref[8]-style pipeline.

    n_qpus is the compiler's REQUESTED partition count (an input, per ref[8]
    Sec.3.1 -- it is not derived from the circuit).
    """
    gate_pairs = circuit_two_qubit_gates(circuit_type, n_qubits)
    membership = _partition(n_qubits, gate_pairs, n_qpus)
    epr_demand = sum(1 for a, b in gate_pairs if membership[a] != membership[b])
    local_gates = len(gate_pairs) - epr_demand

    params = LINK_QUALITIES[link_quality]
    p_s = entanglement_success_probability(params)
    t_state = state_delay_ns(T_CYCLE_NS[link_quality], p_s)

    exec_time_ns = local_gates * LOCAL_GATE_TIME_NS + epr_demand * t_state
    used_qpus = len(set(membership))
    return DQCJob(
        id=job_id,
        circuit_type=circuit_type,
        n_qubits=n_qubits,
        qpu_demand=used_qpus,
        epr_demand=epr_demand,
        exec_time_ns=exec_time_ns,
        arrival_slot=arrival_slot,
    )
