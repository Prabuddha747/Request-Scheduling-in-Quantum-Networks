"""Phase 7 smoke-scale run (10 slots, one seed, small QPU count) across all
eight schedulers on the SAME workload trace. Writes raw per-job records and
a summary table. This is NOT the full 1000-slot/10-QPU paper matrix -- see
docs/assumptions_register.md for why (MILP horizon scale, PPO untrained).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import torch

from dqc.experiment import run_trace
from dqc.metrics import fairness, makespan, non_local_gate_rate, qpu_utilization, selp
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

N_QPUS = 4
QPU_IDS = [f"q{i}" for i in range(N_QPUS)]
SMOKE_QUBIT_COUNTS = (5, 7)  # see tests/integration/test_experiment_smoke.py for why
SLOT_DURATION_NS = 1.5e7
N_SLOTS = 10
SEED = 7

ROOT = Path(__file__).resolve().parent.parent


def link_weight_table():
    params = LINK_QUALITIES["Medium"]
    p_s = entanglement_success_probability(params)
    t_state = state_delay_ns(T_CYCLE_NS["Medium"], p_s)
    return {(a, b): t_state for a in QPU_IDS for b in QPU_IDS if a < b}


def main():
    torch.manual_seed(0)
    catalogue = build_job_catalogue(n_qpu_network=N_QPUS, qubit_counts=SMOKE_QUBIT_COUNTS)
    trace = generate_trace(seed=SEED, n_slots=N_SLOTS, lam=3, tau=0, catalogue=catalogue, n_qpu_network=N_QPUS)
    link_weight = link_weight_table()

    schedulers = {
        "FIFO": (FIFOScheduler(), False),
        "LIST": (ListScheduler(), False),
        "Resource-Priority": (ResourcePriorityScheduler(), False),
        "EPR": (EPRScheduler(), False),
        "EPR (Node Selection)": (EPRNodeSelectionScheduler(), False),
        "MILP": (MILPScheduler(time_scale_ns=100_000.0), False),
        "PPO (Node Selection, UNTRAINED)": (PPOScheduler(ActorCritic(), deterministic=True), False),
        "ASAP": (ASAPScheduler(), True),
    }

    raw_dir = ROOT / "results" / "raw"
    summary_dir = ROOT / "results" / "summary"
    raw_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for name, (scheduler, reinvoke) in schedulers.items():
        records = run_trace(scheduler, trace, QPU_IDS, SLOT_DURATION_NS,
                             reinvoke_on_release=reinvoke, link_weight=link_weight)
        df = pd.DataFrame([r.__dict__ for r in records])
        df["scheduler"] = name
        df.to_csv(raw_dir / f"smoke_{name.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')}.csv", index=False)

        starts = df["start_time_ns"].tolist()
        finishes = df["completion_time_ns"].tolist()
        exec_times = df["exec_time_ns"].tolist()
        qpu_demands = df["qpu_demand"].tolist()
        latencies = (df["completion_time_ns"] - df["arrival_time_ns"]).tolist()

        summary_rows.append({
            "scheduler": name,
            "n_jobs": len(df),
            "makespan_ns": makespan(starts, finishes),
            "qpu_utilization": qpu_utilization(exec_times, qpu_demands, makespan(starts, finishes), N_QPUS),
            "non_local_gate_rate": non_local_gate_rate(starts, finishes),
            "selp": selp(exec_times, latencies),
            "fairness": fairness(exec_times, latencies),
        })
        print(f"{name}: {len(df)} jobs scheduled")

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(summary_dir / "smoke_experiment_summary.csv", index=False)
    print("\n" + summary.to_string(index=False))
    print(f"\nconfig: seed={SEED} slots={N_SLOTS} qpus={N_QPUS} lambda=3 tau=0 "
          f"qubit_counts={SMOKE_QUBIT_COUNTS} slot_duration_ns={SLOT_DURATION_NS}")


if __name__ == "__main__":
    main()
