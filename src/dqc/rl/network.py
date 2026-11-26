"""PPO actor-critic network. Paper Sec.6.6.1-6.6.2, 6.6.5:
- Actor: each job independently encoded by a shared 2-layer MLP (hidden=64,
  ReLU), outputting one logit per job.
- Critic: flattened state through one hidden layer (64, ReLU), linear
  scalar value head.

ponytail: the critic needs a FIXED-size input, but the paper's state matrix
S is |J|x4 with |J| varying per scheduling step. The paper doesn't specify
a max queue length for this -- `max_jobs` zero-pads/truncates the flattened
state, an implementation necessity rather than a paper detail (documented
in docs/assumptions_register.md).
"""
from __future__ import annotations

import torch
from torch import nn

N_FEATURES = 4  # R_j, E_j, T_j, B_j (Eq.25)


class ActorCritic(nn.Module):
    def __init__(self, hidden_dim: int = 64, max_jobs: int = 32):
        super().__init__()
        self.max_jobs = max_jobs
        self.actor = nn.Sequential(
            nn.Linear(N_FEATURES, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )
        self.critic = nn.Sequential(
            nn.Linear(N_FEATURES * max_jobs, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def action_logits(self, state: torch.Tensor) -> torch.Tensor:
        """state: (n_jobs, N_FEATURES) -> (n_jobs,) one logit per job."""
        return self.actor(state).squeeze(-1)

    def value(self, state: torch.Tensor) -> torch.Tensor:
        """state: (n_jobs, N_FEATURES), n_jobs <= max_jobs -> scalar value."""
        n_jobs = state.shape[0]
        padded = state.new_zeros(self.max_jobs, N_FEATURES)
        padded[: min(n_jobs, self.max_jobs)] = state[: self.max_jobs]
        return self.critic(padded.flatten())
