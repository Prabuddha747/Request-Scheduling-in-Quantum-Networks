"""SimPy-backed execution engine. Schedulers never import simpy directly —
they only see SchedulingState and return a ScheduleDecision (master prompt
Sec.4: "Schedulers must not import SimPy or quantum simulator internals").
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import simpy

from dqc.domain import Assignment, ScheduleDecision, SchedulingState, SimulationEvent


class Scheduler(Protocol):
    def select(self, state: SchedulingState) -> ScheduleDecision: ...


class MetricsPlugin(Protocol):
    def update(self, event: SimulationEvent) -> None: ...
    def finalize(self) -> dict[str, float]: ...


@dataclass(frozen=True)
class BackendSnapshot:
    time_ns: float
    free_qpu_ids: frozenset[str]
    events: tuple[SimulationEvent, ...]


class ResourceConflictError(Exception):
    """Raised if a ScheduleDecision would double-book a QPU (atomicity guard)."""


class SimPyBackend:
    """Reference ExecutionBackend. All QPUs reserved/released exactly once."""

    def __init__(self, qpu_ids: list[str]):
        self.env = simpy.Environment()
        self._free: set[str] = set(qpu_ids)
        self._busy_job_of: dict[str, str] = {}
        self._events: list[SimulationEvent] = []
        self._released_at_least_once: set[str] = set()  # completion-exactly-once guard
        self._job_completed: set[str] = set()

    def submit(self, decision: ScheduleDecision) -> None:
        for assignment in decision.assignments:
            self._reserve(assignment)
            self.env.process(self._run_job(assignment))

    def _reserve(self, assignment: Assignment) -> None:
        requested = set(assignment.qpu_ids)
        if not requested <= self._free:
            raise ResourceConflictError(
                f"job {assignment.job_id} requests {requested}, "
                f"but only {self._free} are free"
            )
        self._free -= requested
        for qpu_id in requested:
            self._busy_job_of[qpu_id] = assignment.job_id
        self._events.append(SimulationEvent(
            kind="job_started", time_ns=self.env.now,
            job_id=assignment.job_id, qpu_ids=assignment.qpu_ids,
        ))

    def _run_job(self, assignment: Assignment):
        duration = assignment.completion_time_ns - assignment.start_time_ns
        assert duration >= 0, f"negative duration for job {assignment.job_id}"
        yield self.env.timeout(duration)
        assert assignment.job_id not in self._job_completed, (
            f"job {assignment.job_id} completed twice"
        )
        self._job_completed.add(assignment.job_id)
        for qpu_id in assignment.qpu_ids:
            self._busy_job_of.pop(qpu_id, None)
            self._free.add(qpu_id)
        self._events.append(SimulationEvent(
            kind="job_completed", time_ns=self.env.now,
            job_id=assignment.job_id, qpu_ids=assignment.qpu_ids,
        ))

    def run_until(self, simulation_time_ns: float) -> None:
        # simpy.Environment.run(until=t) does NOT process events scheduled
        # exactly at t (it stops just short); flush those explicitly so a
        # job completing exactly at the query time is reflected. It also
        # rejects until <= now outright, so skip straight to the flush loop
        # when there's nothing to advance (e.g. querying at t=0).
        if simulation_time_ns > self.env.now:
            self.env.run(until=simulation_time_ns)
        while self.env.peek() <= simulation_time_ns:
            self.env.step()

    def snapshot(self) -> BackendSnapshot:
        return BackendSnapshot(
            time_ns=self.env.now,
            free_qpu_ids=frozenset(self._free),
            events=tuple(self._events),
        )


