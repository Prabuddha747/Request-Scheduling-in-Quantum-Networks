import unittest

from qnr_repro.metrics import normalized_entanglement_rate, average_fidelity_ci, average_swaps
from qnr_repro.result_io import Conf, Stat


def make_stat(**counts_and_points):
    stat = Stat(Conf(topology="grid"))
    for k, v in counts_and_points.items():
        if isinstance(v, list):
            for item in v:
                stat.add(k, item)
        else:
            stat.count(k, v)
    return stat


class TestMetrics(unittest.TestCase):
    def test_normalized_rate(self):
        stat = make_stat(**{"success-0.9": 50})
        rate = normalized_entanglement_rate(stat, fidelity_threshold=0.9, cardinality=5, timeslots=10000)
        self.assertAlmostEqual(rate, 50 / 50000)

    def test_normalized_rate_missing_metric_is_zero_not_error(self):
        stat = make_stat()
        rate = normalized_entanglement_rate(stat, fidelity_threshold=0.9, cardinality=5, timeslots=10000)
        self.assertEqual(rate, 0.0)

    def test_normalized_rate_rejects_zero_denominator(self):
        stat = make_stat(**{"success-0.9": 1})
        with self.assertRaises(ValueError):
            normalized_entanglement_rate(stat, fidelity_threshold=0.9, cardinality=0, timeslots=10000)

    def test_average_fidelity_ci_with_data(self):
        stat = make_stat(**{"fidelity-2": [0.8, 0.9, 0.85]})
        mean, halfwidth = average_fidelity_ci(stat, hops=2)
        self.assertAlmostEqual(mean, 0.85, places=2)
        self.assertGreaterEqual(halfwidth, 0)

    def test_average_fidelity_ci_missing_metric(self):
        stat = make_stat()
        self.assertEqual(average_fidelity_ci(stat, hops=2), (0.0, 0.0))

    def test_average_swaps_missing_metric(self):
        stat = make_stat()
        self.assertEqual(average_swaps(stat), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
