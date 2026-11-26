"""Eq.25: input state matrix S in R^{|J|x4}, rows = [R_j, E_j, T_j, B_j]."""
from __future__ import annotations

import torch

from dqc.domain import DQCJob


def build_state_matrix(jobs: list[DQCJob], feasible_mask: list[bool]) -> torch.Tensor:
    assert len(jobs) == len(feasible_mask)
    rows = [
        [float(j.qpu_demand), float(j.epr_demand), float(j.exec_time_ns), float(feasible)]
        for j, feasible in zip(jobs, feasible_mask)
    ]
    return torch.tensor(rows, dtype=torch.float32) if rows else torch.zeros((0, 4))
