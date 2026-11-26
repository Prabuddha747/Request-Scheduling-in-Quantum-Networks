"""Training environment: one episode = one slot's arrived jobs, stepped
job-by-job the same way PPOScheduler.select() does, but exposing the
per-step (state, action, log_prob, value, reward) tuples PPO training needs.

ponytail / explicit simplification vs. the real SimPy engine: "waves"
(parallel groups, each its own index v in Eq.28) are tracked by simple
capacity bookkeeping -- a wave ends and capacity resets to n_qpus once no
remaining job fits in what's left of the current wave -- rather than by
simulating genuine overlapping completion times through SimPyBackend. This
is deliberately cheap (fast rollouts matter far more than engine fidelity
for an already-SCHEDULER_MODEL_REPRODUCTION-labeled training signal, see
docs/assumptions_register.md A1) and is a declared approximation, not a
silent one.

The per-step reward is a decomposition of Eq.27-29: each picked job
contributes -l_j/denom_lat to -R_lat and (1/|J|)*epr_term_j to R_EPR, so
summing every transition's reward over a full episode reproduces the
paper's integrated reward r exactly (verified in tests/unit/test_train_env.py
against the already-tested pure functions in reward.py).
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

from dqc.domain import DQCJob
from dqc.rl.features import build_state_matrix
from dqc.rl.network import ActorCritic
from dqc.rl.reward import BETA_EPR, GAMMA_EPR, IOTA


@dataclass
class Transition:
    state: torch.Tensor
    action: int
    log_prob: torch.Tensor
    value: torch.Tensor
    reward: float
    done: bool


def run_episode(network: ActorCritic, jobs: list[DQCJob], n_qpus: int, stochastic: bool = True) -> list[Transition]:
    remaining = list(jobs)
    n = len(jobs)
    if n == 0:
        return []

    free_capacity = n_qpus
    wave_jobs: list[DQCJob] = []
    prev_wave_max_epr = 0.0  # D_0 = 0
    cumulative_time = 0.0

    exec_times_desc = sorted((j.exec_time_ns for j in jobs), reverse=True)
    denom_lat = sum((n - rank + 1) * e for rank, e in enumerate(exec_times_desc, start=1)) or 1.0

    transitions: list[Transition] = []
    while remaining:
        feasible_mask = [j.qpu_demand <= free_capacity for j in remaining]
        if not any(feasible_mask):
            cumulative_time += max((j.exec_time_ns for j in wave_jobs), default=0.0)
            prev_wave_max_epr = max((j.epr_demand for j in wave_jobs), default=prev_wave_max_epr)
            wave_jobs = []
            free_capacity = n_qpus
            continue

        state = build_state_matrix(remaining, feasible_mask)
        feasible_t = torch.tensor(feasible_mask)
        logits = network.action_logits(state)
        probs = torch.softmax(logits.masked_fill(~feasible_t, float("-inf")), dim=-1)
        value = network.value(state)

        action = int(torch.multinomial(probs, 1).item()) if stochastic else int(torch.argmax(probs))
        log_prob = torch.log(probs[action] + 1e-12)

        job = remaining.pop(action)
        free_capacity -= job.qpu_demand
        o_j = len(wave_jobs)
        wave_jobs.append(job)

        latency = cumulative_time + job.exec_time_ns
        r_lat_term = latency / denom_lat
        epr_denom = BETA_EPR * job.epr_demand * (o_j + 1) + GAMMA_EPR * prev_wave_max_epr
        r_epr_term = (1.0 / n) * (1.0 / epr_denom) if epr_denom > 0 else 0.0
        reward = -r_lat_term + IOTA * r_epr_term

        transitions.append(Transition(
            state=state, action=action, log_prob=log_prob.detach(), value=value.detach(),
            reward=reward, done=not remaining,
        ))
    return transitions
