"""Domain model for the DQC scheduler simulation.

Sourced from "Advanced Scheduling Strategies for Distributed Quantum
Computing Jobs" (arXiv:2602.24152v3) Sec. 4.1-4.2. See
docs/source_traceability.csv rows EQ3-11 for exact equation references.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QPU:
    id: str


@dataclass(frozen=True)
class QuantumLink:
    """Heterogeneous link between two QPUs (paper Sec. 3.2.1, Table 2/3)."""
    qpu_a: str
    qpu_b: str
    t_cycle_ns: float
    p_success: float
    fidelity: float

    @property
    def t_state_ns(self) -> float:
        """Eq. 2: t_state = t_cycle / P_s."""
        return self.t_cycle_ns / self.p_success


@dataclass(frozen=True)
class DQCJob:
    """A compiled DQC job (paper Sec. 4.2: E_j, R_j, T_j per job j).

    qpu_demand = R_j, epr_demand = E_j, exec_time_ns = T_j.
    All three are compiler outputs (see ASSUMPTION A3) rather than formulas
    over (circuit_type, n_qubits); this record holds whatever the job
    source (mini-compiler or declared proxy) computed.
    """
    id: str
    circuit_type: str
    n_qubits: int
    qpu_demand: int
    epr_demand: int
    exec_time_ns: float
    arrival_slot: int


@dataclass(frozen=True)
class Assignment:
    job_id: str
    qpu_ids: tuple[str, ...]
    start_time_ns: float
    completion_time_ns: float


@dataclass(frozen=True)
class ScheduleDecision:
    """What a Scheduler chooses to start right now."""
    assignments: tuple[Assignment, ...] = ()


@dataclass(frozen=True)
class SchedulingState:
    """Input to Scheduler.select — paper Eq. 8-9: B(t)/R(t) = busy/free QPUs."""
    time_ns: float
    free_qpu_ids: frozenset[str]
    queued_jobs: tuple[DQCJob, ...]


@dataclass(frozen=True)
class SimulationEvent:
    kind: str  # "job_started" | "job_completed"
    time_ns: float
    job_id: str
    qpu_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorkloadTrace:
    """Immutable per-slot arrivals, replayed identically for every scheduler."""
    seed: int
    arrivals_by_slot: tuple[tuple[DQCJob, ...], ...] = field(default_factory=tuple)
