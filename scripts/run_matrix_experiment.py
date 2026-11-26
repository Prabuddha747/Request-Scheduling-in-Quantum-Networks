"""Phase 7 condition-matrix run: lambda in {5,10} x tau in {0,0.5}, full
30-template catalogue, heterogeneous links, matched trained PPO checkpoints.

Reduced from the paper's 1000 slots to 30 slots/condition and 1 seed (not
paper's seed count / 10+) -- a disclosed reduction (master prompt's own
rule: document reductions, don't silently shrink coverage), driven by
MILP's real per-call solver overhead (~0.3-1s x up to a few hundred calls
per condition) on this M1. See docs/assumptions_register.md A15.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import torch

from dqc.experiment import run_trace
from dqc.metrics import fairness, makespan, non_local_gate_rate, qpu_utilization, selp
from dqc.network import build_heterogeneous_link_weight
from dqc.rl.network import ActorCritic
from dqc.rl.ppo_scheduler import PPOScheduler
from dqc.schedulers.asap import ASAPScheduler
from dqc.schedulers.epr import EPRNodeSelectionScheduler, EPRScheduler
from dqc.schedulers.fifo import FIFOScheduler
from dqc.schedulers.list_scheduler import ListScheduler
from dqc.schedulers.milp import MILPScheduler
from dqc.schedulers.resource_priority import ResourcePriorityScheduler
from dqc.workload import build_job_catalogue, generate_trace

N_QPUS = 10
QPU_IDS = [f"node{i}" for i in range(N_QPUS)]
SLOT_DURATION_NS = 1.5e10
N_SLOTS = int(sys.argv[1]) if len(sys.argv) > 1 else 30  # paper uses 1000
SEED = 7
CONDITIONS = [(5, 0.0), (5, 0.5), (10, 0.0), (10, 0.5)]

ROOT = Path(__file__).resolve().parent.parent


def load_ppo(lam: int) -> ActorCritic:
    network = ActorCritic()
    path = ROOT / "results" / "checkpoints" / f"ppo_weights_{lam}.pth"
    network.load_state_dict(torch.load(path))
    network.eval()
    return network


def build_schedulers(lam: int):
    ppo_network = load_ppo(lam)
    return {
        "FIFO": (FIFOScheduler(), False),
        "LIST": (ListScheduler(), False),
        "Resource-Priority": (ResourcePriorityScheduler(), False),
        "EPR": (EPRScheduler(), False),
        "EPR (Node Selection)": (EPRNodeSelectionScheduler(), False),
        "MILP": (MILPScheduler(), False),
        f"PPO (Node Selection, trained lambda={lam})": (PPOScheduler(ppo_network, deterministic=True), False),
        "ASAP": (ASAPScheduler(), True),
    }


def main():
    catalogue = build_job_catalogue(n_qpu_network=N_QPUS)
    link_weight = build_heterogeneous_link_weight(QPU_IDS, seed=0)

    raw_dir = ROOT / "results" / "raw"
    summary_dir = ROOT / "results" / "summary"
    raw_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    for lam, tau in CONDITIONS:
        trace = generate_trace(seed=SEED, n_slots=N_SLOTS, lam=lam, tau=tau, catalogue=catalogue, n_qpu_network=N_QPUS)
        total_arrived = sum(len(s) for s in trace.arrivals_by_slot)
        condition = f"lambda={lam}_tau={tau}"
        print(f"\n=== condition {condition}: {total_arrived} jobs arrived ===", flush=True)

        for name, (scheduler, reinvoke) in build_schedulers(lam).items():
            t0 = time.perf_counter()
            records = run_trace(scheduler, trace, QPU_IDS, SLOT_DURATION_NS,
                                 reinvoke_on_release=reinvoke, link_weight=link_weight)
            dt = time.perf_counter() - t0
            df = pd.DataFrame([r.__dict__ for r in records])
            safe = name.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").replace("=", "")
            df.to_csv(raw_dir / f"matrix_{condition}_{safe}.csv", index=False)

            starts, finishes = df["start_time_ns"].tolist(), df["completion_time_ns"].tolist()
            exec_times, qpu_demands = df["exec_time_ns"].tolist(), df["qpu_demand"].tolist()
            latencies = (df["completion_time_ns"] - df["arrival_time_ns"]).tolist()
            m = makespan(starts, finishes)

            all_rows.append({
                "lambda": lam, "tau": tau, "scheduler": name, "n_jobs": len(df), "n_arrived": total_arrived,
                "makespan_ns": m,
                "qpu_utilization": qpu_utilization(exec_times, qpu_demands, m, N_QPUS),
                "non_local_gate_rate": non_local_gate_rate(starts, finishes),
                "selp": selp(exec_times, latencies),
                "fairness": fairness(exec_times, latencies),
                "wall_clock_s": dt,
            })
            print(f"  {name}: {len(df)}/{total_arrived} jobs, makespan={m/1e9:.1f}s, wall_clock={dt:.1f}s", flush=True)

    summary = pd.DataFrame(all_rows)
    summary.to_csv(summary_dir / "matrix_experiment_summary.csv", index=False)
    print("\n" + summary.to_string(index=False))


if __name__ == "__main__":
    main()
