"""FIFO scheduler. Paper Sec.6.7.1 / Table 1: strict arrival order; a job is
grouped into the current parallel step only while nodes allow, and the
group ends as soon as the next queued job cannot be grouped (it does not
look further ahead -- that bypass behavior is LIST's, see list_scheduler.py).
"""
from __future__ import annotations

from dqc.domain import Assignment, ScheduleDecision, SchedulingState


class FIFOScheduler:
    def select(self, state: SchedulingState) -> ScheduleDecision:
        available = sorted(state.free_qpu_ids)
        assignments = []
        for job in state.queued_jobs:
            if job.qpu_demand > len(available):
                break  # next job cannot be grouped -> end of parallel group
            chosen, available = available[: job.qpu_demand], available[job.qpu_demand :]
            assignments.append(Assignment(
                job_id=job.id,
                qpu_ids=tuple(chosen),
                start_time_ns=state.time_ns,
                completion_time_ns=state.time_ns + job.exec_time_ns,
            ))
        return ScheduleDecision(assignments=tuple(assignments))
