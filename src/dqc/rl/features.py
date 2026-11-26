"""Eq.25: input state matrix S in R^{|J|x4}, rows = [R_j, E_j, T_j, B_j].

ponytail: the paper's Eq.25 doesn't mention feature scaling, but T_j
(exec_time_ns) is ~1e8-1e9 while R_j/E_j/B_j are O(1-100) -- feeding that
straight into a freshly-initialized nn.Linear blows up the critic's output
(observed: value_loss ~1e14 before this fix). T_J_SCALE_NS rescales T_j to
roughly the same O(1-100) order as the other features; this is a necessary
implementation detail for numerical stability, not a sourced paper value.
"""
from __future__ import annotations

import torch

from dqc.domain import DQCJob

T_J_SCALE_NS = 1e7  # brings exec_time_ns (~1e8-1e9) down to a ~10-100 range


def build_state_matrix(jobs: list[DQCJob], feasible_mask: list[bool]) -> torch.Tensor:
    assert len(jobs) == len(feasible_mask)
    rows = [
        [float(j.qpu_demand), float(j.epr_demand), j.exec_time_ns / T_J_SCALE_NS, float(feasible)]
        for j, feasible in zip(jobs, feasible_mask)
    ]
    return torch.tensor(rows, dtype=torch.float32) if rows else torch.zeros((0, 4))
