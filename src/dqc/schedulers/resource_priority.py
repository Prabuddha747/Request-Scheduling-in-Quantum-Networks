"""Resource-Priority scheduler. Paper Algorithm 1: among all combinations of
currently queued jobs that fit within the available QPU capacity, pick the
one maximizing total QPU usage, breaking ties by minimum total estimated
time.

Algorithm 1's own pseudocode is a brute-force powerset search ("for all
combinations C of J"), O(2^n). That was the literal first implementation
here, but it made real experiment runs with realistic backlog (20-30+
queued jobs) impractically slow -- found while running the Phase 7 full-
catalogue matrix. This is a 0/1-knapsack DP instead: EXACT same answer
(maximize total qpu_demand subject to capacity, tie-break on minimum total
exec_time_ns) in O(n_jobs * capacity) instead of O(2^n_jobs). capacity is
small (bounded by the network's QPU count), so this is fast regardless of
queue length -- a root-cause fix, not a job-count cap/truncation.

Algorithm 1's outer "while J != empty" loop (repeatedly picking another
best combo from the remainder) corresponds, in our event-driven engine, to
repeated select() calls as resources free up -- not to looping inside a
single select() call, since each call only sees currently-free QPUs.
"""
from __future__ import annotations

from dqc.domain import Assignment, DQCJob, ScheduleDecision, SchedulingState


def _best_combo(jobs: tuple[DQCJob, ...], capacity: int) -> tuple[DQCJob, ...]:
    # dp[c] = (total_demand, total_time, jobs) for the best combo found so
    # far using at most c capacity.
    dp: list[tuple[int, float, tuple[DQCJob, ...]]] = [(0, 0.0, ()) for _ in range(capacity + 1)]
    for job in jobs:
        if job.qpu_demand > capacity:
            continue
        for c in range(capacity, job.qpu_demand - 1, -1):
            prev_demand, prev_time, prev_combo = dp[c - job.qpu_demand]
            candidate = (prev_demand + job.qpu_demand, prev_time + job.exec_time_ns, prev_combo + (job,))
            current = dp[c]
            if candidate[0] > current[0] or (candidate[0] == current[0] and candidate[1] < current[1]):
                dp[c] = candidate
    return max(dp, key=lambda cell: (cell[0], -cell[1]))[2]


class ResourcePriorityScheduler:
    def select(self, state: SchedulingState) -> ScheduleDecision:
        capacity = len(state.free_qpu_ids)
        best_combo = _best_combo(state.queued_jobs, capacity)

        available = sorted(state.free_qpu_ids)
        assignments = []
        for job in best_combo:
            chosen, available = available[: job.qpu_demand], available[job.qpu_demand :]
            assignments.append(Assignment(
                job_id=job.id, qpu_ids=tuple(chosen),
                start_time_ns=state.time_ns,
                completion_time_ns=state.time_ns + job.exec_time_ns,
            ))
        return ScheduleDecision(assignments=tuple(assignments))
