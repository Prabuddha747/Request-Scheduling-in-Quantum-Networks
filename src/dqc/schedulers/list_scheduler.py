"""LIST scheduler. Paper Sec.6.7.2 / Table 1 and ref[7] Algorithm 1
(List-Scheduling): a single forward pass over the arrival-ordered queue;
a job that doesn't currently fit is skipped (bypassed) rather than ending
the group, so a later, smaller job can still be grouped with earlier ones.
"""
from __future__ import annotations

from dqc.domain import Assignment, ScheduleDecision, SchedulingState


class ListScheduler:
    def select(self, state: SchedulingState) -> ScheduleDecision:
        available = sorted(state.free_qpu_ids)
        assignments = []
        for job in state.queued_jobs:
            if job.qpu_demand > len(available):
                continue  # bypass: does not end the group, unlike FIFO
            chosen, available = available[: job.qpu_demand], available[job.qpu_demand :]
            assignments.append(Assignment(
                job_id=job.id,
                qpu_ids=tuple(chosen),
                start_time_ns=state.time_ns,
                completion_time_ns=state.time_ns + job.exec_time_ns,
            ))
            if not available:
                break
        return ScheduleDecision(assignments=tuple(assignments))
