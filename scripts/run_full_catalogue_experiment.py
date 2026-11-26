"""Phase 7: full 30-template catalogue experiment (the real paper job set,
not the 5/7-qubit smoke subset) across all 8 schedulers on one shared
trace, using the actually-trained PPO (lambda=5) checkpoint. Still NOT the
full 1000-slot matrix -- see docs/assumptions_register.md A12/A14.
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

N_QPUS = 10
QPU_IDS = [f"node{i}" for i in range(N_QPUS)]  # matches o.log's node0..node9 naming
SLOT_DURATION_NS = 1.5e10  # generous vs. the catalogue's largest job (~7e9ns, qft_15)
N_SLOTS = 10
LAM = 5  # matches the trained ppo_weights_5.pth checkpoint
SEED = 7

ROOT = Path(__file__).resolve().parent.parent


def link_weight_table():
    params = LINK_QUALITIES["Medium"]
    p_s = entanglement_success_probability(params)
    t_state = state_delay_ns(T_CYCLE_NS["Medium"], p_s)
    return {(a, b): t_state for a in QPU_IDS for b in QPU_IDS if a < b}


def main():
    catalogue = build_job_catalogue(n_qpu_network=N_QPUS)
    trace = generate_trace(seed=SEED, n_slots=N_SLOTS, lam=LAM, tau=0, catalogue=catalogue, n_qpu_network=N_QPUS)
    link_weight = link_weight_table()
    total_arrived = sum(len(s) for s in trace.arrivals_by_slot)
    print(f"trace: {total_arrived} jobs arrived across {N_SLOTS} slots (lambda={LAM})")

    ppo_network = ActorCritic()
    ppo_network.load_state_dict(torch.load(ROOT / "results" / "checkpoints" / "ppo_weights_5.pth"))
    ppo_network.eval()

    schedulers = {
        "FIFO": (FIFOScheduler(), False),
        "LIST": (ListScheduler(), False),
        "Resource-Priority": (ResourcePriorityScheduler(), False),
        "EPR": (EPRScheduler(), False),
        "EPR (Node Selection)": (EPRNodeSelectionScheduler(), False),
        "MILP": (MILPScheduler(), False),  # auto-scaled, see A8 fix
        "PPO (Node Selection, trained lambda=5)": (PPOScheduler(ppo_network, deterministic=True), False),
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
        safe_name = name.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "").replace("=", "")
        df.to_csv(raw_dir / f"fullcat_{safe_name}.csv", index=False)

        starts, finishes = df["start_time_ns"].tolist(), df["completion_time_ns"].tolist()
        exec_times, qpu_demands = df["exec_time_ns"].tolist(), df["qpu_demand"].tolist()
        latencies = (df["completion_time_ns"] - df["arrival_time_ns"]).tolist()
        m = makespan(starts, finishes)

        summary_rows.append({
            "scheduler": name, "n_jobs": len(df), "n_arrived": total_arrived,
            "makespan_ns": m,
            "qpu_utilization": qpu_utilization(exec_times, qpu_demands, m, N_QPUS),
            "non_local_gate_rate": non_local_gate_rate(starts, finishes),
            "selp": selp(exec_times, latencies),
            "fairness": fairness(exec_times, latencies),
        })
        print(f"{name}: {len(df)}/{total_arrived} jobs scheduled, makespan={m/1e9:.2f}s")

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(summary_dir / "fullcatalogue_experiment_summary.csv", index=False)
    print("\n" + summary.to_string(index=False))
    print(f"\nconfig: seed={SEED} slots={N_SLOTS} qpus={N_QPUS} lambda={LAM} tau=0 "
          f"full_30_template_catalogue slot_duration_ns={SLOT_DURATION_NS}")


if __name__ == "__main__":
    main()
