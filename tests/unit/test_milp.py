from itertools import product

from dqc.domain import DQCJob, SchedulingState
from dqc.schedulers.milp import MILPScheduler


def _job(id_, qpu_demand, exec_time_ns):
    return DQCJob(id=id_, circuit_type="ghz", n_qubits=5, qpu_demand=qpu_demand,
                  epr_demand=0, exec_time_ns=exec_time_ns, arrival_slot=0)


def _brute_force_optimal_makespan(durations, demands, capacity):
    """Exhaustive search over every (m_1..m_n) combo on the same integer
    time grid the MILP uses, for cross-validation on tiny instances."""
    horizon = sum(durations)
    candidate_starts = [range(0, horizon - d + 1) for d in durations]
    best = None
    for combo in product(*candidate_starts):
        feasible = True
        for t in range(horizon):
            load = sum(demands[j] for j, m in enumerate(combo) if m <= t < m + durations[j])
            if load > capacity:
                feasible = False
                break
        if feasible:
            makespan = max(m + d for m, d in zip(combo, durations))
            if best is None or makespan < best:
                best = makespan
    return best


def test_milp_matches_brute_force_tiny_instance():
    jobs = [_job("j0", 2, 3), _job("j1", 1, 2), _job("j2", 1, 4)]
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2"}), queued_jobs=tuple(jobs))
    scheduler = MILPScheduler()
    scheduler.select(state)
    expected = _brute_force_optimal_makespan([3, 2, 4], [2, 1, 1], capacity=3)
    assert scheduler.last_solve.status == "optimal"
    assert scheduler.last_solve.objective == expected


def test_milp_matches_brute_force_forced_sequential_instance():
    # two jobs that both need all capacity -- must run sequentially.
    jobs = [_job("j0", 2, 5), _job("j1", 2, 3)]
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0", "q1"}), queued_jobs=tuple(jobs))
    scheduler = MILPScheduler()
    scheduler.select(state)
    expected = _brute_force_optimal_makespan([5, 3], [2, 2], capacity=2)
    assert expected == 8  # no overlap possible
    assert scheduler.last_solve.objective == expected


def test_milp_logs_solve_diagnostics():
    jobs = [_job("j0", 1, 1)]
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0"}), queued_jobs=tuple(jobs))
    scheduler = MILPScheduler()
    scheduler.select(state)
    assert scheduler.last_solve.status == "optimal"
    assert scheduler.last_solve.solve_time_s >= 0
    assert scheduler.last_solve.optimality_gap == 0.0


def test_milp_empty_queue_returns_empty_decision():
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0"}), queued_jobs=())
    scheduler = MILPScheduler()
    decision = scheduler.select(state)
    assert decision.assignments == ()
    assert scheduler.last_solve.status == "empty"


def test_milp_only_returns_jobs_starting_now():
    # forced-sequential case: exactly one of j0/j1 must wait (the makespan
    # is the same, 8, either order -- the solver is free to pick either),
    # so exactly one job should be in this call's decision, not both.
    jobs = [_job("j0", 2, 5), _job("j1", 2, 3)]
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0", "q1"}), queued_jobs=tuple(jobs))
    decision = MILPScheduler().select(state)
    assert len(decision.assignments) == 1
    assert decision.assignments[0].job_id in {"j0", "j1"}
