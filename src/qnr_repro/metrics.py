"""Paper-aligned metric calculations on top of a `uiiit.simstat.Stat` object.

Every formula here is taken directly from upstream's own source (the `graphs/*.plt`
scripts and `uiiit/simstat.py`), not invented -- see docs/SOURCE_CODE_AUDIT.md for the
exact derivation of each one. Confidence intervals reuse `Stat.get_avg_ci` (statsmodels
tconfint_mean), not a reimplementation.
"""
from .result_io import Stat  # result_io does the vendor/netsquid sys.path setup


def normalized_entanglement_rate(stat: Stat, fidelity_threshold: float, cardinality: int, timeslots: int) -> float:
    """established paths with fidelity > threshold, normalized by offered load * slots.

    Matches graphs/grid-success.plt: `$2/$1*0.995e-4` where $1 is the `--factor
    cardinality` value (== offered load 1/lambda for the multipath scripts) and
    0.995e-4 ~= 1/timeslots for the grid scenario's 10,000 slots. Passing the exact
    `cardinality`/`timeslots` used for the run instead of hardcoding upstream's
    grid-specific constants keeps this correct for other scenarios too.
    """
    metric = f"success-{fidelity_threshold:.1f}"
    established = stat.get_sum(metric) if metric in stat else 0
    denominator = cardinality * timeslots
    if denominator == 0:
        raise ValueError("cardinality * timeslots must be > 0")
    return established / denominator


def average_fidelity_ci(stat: Stat, hops: int):
    """(mean, half-width) 95% CI for fidelity-<hops>, or (0, 0) if no data."""
    metric = f"fidelity-{hops}"
    if metric not in stat:
        return (0.0, 0.0)
    return stat.get_avg_ci(metric)


def average_swaps(stat: Stat):
    """mean + 95% CI for Bell measurements/swaps per established path ('meas')."""
    if "meas" not in stat:
        return (0.0, 0.0)
    return stat.get_avg_ci("meas")
