"""Resource-Priority scheduler. Paper Algorithm 1: among all combinations of
currently queued jobs that fit within the available QPU capacity, pick the
one maximizing total QPU usage, breaking ties by minimum total estimated
time.

ponytail: brute-force over the job powerset, O(2^n), exactly matching
Algorithm 1's own pseudocode ("for all combinations C of J"). Fine for the
paper's per-slot queue sizes (truncated-Poisson arrivals, a handful of jobs
per slot); upgrade to a knapsack DP (by qpu_demand) if queues grow large.

Algorithm 1's outer "while J != empty" loop (repeatedly picking another
best combo from the remainder) corresponds, in our event-driven engine, to
repeated select() calls as resources free up -- not to looping inside a
single select() call, since each call only sees currently-free QPUs.
"""
from __future__ import annotations

from itertools import combinations

from dqc.domain import Assignment, ScheduleDecision, SchedulingState


class ResourcePriorityScheduler:
    def select(self, state: SchedulingState) -> ScheduleDecision:
        jobs = state.queued_jobs
        capacity = len(state.free_qpu_ids)
        best_combo: tuple = ()
        best_util = 0
        best_time = float("inf")
        for size in range(1, len(jobs) + 1):
            for combo in combinations(jobs, size):
                total_demand = sum(j.qpu_demand for j in combo)
                if total_demand > capacity:
                    continue
                total_time = sum(j.exec_time_ns for j in combo)
                if total_demand > best_util or (total_demand == best_util and total_time < best_time):
                    best_combo, best_util, best_time = combo, total_demand, total_time

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
