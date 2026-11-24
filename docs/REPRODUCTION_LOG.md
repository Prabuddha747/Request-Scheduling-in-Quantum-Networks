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

## 2026-11-24 — Phase 2 + Phase 3 (partial)

**Action:** Freed disk space (4.3GB -> 9.8GB) by deleting regenerable caches and already-installed `.dmg` installers — user-approved.

**Action:** `git init`, default branch renamed to `main`. Added `vendor/netsquid` as a submodule pinned to `v1.0.1`; confirmed SHA matches the Phase 0 audit (`fece16a66507520a976dea31038e2e6754fbab88`). Created project directory structure, 4 scenario config YAMLs (parameters cross-checked against actual source, not assumed from the paper — see each config's comments for the script it maps to). Added `README.md`, `LICENSE`, `CITATION.cff`, `.gitignore`. Committed as `7feeda2`.

**Action:** Started Docker Desktop, pulled `python:3.7-slim-buster` under `linux/amd64` emulation, confirmed `Python 3.7.17 x86_64` runs.

**Finding:** `pydynaa==0.3.3` (NetSquid's discrete-event engine dependency) is **not on public PyPI** either (only an unrelated `0.0.1` exists there) — both `netsquid` and `pydynaa` require the gated `pypi.netsquid.org` index.

**Finding:** `apt-get update` failed inside `python:3.7-slim-buster` — Debian Buster's repos are archived; fixed by pointing `/etc/apt/sources.list` at `archive.debian.org`.

**Finding:** `cysignals==1.10.2` fails to build a wheel (a modern Cython pulled in during its isolated build triggers a `noexcept`-syntax incompatibility with the package's old `.pyx` sources) but succeeds via the `setup.py install` fallback — functionally fine, not something to "fix" by changing the pin.

**Result:** Built and verified `qnr-repro:py3.7` Docker image — the full non-gated pinned stack (numpy 1.19.2, scipy 1.5.3, pandas 1.1.3, matplotlib 3.3.2, cysignals 1.10.2, etc.) installs and imports successfully. `netsquid`/`pydynaa` deliberately deferred to a runtime-only install step (`scripts/install_netsquid.sh`) so credentials never enter an image layer or git history.

**Blocked:** `pypi.netsquid.org` times out at the TCP level from this sandboxed environment (DNS resolves correctly to `131.180.205.205`, port 443 connect times out) — tested both from the host shell and from inside a Docker container, same result, while GitHub/PyPI work fine from both. This needs to be checked from the user's own regular browser/terminal before the NetSquid-gated install step can be attempted. No simulator code has run yet.

## 2026-11-24 — netsquid.org reachability re-check (confirmed outage) + Phase 4 (partial)

**Action:** Re-ran DNS/TCP/HTTP checks against `netsquid.org`/`pypi.netsquid.org` from multiple angles (port 443, port 80, verbose curl). Identical silent-drop timeout every time.

**Action:** Asked the user to check `https://netsquid.org` directly in their own browser. **Confirmed: it does not load for them either.** This rules out a sandbox-specific block — it's a real outage or access issue on the NetSquid side, outside anyone's control here. No further diagnosis possible from this environment; revisit later.

**Action (unblocked work while waiting):** Checked which of the 4 upstream `uiiit` unit test files (`test_stat.py`, `test_topology.py`, `test_utils.py`, `test_traffic.py`) import `netsquid`/`pydynaa` directly — none do. Ran `python -m unittest` for all of them inside `qnr-repro:py3.7`.

**Result: all 80 upstream unit tests pass.** This validates the non-gated portion of the Docker environment (Python 3.7, numpy/scipy/pandas/cysignals stack, `uiiit`'s parallel-runner/traffic/stat/topology modules) end-to-end, independent of the NetSquid outage. The remaining Phase 3/4 gate (`import netsquid`, `minimal.py`, any test file that does import netsquid) stays blocked until the service is reachable.
