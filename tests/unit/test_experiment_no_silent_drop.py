"""Regression test for a real bug found in the Phase 7 matrix run: the
drain loop's termination check conflated "no more engine events pending"
with "no more work to do." A scheduler that occasionally returns an empty
ScheduleDecision (e.g. a time-limited MILP solve with a sub-optimal
incumbent) while jobs are still queued and capacity is free must never
cause those jobs to be silently dropped from the results."""
import pytest

from dqc.domain import Assignment, DQCJob, ScheduleDecision
from dqc.experiment import run_trace
from dqc.workload import WorkloadTrace


def _job(id_):
    return DQCJob(id=id_, circuit_type="ghz", n_qubits=5, qpu_demand=1,
                  epr_demand=0, exec_time_ns=10.0, arrival_slot=0)


class FlakyScheduler:
    """Returns an empty decision on its first N calls, then schedules
    normally -- simulating a solver that occasionally stalls before making
    progress, as the real time-limited MILP solver does."""

    def __init__(self, stall_calls: int):
        self.stall_calls = stall_calls
        self.calls = 0

    def select(self, state):
        self.calls += 1
        if self.calls <= self.stall_calls:
            return ScheduleDecision()
        if not state.queued_jobs:
            return ScheduleDecision()
        job = state.queued_jobs[0]
        if job.qpu_demand > len(state.free_qpu_ids):
            return ScheduleDecision()
        qpu_id = next(iter(state.free_qpu_ids))
        return ScheduleDecision(assignments=(
            Assignment(job.id, (qpu_id,), state.time_ns, state.time_ns + job.exec_time_ns),
        ))


def test_transient_stalls_do_not_drop_jobs():
    trace = WorkloadTrace(seed=0, arrivals_by_slot=((_job("j0"), _job("j1")),))
    scheduler = FlakyScheduler(stall_calls=3)  # within the retry budget
    records = run_trace(scheduler, trace, ["q0"], slot_duration_ns=100.0)
    assert {r.job_id for r in records} == {"j0", "j1"}


def test_persistent_stall_raises_instead_of_silently_dropping():
    trace = WorkloadTrace(seed=0, arrivals_by_slot=((_job("j0"),),))
    scheduler = FlakyScheduler(stall_calls=10_000)  # never recovers
    with pytest.raises(RuntimeError, match="no progress"):
        run_trace(scheduler, trace, ["q0"], slot_duration_ns=100.0)
