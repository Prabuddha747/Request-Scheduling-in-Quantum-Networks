import pytest

from dqc.domain import Assignment, ScheduleDecision
from dqc.engine import ResourceConflictError, SimPyBackend


def test_resource_exclusivity_rejects_double_booking():
    backend = SimPyBackend(qpu_ids=["q0"])
    backend.submit(ScheduleDecision(assignments=(
        Assignment("j0", ("q0",), 0, 10),
    )))
    with pytest.raises(ResourceConflictError):
        backend.submit(ScheduleDecision(assignments=(
            Assignment("j1", ("q0",), 0, 1),
        )))


def test_resources_released_exactly_once_and_reusable():
    backend = SimPyBackend(qpu_ids=["q0"])
    backend.submit(ScheduleDecision(assignments=(Assignment("j0", ("q0",), 0, 5),)))
    backend.run_until(5)
    assert backend.snapshot().free_qpu_ids == frozenset({"q0"})
    # q0 must be reusable after release, with no error
    backend.submit(ScheduleDecision(assignments=(Assignment("j1", ("q0",), 5, 8),)))
    backend.run_until(8)
    completions = [e for e in backend.snapshot().events if e.kind == "job_completed"]
    assert [e.job_id for e in completions] == ["j0", "j1"]


def test_no_negative_duration_assignment_rejected():
    backend = SimPyBackend(qpu_ids=["q0"])
    backend.submit(ScheduleDecision(assignments=(Assignment("j0", ("q0",), 10, 5),)))
    with pytest.raises(AssertionError):
        backend.run_until(10)


def test_multi_qpu_job_reserves_all_atomically():
    backend = SimPyBackend(qpu_ids=["q0", "q1", "q2"])
    backend.submit(ScheduleDecision(assignments=(
        Assignment("j0", ("q0", "q1"), 0, 10),
    )))
    with pytest.raises(ResourceConflictError):
        backend.submit(ScheduleDecision(assignments=(
            Assignment("j1", ("q1", "q2"), 0, 1),
        )))
    assert backend.snapshot().free_qpu_ids == frozenset({"q2"})
