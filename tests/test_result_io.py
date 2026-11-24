import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from qnr_repro.result_io import load_raw_results, Conf


class TestResultIO(unittest.TestCase):
    """Fixture matches upstream's own MultiStat.json_dump schema exactly
    (see uiiit/simstat.py Stat.content_dump) -- synthetic values, not a
    real simulation output."""

    FIXTURE = [
        {
            "conf": {"topology": "grid", "cardinality": 2, "algorithm": "spf-hops"},
            "points": {"fidelity-2": [0.9, 0.8], "meas": [2, 1]},
            "counts": {"success-0.0": [3, 1], "lenrate-2": [3, 1]},
        }
    ]

    def test_load_roundtrip(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "first_grid.json"
            path.write_text(json.dumps(self.FIXTURE))
            mstat = load_raw_results(path)
            self.assertEqual(len(mstat), 1)
            conf = Conf(topology="grid", cardinality=2, algorithm="spf-hops")
            stat = mstat[conf]
            self.assertEqual(stat.get_sum("success-0.0"), 3)
            self.assertAlmostEqual(stat.get_avg("fidelity-2"), 0.85)

    def test_missing_file_returns_empty(self):
        mstat = load_raw_results("/nonexistent/path/does-not-exist.json")
        self.assertEqual(len(mstat), 0)


if __name__ == "__main__":
    unittest.main()
