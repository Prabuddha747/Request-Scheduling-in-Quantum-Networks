import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from qnr_repro.manifests import RunManifest


class TestRunManifest(unittest.TestCase):
    def test_lifecycle_and_roundtrip(self):
        m = RunManifest(
            run_id="r1", scenario_id="smoke_test", config_file="configs/smoke_test.yaml",
            parameters={"timeslots": 100}, seed=42, repo_sha="fece16a",
        )
        self.assertEqual(m.status, "pending")
        m.mark_started()
        self.assertEqual(m.status, "running")
        self.assertIsNotNone(m.start_time)
        m.mark_finished(0, output_files=["out.json"])
        self.assertEqual(m.status, "completed")
        self.assertEqual(m.output_files, ["out.json"])

        with TemporaryDirectory() as d:
            path = Path(d) / "manifest.json"
            m.save(path)
            loaded = RunManifest.load(path)
            self.assertEqual(loaded.run_id, "r1")
            self.assertEqual(loaded.status, "completed")
            self.assertEqual(json.loads(path.read_text())["seed"], 42)

    def test_failed_run_status(self):
        m = RunManifest(run_id="r2", scenario_id="x", config_file="c.yaml", parameters={})
        m.mark_finished(exit_code=1)
        self.assertEqual(m.status, "failed")

    def test_blocked_status_records_reason(self):
        m = RunManifest(run_id="r3", scenario_id="x", config_file="c.yaml", parameters={})
        m.mark_blocked("netsquid.org unreachable")
        self.assertEqual(m.status, "blocked")
        self.assertIn("netsquid.org unreachable", m.deviations)

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            RunManifest(
                run_id="r4", scenario_id="x", config_file="c.yaml", parameters={},
                status="bogus",
            )


if __name__ == "__main__":
    unittest.main()
