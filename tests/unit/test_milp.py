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


def test_milp_falls_back_to_smaller_batch_when_full_batch_times_out(monkeypatch):
    """Regression test for a real finding: at high backlog, a specific
    15-job MIP instance was observed to deterministically fail (time out
    without even a feasible incumbent) on every retry -- retrying the
    identical instance can never help. The scheduler must shrink the batch
    and retry smaller, not give up or loop forever on the same instance."""
    import dqc.schedulers.milp as milp_mod

    real_milp = milp_mod.milp
    calls = []

    def flaky_milp(c, constraints, integrality, bounds, options=None):
        calls.append(len(c))
        # simulate: any batch of size > 2 variables worth "fails" every time
        if len(c) > 5:
            class Failed:
                success = False
            return Failed()
        return real_milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds, options=options)

    monkeypatch.setattr(milp_mod, "milp", flaky_milp)
    jobs = [_job(f"j{i}", 1, 2) for i in range(8)]
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0", "q1"}), queued_jobs=tuple(jobs))
    decision = MILPScheduler(max_jobs_per_solve=8).select(state)
    assert len(decision.assignments) >= 1  # eventually succeeded at a smaller batch size
    assert len(calls) > 1  # actually retried at a smaller size, didn't just fail once


def test_milp_empty_queue_returns_empty_decision():
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0"}), queued_jobs=())
    scheduler = MILPScheduler()
    decision = scheduler.select(state)
    assert decision.assignments == ()
    assert scheduler.last_solve.status == "empty"


def test_milp_tiebreaks_toward_starting_jobs_now():
    """Regression test for a real bug: several small jobs that easily fit
    together within capacity, all tied on makespan whether or not they all
    start immediately -- the solver must prefer starting them NOW (this
    scheduler only acts on jobs with chosen_m==0; a tie broken the other
    way silently starves the queue even though nothing is overloaded,
    exactly as observed in a real experiment run)."""
    jobs = [_job(f"j{i}", 1, 2) for i in range(5)]  # 5 jobs, 1 QPU each, same duration
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2", "q3", "q4"}), queued_jobs=tuple(jobs))
    decision = MILPScheduler().select(state)
    assert len(decision.assignments) == 5  # all 5 fit at once and all should start now


def test_milp_only_returns_jobs_starting_now():
    # forced-sequential case: exactly one of j0/j1 must wait (the makespan
    # is the same, 8, either order -- the solver is free to pick either),
    # so exactly one job should be in this call's decision, not both.
    jobs = [_job("j0", 2, 5), _job("j1", 2, 3)]
    state = SchedulingState(time_ns=0, free_qpu_ids=frozenset({"q0", "q1"}), queued_jobs=tuple(jobs))
    decision = MILPScheduler().select(state)
    assert len(decision.assignments) == 1
    assert decision.assignments[0].job_id in {"j0", "j1"}
