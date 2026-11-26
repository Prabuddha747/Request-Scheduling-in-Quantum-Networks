"""Phase 7 gate: smoke test (10 slots, one seed, small QPU count) across
ALL EIGHT schedulers on the SAME workload trace (paired comparison)."""
from __future__ import annotations

import torch

from dqc.experiment import run_trace
from dqc.network import LINK_QUALITIES, T_CYCLE_NS, entanglement_success_probability, state_delay_ns
from dqc.rl.network import ActorCritic
from dqc.rl.ppo_scheduler import PPOScheduler
from dqc.schedulers.asap import ASAPScheduler
from dqc.schedulers.epr import EPRNodeSelectionScheduler, EPRScheduler
from dqc.schedulers.fifo import FIFOScheduler
from dqc.schedulers.list_scheduler import ListScheduler
from dqc.schedulers.milp import MILPScheduler
from dqc.schedulers.resource_priority import ResourcePriorityScheduler
from dqc.workload import build_job_catalogue, generate_trace

N_QPUS = 4  # small QPU count per the smoke-test gate
QPU_IDS = [f"q{i}" for i in range(N_QPUS)]
# Restrict the smoke run to the catalogue's 5/7-qubit templates: the full
# 30-template catalogue includes jobs up to ~7s of simulated exec time
# (qft_15), which would backlog a 4-QPU/10-slot smoke run into queues large
# enough to blow up ResourcePriorityScheduler's O(2^n) search and MILP's
# time-indexed horizon -- neither is a bug, both are the documented
# complexity ceilings in those schedulers' own ponytail comments. The full
# catalogue belongs in a real (non-smoke) Phase 7 run sized accordingly.
SMOKE_QUBIT_COUNTS = (5, 7)
SLOT_DURATION_NS = 1.5e7  # comfortably above the largest smoke-catalogue exec time


def _homogeneous_link_weight():
    params = LINK_QUALITIES["Medium"]
    p_s = entanglement_success_probability(params)
    t_state = state_delay_ns(T_CYCLE_NS["Medium"], p_s)
    return {(a, b): t_state for a in QPU_IDS for b in QPU_IDS if a < b}


def _small_trace():
    catalogue = build_job_catalogue(n_qpu_network=N_QPUS, qubit_counts=SMOKE_QUBIT_COUNTS)
    return generate_trace(seed=7, n_slots=10, lam=3, tau=0, catalogue=catalogue, n_qpu_network=N_QPUS)


def _assert_valid_records(records, total_arrived):
    assert len(records) == total_arrived, "every arrived job must eventually be scheduled"
    seen_ids = {r.job_id for r in records}
    assert len(seen_ids) == len(records), "no job scheduled twice"
    for r in records:
        assert r.completion_time_ns >= r.start_time_ns >= r.arrival_time_ns


def test_fifo_list_epr_resource_priority_asap_smoke():
    trace = _small_trace()
    total_arrived = sum(len(s) for s in trace.arrivals_by_slot)
    link_weight = _homogeneous_link_weight()

    for scheduler, reinvoke in [
        (FIFOScheduler(), False),
        (ListScheduler(), False),
        (ResourcePriorityScheduler(), False),
        (EPRScheduler(), False),
        (EPRNodeSelectionScheduler(), False),
        (ASAPScheduler(), True),
    ]:
        records = run_trace(scheduler, trace, QPU_IDS, SLOT_DURATION_NS,
                             reinvoke_on_release=reinvoke, link_weight=link_weight)
        _assert_valid_records(records, total_arrived)


def test_milp_smoke():
    trace = _small_trace()
    total_arrived = sum(len(s) for s in trace.arrivals_by_slot)
    scheduler = MILPScheduler(time_scale_ns=100_000.0)  # coarser grid for a tractable smoke horizon
    records = run_trace(scheduler, trace, QPU_IDS, SLOT_DURATION_NS)
    _assert_valid_records(records, total_arrived)


def test_ppo_smoke_runs_without_crashing():
    """PPO here is an UNTRAINED (randomly-initialized) network -- this only
    confirms the scheduler wires into the runner correctly, not that it
    produces paper-representative scheduling decisions."""
    torch.manual_seed(0)
    trace = _small_trace()
    total_arrived = sum(len(s) for s in trace.arrivals_by_slot)
    link_weight = _homogeneous_link_weight()
    scheduler = PPOScheduler(ActorCritic(), deterministic=True)
    records = run_trace(scheduler, trace, QPU_IDS, SLOT_DURATION_NS, link_weight=link_weight)
    _assert_valid_records(records, total_arrived)
