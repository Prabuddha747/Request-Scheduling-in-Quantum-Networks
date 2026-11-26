"""Regression test for the drain-loop bug found in the Phase 7 full-
catalogue run: non-reinvoke schedulers (MILP, Resource-Priority, ...) must
NOT be re-solved after every single job completion during drain, only once
per fully-finished batch -- otherwise a backlog makes this pathologically
slow (previously observed: >6 minutes, here it must finish in seconds)."""
from __future__ import annotations

import time

from dqc.experiment import run_trace
from dqc.schedulers.milp import MILPScheduler
from dqc.workload import build_job_catalogue, generate_trace

N_QPUS = 10
QPU_IDS = [f"node{i}" for i in range(N_QPUS)]


def test_milp_full_catalogue_drain_does_not_pathologically_reinvoke():
    catalogue = build_job_catalogue(n_qpu_network=N_QPUS)
    trace = generate_trace(seed=7, n_slots=5, lam=5, tau=0, catalogue=catalogue, n_qpu_network=N_QPUS)
    total_arrived = sum(len(s) for s in trace.arrivals_by_slot)

    t0 = time.perf_counter()
    records = run_trace(MILPScheduler(), trace, QPU_IDS, slot_duration_ns=1.5e10, reinvoke_on_release=False)
    elapsed = time.perf_counter() - t0

    assert len(records) == total_arrived
    assert elapsed < 30, f"drain loop took {elapsed:.1f}s -- regression of the per-completion reinvoke bug?"
