# Reproduction Log

## 2026-11-24 — Phase 0 + Phase 1

**Action:** Read `01_PRD`, `02_Implementation_Plan`, `03_TRD` PDFs in full. Confirmed research paper PDF (`Request_Scheduling_in_Quantum_Networks.pdf`) is present in `docs/`.

**Action:** Shallow-cloned `https://github.com/ccicconetti/netsquid` at tag `v1.0.1` into the scratchpad (`/private/tmp/.../scratchpad/netsquid-audit`) for read-only inspection. Not vendored into the project yet (that's Phase 2's job).

**Result:** Commit SHA for `v1.0.1` = `fece16a66507520a976dea31038e2e6754fbab88`. Repo is 732 KB, matches the PRD's described structure (`experiments/001-Scheduling-and-path-selection/`, `uiiit/`, `scripts/`).

**Finding:** `run_simulation.py` + `uiiit/oracle.py` confirm the Strict/Best/Random FIFO ↔ `skip_policy` (`none`/`always-skip`/`random-skip`) mapping exactly as described in the PRD.

**Finding (discrepancy):** `first_grid.py`'s `algos` list (`["spf-hops", "minmax-dist"]`) contains no skip-policy suffix, so it only ever runs Strict FIFO. The actual Strict/Best/Random FIFO comparison (Figs. 12–14) is produced by `first_gridmp.py` / `first_gridmpvar.py` at `cardinality=1`, which do have the full 4-entry `algos` list. Documented in `FIGURE_MAPPING.md` and `SOURCE_CODE_AUDIT.md` so later phases don't run the wrong script and call it a figure's source.

**Finding (discrepancy):** `run_all.sh` does not run `first_calibration.py` — calibration (Fig. 11) must be invoked and exported separately from the documented "run everything" path.

**Finding (resource concern):** `first_grid.py` hardcodes `nworkers = 50` for its parallel runner — must be overridden to a low value (ideally 1, per the PRD's RAM policy) for any actual run on this 8 GB machine; this is a deliberate execution-only deviation to record per-run in future manifests, not a scientific one.

**Finding (environment risk):** Upstream `requirements.txt` pins numpy 1.19.2 / scipy 1.5.3 / cysignals 1.10.2 / pydynaa 0.3.3 — all compiled extensions pinned to 2020-era versions, predating general Apple Silicon wheel availability. Native arm64 install is assessed as low-confidence; see `DEPENDENCY_AUDIT.md`.

**Finding (blocking, environment-independent):** Disk has only 4.3 GB free out of 228 GB (98% full). This blocks meaningful progress (Docker images, venvs, experiment output) regardless of which environment path is chosen.

**Finding (network):** `netsquid.org` and `pypi.netsquid.org` both timed out from this sandboxed shell; GitHub was reachable fine. Not yet attributable to sandbox restriction vs. actual outage — needs checking from the user's own terminal.

**No simulation has been run. No installation has been performed.** This entry covers documentation/audit work only, per the master prompt's instruction to stop after Phase 0/1 and report before touching the environment.
