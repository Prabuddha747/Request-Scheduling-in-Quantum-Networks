"""Reusable plotting for the paper's figures. Two generic shapes cover all of
Figs. 11-20 (PRD section 10): an x-y line/point plot with optional 95% CI error
bars (offered-load sweeps, calibration sweeps), and a distribution plot across
independent replications (degree/fidelity/delay distributions). Ten near-identical
per-figure functions would just be the same two shapes copy-pasted.

Labels/units/sample sizes are REQUIRED arguments, not optional kwargs with
defaults -- the PRD requires every figure to carry them, so a caller that forgets
one should get a TypeError, not a silently unlabeled plot.
"""
import os

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.pyplot as plt  # noqa: E402


def line_plot_with_ci(
    ax, x, y, yerr, *, xlabel: str, ylabel: str, title: str, label: str, sample_size: int
):
    """One series of an x-y plot with 95% CI error bars, paper-figure style."""
    ax.errorbar(x, y, yerr=yerr, marker="o", capsize=3, label=f"{label} (n={sample_size})")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    return ax


def distribution_plot(ax, samples, *, xlabel: str, title: str, label: str, sample_size: int):
    """Boxplot of a metric distributed across independent replications/topologies."""
    ax.boxplot(samples, labels=[f"{label} (n={sample_size})"])
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    return ax


def _demo():
    """Self-check with clearly-synthetic fixture data -- NOT research output."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
    x = [1, 2, 3, 4, 5]
    y = [0.9, 0.7, 0.5, 0.3, 0.1]
    yerr = [0.02] * 5
    line_plot_with_ci(
        ax1, x, y, yerr,
        xlabel="1/lambda", ylabel="Normalized entanglement rate",
        title="SYNTHETIC FIXTURE - not a research result", label="strict_fifo", sample_size=200,
    )
    distribution_plot(
        ax2, [2, 3, 3, 4, 2, 5],
        xlabel="degree", title="SYNTHETIC FIXTURE - not a research result",
        label="avg_degree", sample_size=6,
    )
    assert ax1.get_legend() is not None
    assert ax1.get_title().startswith("SYNTHETIC")
    plt.close(fig)
    print("paper_figures self-check OK (synthetic fixture only)")


if __name__ == "__main__":
    _demo()
