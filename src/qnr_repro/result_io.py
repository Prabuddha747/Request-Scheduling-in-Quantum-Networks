"""Reads upstream's own raw result format. Deliberately thin: `uiiit.simstat.MultiStat`
already parses the `{"conf": ..., "points": ..., "counts": ...}` JSON and already implements
the paper's 95% Student-t CI (`Stat.get_avg_ci`, via statsmodels) -- reimplementing either
would risk silently diverging from upstream's own metric definitions, which the PRD forbids.

Requires vendor/netsquid on sys.path (set via PYTHONPATH in the Dockerfile). Does NOT require
netsquid/pydynaa itself -- uiiit.simstat has no such import.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")  # headless: no display in a container/CI

_VENDOR_PATH = str(Path(__file__).resolve().parents[2] / "vendor" / "netsquid")
if _VENDOR_PATH not in sys.path:
    sys.path.insert(0, _VENDOR_PATH)

from uiiit.simstat import Conf, MultiStat, Stat  # noqa: E402  (path setup must come first)

__all__ = ["Conf", "MultiStat", "Stat", "load_raw_results"]


def load_raw_results(path) -> MultiStat:
    """Load a raw `first_*.json` result file produced by the upstream scripts.

    Returns an empty MultiStat if the file does not exist yet (e.g. the scenario
    hasn't been run) -- same behaviour as upstream's own json_load_from_file.
    """
    return MultiStat.json_load_from_file(str(path))


def load_dat_count(path) -> "tuple[float, int]":
    """(sum, count) from one of upstream's exported count-metric .dat files
    (format: 'sum count\\n', written by Stat.export())."""
    total, count = Path(path).read_text().split()
    return float(total), int(count)


def load_dat_points(path) -> list:
    """List of float values from an exported point-metric .dat file (one value/line)."""
    return [float(x) for x in Path(path).read_text().splitlines() if x.strip()]
