"""PPO (Node Selection) scheduler. Paper Sec.6.6: at each internal step,
mask infeasible jobs (those whose R_j exceeds remaining free capacity),
score the rest via the actor network's masked softmax (Eq.26, temperature
kappa=1), pick one (argmax in deterministic/eval mode, sample otherwise),
assign it the best-linked node subset (Algorithm 3, same as EPR Node
Selection), and repeat until no feasible job remains -- matching "the
action-selection procedure is repeated until all jobs have been scheduled."
"""
from __future__ import annotations

import torch

from dqc.domain import Assignment, ScheduleDecision, SchedulingState
from dqc.rl.features import build_state_matrix
from dqc.rl.network import ActorCritic
from dqc.schedulers.node_selection import select_best_node_subset

KAPPA = 1.0  # Eq.26 softmax temperature


def masked_softmax(logits: torch.Tensor, feasible_mask: torch.Tensor, kappa: float = KAPPA) -> torch.Tensor:
    masked = logits.masked_fill(~feasible_mask, float("-inf"))
    return torch.softmax(masked / kappa, dim=-1)


class PPOScheduler:
    def __init__(self, network: ActorCritic, deterministic: bool = True):
        self.network = network
        self.deterministic = deterministic

    def select(self, state: SchedulingState) -> ScheduleDecision:
        remaining_jobs = list(state.queued_jobs)
        available = list(sorted(state.free_qpu_ids))
        assignments = []

        while remaining_jobs:
            feasible = [j.qpu_demand <= len(available) for j in remaining_jobs]
            if not any(feasible):
                break
            s = build_state_matrix(remaining_jobs, feasible)
            with torch.no_grad():
                logits = self.network.action_logits(s)
            probs = masked_softmax(logits, torch.tensor(feasible))
            action = int(torch.argmax(probs)) if self.deterministic else int(
                torch.multinomial(probs, 1).item()
            )
            job = remaining_jobs.pop(action)
            chosen = select_best_node_subset(available, job.qpu_demand, state.link_weight)
            available = [q for q in available if q not in chosen]
            assignments.append(Assignment(
                job_id=job.id, qpu_ids=chosen,
                start_time_ns=state.time_ns,
                completion_time_ns=state.time_ns + job.exec_time_ns,
            ))
        return ScheduleDecision(assignments=tuple(assignments))
