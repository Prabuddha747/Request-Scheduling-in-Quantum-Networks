import unittest

from qnr_repro.validation import validate_scenario_config, require_metric, ConfigError
from qnr_repro.result_io import Conf, Stat


class TestValidation(unittest.TestCase):
    def test_valid_config_passes(self):
        cfg = {"scenario_id": "paper_grid_regular", "timeslots": 10000, "fidelity_thresholds": [0, 0.9]}
        self.assertEqual(validate_scenario_config(cfg), cfg)

    def test_missing_scenario_id_rejected(self):
        with self.assertRaises(ConfigError):
            validate_scenario_config({"timeslots": 100})

    def test_out_of_range_fidelity_threshold_rejected(self):
        with self.assertRaises(ConfigError):
            validate_scenario_config({"scenario_id": "x", "fidelity_thresholds": [1.5]})

    def test_non_positive_timeslots_rejected(self):
        with self.assertRaises(ConfigError):
            validate_scenario_config({"scenario_id": "x", "timeslots": 0})

    def test_require_metric_present(self):
        stat = Stat(Conf())
        stat.count("degree-max", 4)
        self.assertIs(require_metric(stat, "degree-max"), stat)

    def test_require_metric_missing_raises_not_defaults_to_zero(self):
        stat = Stat(Conf())
        with self.assertRaises(KeyError):
            require_metric(stat, "degree-max")


if __name__ == "__main__":
    unittest.main()
