"""PPO training loop. Paper Sec.6.6.5: mini-batch 64, update every 1024
collected transitions, cosine LR 1e-3->1e-7, separate models per arrival
rate (we train lambda=5 and lambda=10 first, per the master prompt's
explicit "Start PPO with lambda 5 and 10 before expanding to lambda 4-15").

ponytail: "roughly 100 training epochs to convergence" is read here as 100
outer update iterations (each consuming one 1024-transition rollout batch)
-- the paper doesn't define what one "epoch" means for an online RL loop
collecting its own data, so this is a declared interpretation, not the
authors' literal procedure. Each minibatch is used for exactly ONE gradient
step (the paper doesn't say how many PPO epochs-per-batch either); this is
the simplest faithful reading of the stated hyperparameters and is the
standard single-pass-per-batch PPO default when unspecified.

Training uses OUR engine/workload generator, not Qoala -- every resulting
checkpoint is SCHEDULER_MODEL_REPRODUCTION (ASSUMPTION A1), never
PAPER_REPRODUCTION, regardless of how long it trains.
"""
from __future__ import annotations

import resource
import sys
import time
from dataclasses import dataclass, field

import torch
from torch.optim import Adam
from torch.optim.lr_scheduler import CosineAnnealingLR

from dqc.rl.network import ActorCritic
from dqc.rl.ppo_update import CLIP_EPS, ENTROPY_COEF, GAE_LAMBDA, GAMMA, VALUE_COEF, compute_gae, ppo_clipped_loss
from dqc.rl.train_env import run_episode
from dqc.workload import build_job_catalogue, generate_trace

BUFFER_SIZE = 1024
MINIBATCH_SIZE = 64
LR_START = 1e-3
LR_END = 1e-7


@dataclass
class UpdateLog:
    update: int
    mean_reward: float
    policy_loss: float
    value_loss: float
    entropy: float
    lr: float
    wall_clock_s: float


@dataclass
class TrainingResult:
    network: ActorCritic
    logs: list[UpdateLog] = field(default_factory=list)
    total_wall_clock_s: float = 0.0
    peak_rss_mb: float = 0.0


def _collect_buffer(network: ActorCritic, catalogue, n_qpu: int, lam: float, tau: float, rng_seed: int):
    buffer = []
    episode_rewards = []
    seed = rng_seed
    while len(buffer) < BUFFER_SIZE:
        trace = generate_trace(seed=seed, n_slots=1, lam=lam, tau=tau, catalogue=catalogue, n_qpu_network=n_qpu)
        seed += 1
        jobs = trace.arrivals_by_slot[0]
        if not jobs:
            continue
        transitions = run_episode(network, list(jobs), n_qpu, stochastic=True)
        if not transitions:
            continue
        rewards = [t.reward for t in transitions]
        values = [t.value.item() for t in transitions]
        dones = [t.done for t in transitions]
        advantages, returns = compute_gae(rewards, values, next_value=0.0, dones=dones, gamma=GAMMA, lam=GAE_LAMBDA)
        episode_rewards.append(sum(rewards))
        for t, adv, ret in zip(transitions, advantages, returns):
            buffer.append((t.state, t.action, t.log_prob, adv, ret))
    return buffer[:BUFFER_SIZE], seed, episode_rewards


def train(lam: float, n_updates: int = 100, n_qpu: int = 10, tau: float = 0.0, seed: int = 0) -> TrainingResult:
    torch.manual_seed(seed)
    network = ActorCritic()
    optimizer = Adam(network.parameters(), lr=LR_START)
    lr_scheduler = CosineAnnealingLR(optimizer, T_max=n_updates, eta_min=LR_END)
    catalogue = build_job_catalogue(n_qpu_network=n_qpu)

    result = TrainingResult(network=network)
    t_start = time.perf_counter()
    data_seed = seed * 1_000_000

    for update_i in range(n_updates):
        buffer, data_seed, episode_rewards = _collect_buffer(network, catalogue, n_qpu, lam, tau, data_seed)

        policy_losses, value_losses, entropies = [], [], []
        for mb_start in range(0, len(buffer), MINIBATCH_SIZE):
            minibatch = buffer[mb_start: mb_start + MINIBATCH_SIZE]
            old_log_probs = torch.stack([b[2] for b in minibatch])
            advantages = torch.tensor([b[3] for b in minibatch], dtype=torch.float32)
            returns = torch.tensor([b[4] for b in minibatch], dtype=torch.float32)

            new_log_probs, new_values, entropy_terms = [], [], []
            for state, action, _, _, _ in minibatch:
                logits = network.action_logits(state)
                probs = torch.softmax(logits, dim=-1)
                new_log_probs.append(torch.log(probs[action] + 1e-12))
                entropy_terms.append(-(probs * torch.log(probs + 1e-12)).sum())
                new_values.append(network.value(state))
            new_log_probs = torch.stack(new_log_probs)
            new_values = torch.stack(new_values).squeeze(-1)
            entropy = torch.stack(entropy_terms)

            loss = ppo_clipped_loss(old_log_probs, new_log_probs, advantages, new_values, returns, entropy,
                                     clip_eps=CLIP_EPS, value_coef=VALUE_COEF, entropy_coef=ENTROPY_COEF)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            with torch.no_grad():
                ratio = torch.exp(new_log_probs - old_log_probs)
                clipped = torch.clamp(ratio, 1 - CLIP_EPS, 1 + CLIP_EPS) * advantages
                policy_losses.append((-torch.min(ratio * advantages, clipped).mean()).item())
                value_losses.append(torch.nn.functional.mse_loss(new_values, returns).item())
                entropies.append(entropy.mean().item())

        lr_scheduler.step()
        result.logs.append(UpdateLog(
            update=update_i,
            mean_reward=sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0,
            policy_loss=sum(policy_losses) / len(policy_losses),
            value_loss=sum(value_losses) / len(value_losses),
            entropy=sum(entropies) / len(entropies),
            lr=lr_scheduler.get_last_lr()[0],
            wall_clock_s=time.perf_counter() - t_start,
        ))

    result.total_wall_clock_s = time.perf_counter() - t_start
    # ru_maxrss is bytes on macOS (Darwin), KB on Linux -- normalize to MB.
    raw_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result.peak_rss_mb = raw_rss / (1024 * 1024) if sys.platform == "darwin" else raw_rss / 1024
    return result
