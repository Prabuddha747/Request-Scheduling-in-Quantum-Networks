"""PPO training mechanics. Paper Sec.6.6.5, Eq.30: gamma=0.99 (discount),
GAE lambda=0.95, clip=0.2, value coef c_v=0.5, entropy coef c_e=0.01.

ponytail: this is the generic PPO update math (GAE + clipped surrogate +
value/entropy terms), paper-parameterized but otherwise standard PPO
(Schulman et al. 2017, cited as ref[23]) -- there's no DQC-specific
variant to transcribe here beyond the hyperparameter values themselves.
"""
from __future__ import annotations

import torch

GAMMA = 0.99
GAE_LAMBDA = 0.95
CLIP_EPS = 0.2
VALUE_COEF = 0.5
ENTROPY_COEF = 0.01


def compute_gae(
    rewards: list[float], values: list[float], next_value: float, dones: list[bool],
    gamma: float = GAMMA, lam: float = GAE_LAMBDA,
) -> tuple[list[float], list[float]]:
    """Returns (advantages, returns), both length len(rewards)."""
    advantages = [0.0] * len(rewards)
    gae = 0.0
    next_v = next_value
    for t in reversed(range(len(rewards))):
        mask = 0.0 if dones[t] else 1.0
        delta = rewards[t] + gamma * next_v * mask - values[t]
        gae = delta + gamma * lam * mask * gae
        advantages[t] = gae
        next_v = values[t]
    returns = [a + v for a, v in zip(advantages, values)]
    return advantages, returns


def ppo_clipped_loss(
    old_log_probs: torch.Tensor, new_log_probs: torch.Tensor, advantages: torch.Tensor,
    new_values: torch.Tensor, returns: torch.Tensor, entropy: torch.Tensor,
    clip_eps: float = CLIP_EPS, value_coef: float = VALUE_COEF, entropy_coef: float = ENTROPY_COEF,
) -> torch.Tensor:
    """Eq.30: L = L_pi + c_v*L_v - c_e*H."""
    ratio = torch.exp(new_log_probs - old_log_probs)
    unclipped = ratio * advantages
    clipped = torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps) * advantages
    policy_loss = -torch.min(unclipped, clipped).mean()
    value_loss = torch.nn.functional.mse_loss(new_values, returns)
    return policy_loss + value_coef * value_loss - entropy_coef * entropy.mean()
