"""Paper Sec.5, Eq.12-19. Pure functions, each unit-tested against a
hand-calculated fixture (master prompt requirement). Inputs are plain
numeric sequences, not domain objects, so these stay reusable regardless
of which backend/scheduler produced the timings.
"""
from __future__ import annotations

import statistics

from scipy.stats import gmean


def makespan(start_times: list[float], finish_times: list[float]) -> float:
    """Eq.12: M = max(t_j^f) - min(t_j^s)."""
    return max(finish_times) - min(start_times)


def qpu_utilization(exec_times: list[float], qpu_demands: list[int], makespan_value: float, n_qpu: int) -> float:
    """Eq.13: U_QPU = sum(p_j q_j) / (M n_QPU)."""
    if makespan_value == 0 or n_qpu == 0:
        return 0.0
    return sum(p * q for p, q in zip(exec_times, qpu_demands)) / (makespan_value * n_qpu)


def non_local_gate_rate(start_times: list[float], finish_times: list[float]) -> float:
    """Eq.14-16: U_g = T_overlap / T_max, the pairwise execution-time-overlap
    ratio -- NOT a physical non-local-gate counter (see docs/source_traceability.csv).

    Edge case not addressed by the paper: with 0 or 1 jobs there are no
    pairs, so T_max = 0. We return 1.0 in that case (trivially "fully
    overlapping": the paper's own Fig.6 caption treats full overlap as
    rate=1 when few jobs are fully parallelizable) -- a declared edge-case
    interpretation, not a fabricated result.
    """
    n = len(start_times)
    t_overlap = 0.0
    t_max = 0.0
    for j in range(n):
        for k in range(j + 1, n):
            t_overlap += max(0.0, min(finish_times[j], finish_times[k]) - max(start_times[j], start_times[k]))
            t_max += min(finish_times[j] - start_times[j], finish_times[k] - start_times[k])
    if t_max == 0:
        return 1.0
    return t_overlap / t_max


def execution_latency_performance(exec_times: list[float], latencies: list[float]) -> list[float]:
    """Eq.17: ELP_j = e_j / l_j, for every job j."""
    return [e / l for e, l in zip(exec_times, latencies)]


def selp(exec_times: list[float], latencies: list[float]) -> float:
    """Eq.18: SELP = geometric mean of ELP_j."""
    elp = execution_latency_performance(exec_times, latencies)
    return float(gmean(elp))


def fairness(exec_times: list[float], latencies: list[float]) -> float:
    """Eq.19: f = 1 - stdev(ELP).

    The paper doesn't say population vs. sample stdev; we use population
    stdev (the jobs given ARE the complete set being evaluated for that
    slot/condition, not a sample of a larger population) -- a declared
    interpretation choice.
    """
    elp = execution_latency_performance(exec_times, latencies)
    if len(elp) < 2:
        return 1.0  # no variation possible with 0-1 jobs
    return 1.0 - statistics.pstdev(elp)
