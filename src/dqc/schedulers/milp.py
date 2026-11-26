"""MILP scheduler. Paper Sec.6.5, Eq.20-24, Algorithm 5: time-indexed RCPSP.

ponytail: horizon H = sum(T_j) over INTEGER time units. Raw nanosecond
DQCJob.exec_time_ns would make H astronomically large (sum of ~1e8-1e10 ns
values => a billions-of-steps horizon). `time_scale_ns=None` (the default)
auto-derives a scale each call from the CURRENT queue's own durations,
targeting `target_horizon_steps` discrete steps regardless of how large or
small the actual ns values are -- this is what makes MILP usable at any
scale without per-experiment manual tuning (previously (A8) required a
hand-picked constant; auto-scaling closes that gap). The returned
Assignment still carries the job's original (unrounded) exec_time_ns for
completion timing -- only the internal search grid is coarsened, which
trades makespan precision (bounded by horizon/target_horizon_steps) for
tractability, a real approximation, not a free lunch.

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
    horizon_steps: int = 0
    time_scale_ns_used: float = 1.0


DEFAULT_TARGET_HORIZON_STEPS = 500
DEFAULT_MAX_JOBS_PER_SOLVE = 15
DEFAULT_SOLVER_TIME_LIMIT_S = 20.0


class MILPScheduler:
    """ponytail: `max_jobs_per_solve` caps the per-call MIP instance size.
    Unlike target_horizon_steps (a time-grid coarseness/precision tradeoff),
    this exists because real MIP solve time does NOT scale predictably with
    instance size -- a burst of 20-30+ queued jobs can make a single HiGHS
    solve take an unpredictable amount of time (observed: minutes, not the
    seconds a similarly-sized smaller instance takes). Solving only the
    oldest `max_jobs_per_solve` queued jobs each call (remaining jobs wait
    for a later call, exactly like any rolling-horizon MILP scheduler in
    practice) keeps solve time bounded and predictable. Upgrade path: raise
    this if a given machine's HiGHS build handles larger instances reliably.

    `solver_time_limit_s` is a second, independent safety net: even at a
    capped instance size, a SPECIFIC instance can occasionally be a hard
    MIP for HiGHS's branch-and-bound (observed directly: one real instance
    here ran past several minutes with no sign of stopping, vs. ~1-4s
    typical). HiGHS is told to stop after this many seconds and return its
    best incumbent; `MILPSolveInfo.status` becomes "time_limit" and
    `optimality_gap` reports HiGHS's own relative MIP gap at cutoff (not
    0.0 -- the master prompt requires logging solver status/gap honestly,
    so a time-limited solve must never be reported as "optimal")."""

    def __init__(
        self, time_scale_ns: float | None = None, target_horizon_steps: int = DEFAULT_TARGET_HORIZON_STEPS,
        max_jobs_per_solve: int = DEFAULT_MAX_JOBS_PER_SOLVE,
        solver_time_limit_s: float = DEFAULT_SOLVER_TIME_LIMIT_S,
    ):
        self.time_scale_ns = time_scale_ns
        self.target_horizon_steps = target_horizon_steps
        self.max_jobs_per_solve = max_jobs_per_solve
        self.solver_time_limit_s = solver_time_limit_s
        self.last_solve: MILPSolveInfo | None = None

    def select(self, state: SchedulingState) -> ScheduleDecision:
        jobs = list(state.queued_jobs)[: self.max_jobs_per_solve]
        capacity = len(state.free_qpu_ids)
        if not jobs:
            self.last_solve = MILPSolveInfo("empty", 0.0, 0.0, 0.0)
            return ScheduleDecision()

        raw_total_ns = sum(j.exec_time_ns for j in jobs)
        scale = self.time_scale_ns or max(1.0, raw_total_ns / self.target_horizon_steps)
        durations = [max(1, round(j.exec_time_ns / scale)) for j in jobs]
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
        result = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds,
                      options={"time_limit": self.solver_time_limit_s})
        solve_time = _time.perf_counter() - t0

        if not result.success:
            self.last_solve = MILPSolveInfo("infeasible_or_failed", None, solve_time, None, horizon, scale)
            return ScheduleDecision()
        gap = float(getattr(result, "mip_gap", 0.0) or 0.0)
        status = "optimal" if getattr(result, "status", 0) == 0 else "time_limit"
        self.last_solve = MILPSolveInfo(status, float(result.fun), solve_time, gap, horizon, scale)

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
