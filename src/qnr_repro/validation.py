"""Config and result validation. Operates on plain dicts (the configs/*.yaml files,
once parsed) -- no YAML parsing here, since nothing yet consumes a parsed config
(that wiring belongs to scripts/run_scenario.py in Phase 3, which needs netsquid
to actually run anything). Raising early beats silently defaulting, per the PRD's
"missing data does not silently become zero" rule.
"""
from .result_io import Stat

REQUIRED_SCENARIO_KEYS = ("scenario_id",)


class ConfigError(ValueError):
    pass


def validate_scenario_config(config: dict):
    """Raise ConfigError if a scenario config dict is missing required keys or
    has an out-of-range value. Returns the config unchanged if valid."""
    missing = [k for k in REQUIRED_SCENARIO_KEYS if k not in config]
    if missing:
        raise ConfigError(f"missing required keys: {missing}")

    for key in ("fidelity_thresholds",):
        for threshold in config.get(key, []):
            if not 0 <= threshold <= 1:
                raise ConfigError(f"{key} value {threshold} outside [0,1]")

    for key in ("timeslots", "replications"):
        if key in config and config[key] <= 0:
            raise ConfigError(f"{key} must be > 0, got {config[key]}")

    return config


def require_metric(stat: Stat, metric: str):
    """Raise instead of letting a missing metric silently read as 0/empty."""
    if metric not in stat:
        raise KeyError(f"metric {metric!r} not present in this Stat -- refusing to default to 0")
    return stat
