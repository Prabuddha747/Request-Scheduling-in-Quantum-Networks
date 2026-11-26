"""Train PPO (Node Selection) for lambda=5 and lambda=10 (master prompt's
explicit priority order before expanding to lambda 4-15). Saves checkpoints,
per-update training logs (Figure F6 raw data), and wall-clock/peak-memory
diagnostics per model.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import torch

from dqc.rl.train import train

ROOT = Path(__file__).resolve().parent.parent
N_UPDATES = 100
N_QPU = 10


def main():
    results_dir = ROOT / "results" / "raw"
    checkpoints_dir = ROOT / "results" / "checkpoints"
    results_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    for lam in (5, 10):
        print(f"training PPO for lambda={lam} ({N_UPDATES} updates)...")
        result = train(lam=lam, n_updates=N_UPDATES, n_qpu=N_QPU, seed=0)

        log_df = pd.DataFrame([vars(l) for l in result.logs])
        log_df.to_csv(results_dir / f"ppo_training_lambda_{lam}.csv", index=False)
        torch.save(result.network.state_dict(), checkpoints_dir / f"ppo_weights_{lam}.pth")

        print(f"  lambda={lam}: wall_clock={result.total_wall_clock_s:.1f}s "
              f"peak_rss={result.peak_rss_mb:.1f}MB "
              f"final_mean_reward={result.logs[-1].mean_reward:.4f} "
              f"first_mean_reward={result.logs[0].mean_reward:.4f}")


if __name__ == "__main__":
    main()
