#!/usr/bin/env python3
"""Generates figures from the AUTHORS' OWN PUBLISHED RESULT ARCHIVES
(artifacts/reference/, downloaded from the experiment README's links, MD5-verified
against docs/REFERENCE_DATA_AUDIT.md). This is analysis of author-provided results,
NOT output from an independently executed NetSquid simulation -- NetSquid itself
remains uninstalled (see docs/NETSQUID_ACCESS_STATUS.md). Every figure says so.

Run inside the project's Docker image (no netsquid import needed):
    docker run --rm -e PYTHONPATH=/workspace/src -v "$PWD":/workspace -w /workspace \
        qnr-repro:py3.7 python3 scripts/analyze_reference_data.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib.pyplot as plt  # noqa: E402

from qnr_repro.result_io import load_raw_results  # noqa: E402
from qnr_repro.metrics import normalized_entanglement_rate, average_fidelity_ci, average_swaps  # noqa: E402

REFERENCE_LABEL = (
    "Author-provided reference data (ccicconetti/netsquid v1.0.1 archives) -- "
    "NOT an independently executed NetSquid simulation"
)

ROOT = Path(__file__).resolve().parents[1]
RAW_JSON = ROOT / "artifacts" / "reference" / "raw-json"
RESULTS = ROOT / "artifacts" / "reference" / "results"
OUT = ROOT / "artifacts" / "figures" / "reference"
OUT.mkdir(parents=True, exist_ok=True)

GRID_TIMESLOTS = 10000  # from first_gridmp.py / SOURCE_CODE_AUDIT.md


def fig_grid_policy_comparison(json_path: Path, title_suffix: str, out_name: str):
    """Figs. 12-13 shape: normalized rate & fidelity vs offered load (cardinality), by policy."""
    mstat = load_raw_results(json_path)
    if mstat.empty():
        print(f"SKIP {out_name}: {json_path} not found/empty")
        return

    policies = ["spf-hops", "minmax", "always-skip", "random-skip"]
    cardinalities = sorted(mstat.param_values("cardinality"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    for policy in policies:
        rates, fids = [], []
        for card in cardinalities:
            stats = mstat.get_stats(algorithm=policy, cardinality=card)
            if not stats:
                rates.append(0.0)
                fids.append(0.0)
                continue
            stat = stats[0]
            rates.append(normalized_entanglement_rate(stat, 0.0, card, GRID_TIMESLOTS))
            mean, _ = average_fidelity_ci(stat, hops=2)
            fids.append(mean)
        ax1.plot(cardinalities, rates, marker="o", label=policy)
        ax2.plot(cardinalities, fids, marker="o", label=policy)

    ax1.set_xlabel("1/lambda (offered load, via cardinality)")
    ax1.set_ylabel("Normalized entanglement rate (any fidelity)")
    ax1.set_title(f"{title_suffix} - rate\n{REFERENCE_LABEL}", fontsize=8)
    ax1.legend(fontsize=7)
    ax2.set_xlabel("1/lambda (offered load, via cardinality)")
    ax2.set_ylabel("Average fidelity (2-hop paths)")
    ax2.set_title(f"{title_suffix} - fidelity\n{REFERENCE_LABEL}", fontsize=8)
    ax2.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / out_name, dpi=120)
    plt.close(fig)
    print(f"wrote {OUT / out_name}")


def fig_irregular_grid_swaps(json_path: Path, out_name: str):
    """Fig. 14 shape: average swaps vs offered load, by policy (irregular grid)."""
    mstat = load_raw_results(json_path)
    if mstat.empty():
        print(f"SKIP {out_name}: {json_path} not found/empty")
        return

    policies = ["spf-hops", "minmax", "always-skip", "random-skip"]
    cardinalities = sorted(mstat.param_values("cardinality"))

    fig, ax = plt.subplots(figsize=(6, 4))
    for policy in policies:
        swaps = []
        for card in cardinalities:
            stats = mstat.get_stats(algorithm=policy, cardinality=card)
            mean, _ = average_swaps(stats[0]) if stats else (0.0, 0.0)
            swaps.append(mean)
        ax.plot(cardinalities, swaps, marker="o", label=policy)

    ax.set_xlabel("1/lambda (offered load, via cardinality)")
    ax.set_ylabel("Average swaps per established path")
    ax.set_title(f"Irregular grid - avg swaps\n{REFERENCE_LABEL}", fontsize=8)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / out_name, dpi=120)
    plt.close(fig)
    print(f"wrote {OUT / out_name}")


def fig_calibration(json_path: Path, out_name: str):
    """Fig. 11 shape: fidelity vs chain link distance, for the depol/dephase combos present."""
    mstat = load_raw_results(json_path)
    if mstat.empty():
        print(f"SKIP {out_name}: {json_path} not found/empty")
        return

    depol_values = sorted(mstat.param_values("depol_rate"))
    dephase_values = sorted(mstat.param_values("dephase_rate"))

    fig, ax = plt.subplots(figsize=(6, 4))
    for depol in depol_values[:1]:  # one representative combo -- avoid an unreadable 2x3 legend
        for dephase in dephase_values:
            stats = mstat.get_stats(
                topology="chain", num_nodes=3, depol_rate=depol, dephase_rate=dephase
            )
            points = []
            for s in stats:
                fidelity_metrics = [m for m in s.point_metrics() if m.startswith("fidelity-")]
                if not fidelity_metrics:
                    continue
                # a 3-node chain always has one hop count for the farthest pair -- take it as-is
                hops = int(fidelity_metrics[0].split("-")[1])
                points.append((s.conf()["node_distance"], average_fidelity_ci(s, hops=hops)[0]))
            if not points:
                continue
            points.sort()
            xs, ys = zip(*points)
            ax.plot(xs, ys, marker="o", label=f"depol={depol:.0f}Hz dephase={dephase:.0f}Hz")

    ax.set_xlabel("Node distance (km)")
    ax.set_ylabel("Average fidelity (2-hop, 3-node chain)")
    ax.set_title(f"Calibration\n{REFERENCE_LABEL}", fontsize=8)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / out_name, dpi=120)
    plt.close(fig)
    print(f"wrote {OUT / out_name}")


def fig_disc_degree_distribution(results_dir: Path, out_name: str, algorithm="spf-hops", cardinality=1, dephase_rate=100000.0):
    """Fig. 15 shape: min/avg/max logical degree distribution across the 200 disc replications.

    Reads the small per-seed .dat files one at a time (never loads the whole
    265k-file results-disc/ tree at once) -- matches the project's incremental-
    processing / RAM policy.
    """
    prefix = f"algorithm={algorithm}.cardinality={cardinality}.dephase_rate={dephase_rate}.seed="
    degree_min, degree_avg, degree_max = [], [], []
    for path in sorted(results_dir.glob(f"{prefix}*.degree-min.dat")):
        seed_tag = path.name[len(prefix):-len(".degree-min.dat")]
        avg_path = results_dir / f"{prefix}{seed_tag}.degree-avg.dat"
        max_path = results_dir / f"{prefix}{seed_tag}.degree-max.dat"
        if not (avg_path.exists() and max_path.exists()):
            continue
        degree_min.append(_count_value(path))
        degree_avg.append(_count_value(avg_path))
        degree_max.append(_count_value(max_path))

    if not degree_min:
        print(f"SKIP {out_name}: no matching files for prefix {prefix!r}")
        return

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot(
        [degree_min, degree_avg, degree_max],
        labels=[f"min (n={len(degree_min)})", f"avg (n={len(degree_avg)})", f"max (n={len(degree_max)})"],
    )
    ax.set_ylabel("Logical node degree")
    ax.set_title(f"Random/disc degree distribution\n{algorithm}, cardinality={cardinality}\n{REFERENCE_LABEL}", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / out_name, dpi=120)
    plt.close(fig)
    print(f"wrote {OUT / out_name} (n={len(degree_min)} replications)")


def _count_value(path: Path) -> float:
    from qnr_repro.result_io import load_dat_count
    total, count = load_dat_count(path)
    return total / count if count else 0.0


if __name__ == "__main__":
    fig_calibration(RAW_JSON / "first_calibration.json", "REFERENCE_fig11_calibration.png")
    fig_grid_policy_comparison(
        RAW_JSON / "first_gridmp.json", "Regular grid, 25 nodes", "REFERENCE_fig12_13_grid_regular.png"
    )
    fig_grid_policy_comparison(
        RAW_JSON / "first_gridmpvar.json", "Irregular grid, 25 nodes", "REFERENCE_fig12_13_grid_irregular.png"
    )
    fig_irregular_grid_swaps(RAW_JSON / "first_gridmpvar.json", "REFERENCE_fig14_irregular_grid_swaps.png")
    fig_disc_degree_distribution(RESULTS / "results-disc", "REFERENCE_fig15_disc_degree_distribution.png")
    print("Done. All outputs are analysis of author-provided reference data, not simulation runs.")
