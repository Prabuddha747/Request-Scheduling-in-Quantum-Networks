"""MILP scheduler. Paper Sec.6.5, Eq.20-24, Algorithm 5: time-indexed RCPSP.

ponytail: horizon H = sum(T_j) over INTEGER time units. Raw nanosecond
DQCJob.exec_time_ns would make H astronomically large (sum of ~1e8-1e10 ns
values => a billions-of-steps horizon), so `time_scale_ns` rescales/rounds
durations to a manageable integer grid before solving; the returned
Assignment still carries the job's original (unrounded) exec_time_ns for
completion timing. This scheduler is for Phase 4's small-instance
comparisons per the master prompt, not full 1000-slot/10-QPU production
runs -- see docs/assumptions_register.md for the scale-up gap (upgrade
path: a rolling/receding horizon or a coarser time grid if full-scale MILP
runs are ever needed).

Node selection is out of scope here (paper gives MILP a total-capacity
resource constraint only, no node-quality awareness -- Table 1 doesn't list
"node selection" as a MILP feature either).
"""
from __future__ import annotations

import time as _time
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from dqc.domain import Assignment, ScheduleDecision, SchedulingState


@dataclass(frozen=True)
class MILPSolveInfo:
    status: str
    objective: float | None
    solve_time_s: float
    optimality_gap: float | None


class MILPScheduler:
    def __init__(self, time_scale_ns: float = 1.0):
        self.time_scale_ns = time_scale_ns
        self.last_solve: MILPSolveInfo | None = None

    def select(self, state: SchedulingState) -> ScheduleDecision:
        jobs = list(state.queued_jobs)
        capacity = len(state.free_qpu_ids)
        if not jobs:
            self.last_solve = MILPSolveInfo("empty", 0.0, 0.0, 0.0)
            return ScheduleDecision()

        durations = [max(1, round(j.exec_time_ns / self.time_scale_ns)) for j in jobs]
        demands = [j.qpu_demand for j in jobs]
        horizon = sum(durations)

        starts = [list(range(0, horizon - d + 1)) for d in durations]
        offsets = []
        idx = 0
        for s in starts:
            offsets.append(idx)
            idx += len(s)
        n_x = idx
        m_idx = n_x  # makespan variable
        n_vars = n_x + 1

        c = np.zeros(n_vars)
        c[m_idx] = 1.0  # Eq.22: minimize M

        constraints = []
        for j, s in enumerate(starts):  # Eq.23: each job starts exactly once
            row = np.zeros(n_vars)
            row[offsets[j]: offsets[j] + len(s)] = 1.0
            constraints.append(LinearConstraint(row, 1, 1))

        for j, s in enumerate(starts):  # Eq.22 linearized: M >= m_j + T_j for the chosen m
            row = np.zeros(n_vars)
            for k, m in enumerate(s):
                row[offsets[j] + k] = m + durations[j]
            row[m_idx] = -1.0
            constraints.append(LinearConstraint(row, -np.inf, 0))

        for t in range(horizon):  # Eq.24: resource capacity at every time step
            row = np.zeros(n_vars)
            touched = False
            for j, s in enumerate(starts):
                for k, m in enumerate(s):
                    if m <= t < m + durations[j]:
                        row[offsets[j] + k] = demands[j]
                        touched = True
            if touched:
                constraints.append(LinearConstraint(row, -np.inf, capacity))

        integrality = np.ones(n_vars)
        integrality[m_idx] = 0
        bounds = Bounds(lb=np.zeros(n_vars), ub=np.concatenate([np.ones(n_x), [horizon]]))

        t0 = _time.perf_counter()
        result = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds)
        solve_time = _time.perf_counter() - t0

        if not result.success:
            self.last_solve = MILPSolveInfo(result.status if hasattr(result, "status") else "failed",
                                             None, solve_time, None)
            return ScheduleDecision()
        self.last_solve = MILPSolveInfo("optimal", float(result.fun), solve_time, 0.0)

        x = result.x[:n_x]
        available = sorted(state.free_qpu_ids)
        assignments = []
        for j, s in enumerate(starts):
            chosen_m = next((m for k, m in enumerate(s) if x[offsets[j] + k] > 0.5), None)
            if chosen_m == 0:  # only jobs starting right now are actionable this call
                qpu_ids, available = available[: demands[j]], available[demands[j]:]
                assignments.append(Assignment(
                    job_id=jobs[j].id, qpu_ids=tuple(qpu_ids),
                    start_time_ns=state.time_ns,
                    completion_time_ns=state.time_ns + jobs[j].exec_time_ns,
                ))
        return ScheduleDecision(assignments=tuple(assignments))
