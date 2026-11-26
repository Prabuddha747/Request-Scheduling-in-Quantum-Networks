"""EPR and EPR (Node Selection) schedulers. Paper Sec.6.2-6.3 / Table 1.

Body text + Algorithm 2: sort the queue ascending by E_j (EPR demand), then
do a single forward pass that stops at the first job that doesn't fit --
Table 1 gives EPR the same "next job cannot be grouped" end condition as
FIFO, confirming it's FIFO's own grouping logic re-applied to an
EPR-sorted queue, not a different search strategy.
"""
from __future__ import annotations

from dqc.domain import Assignment, ScheduleDecision, SchedulingState
from dqc.schedulers.node_selection import select_best_node_subset


def _sorted_by_epr(state: SchedulingState) -> tuple:
    return tuple(sorted(state.queued_jobs, key=lambda j: j.epr_demand))


class EPRScheduler:
    def select(self, state: SchedulingState) -> ScheduleDecision:
        available = sorted(state.free_qpu_ids)
        assignments = []
        for job in _sorted_by_epr(state):
            if job.qpu_demand > len(available):
                break  # same "next job cannot be grouped" end condition as FIFO
            chosen, available = available[: job.qpu_demand], available[job.qpu_demand :]
            assignments.append(Assignment(
                job_id=job.id, qpu_ids=tuple(chosen),
                start_time_ns=state.time_ns,
                completion_time_ns=state.time_ns + job.exec_time_ns,
            ))
        return ScheduleDecision(assignments=tuple(assignments))


class EPRNodeSelectionScheduler:
    """EPR ordering + Algorithm 3 node selection (best-linked subset) instead
    of an arbitrary subset of available QPUs."""

    def select(self, state: SchedulingState) -> ScheduleDecision:
        available = list(sorted(state.free_qpu_ids))
        assignments = []
        for job in _sorted_by_epr(state):
            if job.qpu_demand > len(available):
                break
            chosen = select_best_node_subset(available, job.qpu_demand, state.link_weight)
            available = [q for q in available if q not in chosen]
            assignments.append(Assignment(
                job_id=job.id, qpu_ids=chosen,
                start_time_ns=state.time_ns,
                completion_time_ns=state.time_ns + job.exec_time_ns,
            ))
        return ScheduleDecision(assignments=tuple(assignments))
