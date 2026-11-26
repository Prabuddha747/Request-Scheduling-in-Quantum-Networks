"""Workload/arrival-trace generator. Paper Sec.7.1.1-7.1.2, Eq.31-32.

Job catalogue: the 30 (circuit_type, qubit_count) templates found in the
authors' own run log (see docs/assumptions_register.md A4) -- 5 circuit
types x odd qubit counts {5,7,9,11,13,15}.

ponytail: per-job target QPU count (the mini-compiler's k) is NOT given by
either paper -- uses round(n_qubits/5) capped to the network size, since
nothing in the source material specifies the authors' choice (ASSUMPTION
A11). Truncated-Poisson bounds are also undocumented; defaults to
[0, 3*lambda] (ASSUMPTION A10). Both are declared, not hidden, assumptions.
"""
from __future__ import annotations

import numpy as np

from dqc.compiler import compile_job
from dqc.domain import DQCJob, WorkloadTrace

CIRCUIT_TYPES = ("ghz", "graph", "qaoa", "qft", "vqe")
QUBIT_COUNTS = (5, 7, 9, 11, 13, 15)  # odd counts only, per o.log


def _default_qpu_count(n_qubits: int, n_qpu_network: int) -> int:
    return max(1, min(n_qpu_network, round(n_qubits / 5)))


def build_job_catalogue(
    n_qpu_network: int = 10, link_quality: str = "Medium", qubit_counts: tuple[int, ...] = QUBIT_COUNTS,
) -> list[DQCJob]:
    """The (up to 30-template) catalogue (set Gamma, Eq.31), ordered
    ascending by EPR demand as Eq.31 requires ("ordered... from smallest to
    largest"). `qubit_counts` lets a caller restrict to a subset (e.g. a
    smoke-scale run) -- the full paper catalogue is all of QUBIT_COUNTS."""
    catalogue = [
        compile_job(
            job_id=f"{circuit_type}_{n_qubits}", circuit_type=circuit_type, n_qubits=n_qubits,
            n_qpus=_default_qpu_count(n_qubits, n_qpu_network), arrival_slot=-1, link_quality=link_quality,
        )
        for circuit_type in CIRCUIT_TYPES
        for n_qubits in qubit_counts
    ]
    return sorted(catalogue, key=lambda j: j.epr_demand)


def _tau_weights(n: int, tau: float) -> np.ndarray:
    """Eq.31-32: w_j = j^tau over 1-indexed rank; normalized to probabilities."""
    ranks = np.arange(1, n + 1, dtype=float)
    weights = ranks**tau
    return weights / weights.sum()


def generate_trace(
    seed: int, n_slots: int, lam: float, tau: float,
    catalogue: list[DQCJob] | None = None, n_qpu_network: int = 10,
    truncation_bounds: tuple[int, int] | None = None,
) -> WorkloadTrace:
    catalogue = catalogue or build_job_catalogue(n_qpu_network)
    low, high = truncation_bounds or (0, max(1, round(3 * lam)))
    rng = np.random.default_rng(seed)
    probs = _tau_weights(len(catalogue), tau)

    arrivals_by_slot = []
    job_counter = 0
    for slot in range(n_slots):
        n_arrivals = int(np.clip(rng.poisson(lam), low, high))
        chosen = rng.choice(len(catalogue), size=n_arrivals, p=probs)
        slot_jobs = []
        for template_idx in chosen:
            t = catalogue[template_idx]
            job_counter += 1
            slot_jobs.append(DQCJob(
                id=f"{t.id}_s{slot}_{job_counter}", circuit_type=t.circuit_type, n_qubits=t.n_qubits,
                qpu_demand=t.qpu_demand, epr_demand=t.epr_demand, exec_time_ns=t.exec_time_ns,
                arrival_slot=slot,
            ))
        arrivals_by_slot.append(tuple(slot_jobs))
    return WorkloadTrace(seed=seed, arrivals_by_slot=tuple(arrivals_by_slot))
