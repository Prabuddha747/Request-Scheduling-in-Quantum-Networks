"""PPO reward terms. Paper Sec.6.6.3, Eq.27-29. Pure functions, unit-tested
against hand-calculated fixtures (master prompt requirement).

Note: the PPO discount factor (gamma=0.99, PPO training hyperparameter) is a
DIFFERENT gamma from the reward term's gamma=0.8 (Eq.28's D_{v-1} weight).
Don't conflate them -- see GAMMA_EPR vs the PPO trainer's own discount.
"""
from __future__ import annotations

GAMMA_EPR = 0.8   # Eq.28 weight on D_{v-1}
BETA_EPR = 0.5    # Eq.28 weight on E_j(o_j+1)
IOTA = 0.3        # Eq.29 weight on R_EPR in the integrated reward


def latency_penalty(latencies: list[float], exec_times_desc: list[float]) -> float:
    """Eq.27: R_lat = sum_j l_j / sum_j (|J|-j+1) e_(j), e_(j) = exec times
    sorted descending (j=1 is the largest)."""
    n = len(exec_times_desc)
    numerator = sum(latencies)
    denominator = sum((n - j + 1) * e for j, e in enumerate(exec_times_desc, start=1))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def epr_incentive(groups: list[list[float]], gamma: float = GAMMA_EPR, beta: float = BETA_EPR) -> float:
    """Eq.28: R_EPR = (1/|J|) sum_v sum_j 1/(beta*E_j*(o_j+1) + gamma*D_{v-1}).

    `groups` is a list of per-step (v) lists of EPR demands E_j, in their
    node-selection priority order (job at list index o_j has priority o_j).
    D_{v-1} = max_j E_j from the PREVIOUS step (D_0 = 0).
    """
    total_jobs = sum(len(g) for g in groups)
    if total_jobs == 0:
        return 0.0
    total = 0.0
    d_prev = 0.0
    for group in groups:
        for o_j, e_j in enumerate(group):
            total += 1.0 / (beta * e_j * (o_j + 1) + gamma * d_prev)
        d_prev = max(group) if group else d_prev
    return total / total_jobs


def integrated_reward(r_lat: float, r_epr: float, iota: float = IOTA) -> float:
    """Eq.29: r = -R_lat + iota * R_EPR."""
    return -r_lat + iota * r_epr
