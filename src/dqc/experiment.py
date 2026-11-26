"""Experiment runner: WorkloadTrace -> Scheduler -> SimPyBackend -> per-job
records. Phase 7 (master prompt Sec.6/10).

ponytail: this is the SMOKE-SCALE runner the master prompt's own gate order
requires before any larger matrix (Phase 7: "First run smoke tests: 10
slots, one seed, small QPU count"). It has not been proven at the full
1000-slot/10-QPU scale -- see docs/assumptions_register.md.

`slot_duration_ns` (when arrivals happen relative to the engine's
continuous ns clock) is an implementation parameter neither paper source
gives (the paper's "time slots" are discrete scheduling rounds, not
wall-clock durations) -- callers must pick one large enough that a slot's
arrivals have a chance to be scheduled before the next slot's jobs arrive.
"""
from __future__ import annotations

from dataclasses import dataclass

from dqc.domain import DQCJob, SchedulingState, WorkloadTrace
from dqc.engine import SimPyBackend

MAX_DRAIN_ITERATIONS = 100_000


@dataclass(frozen=True)
class JobRecord:
    job_id: str
    arrival_slot: int
    arrival_time_ns: float
    qpu_demand: int
    epr_demand: int
    start_time_ns: float
    completion_time_ns: float
    exec_time_ns: float


def run_trace(
    scheduler, trace: WorkloadTrace, qpu_ids: list[str], slot_duration_ns: float,
    reinvoke_on_release: bool = False, link_weight: dict | None = None,
) -> list[JobRecord]:
    backend = SimPyBackend(qpu_ids)
    link_weight = link_weight or {}
    pending: list[DQCJob] = []
    job_lookup: dict[str, DQCJob] = {}
    arrival_time_of: dict[str, float] = {}
    records: dict[str, JobRecord] = {}

    def dispatch() -> None:
        while True:
            snap = backend.snapshot()
            state = SchedulingState(
                time_ns=backend.env.now, free_qpu_ids=snap.free_qpu_ids,
                queued_jobs=tuple(pending), link_weight=link_weight,
            )
            decision = scheduler.select(state)
            if not decision.assignments:
                return
            backend.submit(decision)
            assigned_ids = {a.job_id for a in decision.assignments}
            for a in decision.assignments:
                records[a.job_id] = JobRecord(
                    job_id=a.job_id, arrival_slot=job_lookup[a.job_id].arrival_slot,
                    arrival_time_ns=arrival_time_of[a.job_id],
                    qpu_demand=len(a.qpu_ids), epr_demand=job_lookup[a.job_id].epr_demand,
                    start_time_ns=a.start_time_ns, completion_time_ns=a.completion_time_ns,
                    exec_time_ns=a.completion_time_ns - a.start_time_ns,
                )
            pending[:] = [j for j in pending if j.id not in assigned_ids]
            if not reinvoke_on_release:
                return

    for slot, slot_jobs in enumerate(trace.arrivals_by_slot):
        slot_time = slot * slot_duration_ns
        backend.run_until(slot_time)
        for job in slot_jobs:
            pending.append(job)
            job_lookup[job.id] = job
            arrival_time_of[job.id] = slot_time
        dispatch()
        if reinvoke_on_release:
            next_slot_time = (slot + 1) * slot_duration_ns
            while backend.env.peek() < next_slot_time:
                backend.run_until(backend.env.peek())
                dispatch()

    for _ in range(MAX_DRAIN_ITERATIONS):
        dispatch()
        idle = not pending and backend.snapshot().free_qpu_ids == frozenset(qpu_ids)
        if idle:
            break
        next_event = backend.env.peek()
        if next_event == float("inf"):
            break
        backend.run_until(next_event)
    else:
        raise RuntimeError("drain loop did not converge within MAX_DRAIN_ITERATIONS")

    return list(records.values())
