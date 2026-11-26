from dqc.domain import DQCJob, ScheduleDecision, SchedulingState
from dqc.engine import SimPyBackend
from dqc.schedulers.fifo import FIFOScheduler
from dqc.schedulers.list_scheduler import ListScheduler


def _job(id_, qpu_demand, exec_time_ns=10.0):
    return DQCJob(id=id_, circuit_type="ghz", n_qubits=5, qpu_demand=qpu_demand,
                  epr_demand=0, exec_time_ns=exec_time_ns, arrival_slot=0)


def test_fifo_stops_at_first_job_that_cannot_be_grouped():
    # j0 needs 2 (fits in 3 free), j1 needs 2 (does NOT fit in remaining 1),
    # j2 needs 1 (WOULD fit, but FIFO must not bypass j1).
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2"}),
        queued_jobs=(_job("j0", 2), _job("j1", 2), _job("j2", 1)),
    )
    decision = FIFOScheduler().select(state)
    assert [a.job_id for a in decision.assignments] == ["j0"]


def test_list_bypasses_blocked_job_unlike_fifo():
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2"}),
        queued_jobs=(_job("j0", 2), _job("j1", 2), _job("j2", 1)),
    )
    decision = ListScheduler().select(state)
    assert [a.job_id for a in decision.assignments] == ["j0", "j2"]


def test_fifo_and_list_run_end_to_end_through_engine():
    for scheduler_cls in (FIFOScheduler, ListScheduler):
        backend = SimPyBackend(qpu_ids=["q0", "q1", "q2"])
        state = SchedulingState(
            time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2"}),
            queued_jobs=(_job("j0", 2), _job("j1", 1)),
        )
        decision = scheduler_cls().select(state)
        backend.submit(decision)
        backend.run_until(10)
        snap = backend.snapshot()
        assert snap.free_qpu_ids == frozenset({"q0", "q1", "q2"})
        completed = {e.job_id for e in snap.events if e.kind == "job_completed"}
        assert completed == {"j0", "j1"}
