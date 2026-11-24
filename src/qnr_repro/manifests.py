"""Run manifests: one JSON file per experiment run, recording everything the
PRD/TRD require for reproducibility (repo SHA, env, seed, params, status).

Fields match docs/02_Implementation_Plan_Claude_Code.pdf section 6 exactly.
"""
import dataclasses
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

STATUSES = ("pending", "running", "completed", "failed", "blocked")


@dataclasses.dataclass
class RunManifest:
    run_id: str
    scenario_id: str
    config_file: str
    parameters: Dict[str, Any]
    seed: Optional[int] = None
    replication: Optional[int] = None
    repo_sha: str = ""
    python_version: str = dataclasses.field(default_factory=platform.python_version)
    os_arch: str = dataclasses.field(
        default_factory=lambda: f"{platform.system()}/{platform.machine()}"
    )
    command: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    exit_code: Optional[int] = None
    output_files: List[str] = dataclasses.field(default_factory=list)
    deviations: List[str] = dataclasses.field(default_factory=list)
    status: str = "pending"

    def __post_init__(self):
        if self.status not in STATUSES:
            raise ValueError(f"invalid status {self.status!r}, must be one of {STATUSES}")

    def mark_started(self):
        self.status = "running"
        self.start_time = datetime.now(timezone.utc).isoformat()

    def mark_finished(self, exit_code: int, output_files: Optional[List[str]] = None):
        self.exit_code = exit_code
        self.end_time = datetime.now(timezone.utc).isoformat()
        self.status = "completed" if exit_code == 0 else "failed"
        if output_files:
            self.output_files.extend(output_files)

    def mark_blocked(self, reason: str):
        self.status = "blocked"
        self.deviations.append(reason)

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), indent=2, sort_keys=True)

    def save(self, path: Path):
        Path(path).write_text(self.to_json())

    @staticmethod
    def load(path: Path) -> "RunManifest":
        data = json.loads(Path(path).read_text())
        return RunManifest(**data)
