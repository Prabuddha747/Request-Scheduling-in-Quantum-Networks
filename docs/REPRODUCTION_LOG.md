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

## 2026-11-24 — Offline development phase (Phases 3/4/8/9 scaffolding that doesn't need netsquid)

**Action:** Re-verified netsquid.org/pypi.netsquid.org are still unreachable (TCP timeout on both port 443 and 80, DNS resolves fine) — consistent with the earlier confirmed outage, no change.

**Finding (resolves a prior open question):** Read `graphs/grid-success.plt`'s actual gnuplot plot command — `$2/$1*0.995e-4` — which shows `cardinality` (the `--factor cardinality` export column) doubles as the offered-load (1/λ) axis for the multipath grid/disc scripts, normalized by `1/timeslots`. Documented in `docs/SOURCE_CODE_AUDIT.md`; the exact `0.995` vs `1.0` constant is deferred to Phase 8 when real data exists to check against.

**Action:** Confirmed `uiiit.simstat` (upstream's own `Stat`/`MultiStat`/`Conf` classes, including their JSON schema and their `statsmodels`-based 95% CI calculation) imports and runs with zero `netsquid`/`pydynaa` dependency.

**Built (`src/qnr_repro/`), all without importing netsquid:**
- `manifests.py` — `RunManifest` dataclass (run_id, scenario, params, seed, repo_sha, env, status lifecycle incl. a `blocked` state for exactly this kind of outage), JSON save/load.
- `result_io.py` — thin wrapper around `uiiit.simstat.MultiStat`/`Stat`, reusing upstream's own JSON parsing and CI math rather than reimplementing either (the PRD forbids altering metric definitions).
- `metrics.py` — `normalized_entanglement_rate` (formula taken from the gnuplot script above), `average_fidelity_ci`, `average_swaps`.
- `validation.py` — scenario-config validation (raises on missing/out-of-range values) and `require_metric` (raises on a missing metric instead of silently returning 0, per the PRD's missing-data rule).
- `paper_figures.py` — two generic reusable plot shapes (x-y with 95% CI error bars; distribution boxplot) that structurally cover all of Figs. 11-20, each requiring label/units/sample-size arguments. Self-check uses data explicitly labeled "SYNTHETIC FIXTURE".

**Tests:** `tests/test_{manifest,result_io,metrics,validation}.py` — 18 tests, all pass inside `qnr-repro:py3.7`.

**Action:** Added `scripts/check_netsquid_access.sh` (one-shot reachability check, no retries, no credential output) and `docs/NETSQUID_ACCESS_STATUS.md` logging the current (still unreachable) status.

**Resource note:** Pruned Docker's dangling build cache (freed ~200MB). Disk currently 6.9GB free (down from the 9.8GB after the earlier cleanup, due to the `qnr-repro:py3.7` image + base layers, ~1GB total) — still healthy, rechecked per the PRD's resource policy rather than assumed.

**No simulation has run. No fabricated results were created anywhere in this entry** — the figure-generation self-check explicitly labels its fixture data as synthetic in both the title string and an assertion.

## 2026-11-24 — Revised strategy: analysis of authors' published reference archives

**Action:** Confirmed `vendor/netsquid` submodule already present (steps 1-2 of the revised plan were already done in Phase 2). Checked reachability of both archive URLs from the experiment README — both resolved (via a 301 to `https://turig.iit.cnr.it/...`), `HEAD` content-lengths matched the README's documented 272MB/313MB.

**Action:** Downloaded both archives into `artifacts/reference/`. **MD5 verified exact match** against the README's recorded checksums for both (`208815839ff...` and `754d5db3b2...`).

**Action:** Inspected `tar -tzvf` listings (uncompressed size sums, ~1GB each) *before* extracting, to estimate disk needs. Extracted one at a time, checking `df -h .` after each: disk went 8.1GB → 6.5GB (after raw JSON) → 4.4GB (after results — 266,592 tiny files caused ~1.8GB on-disk for ~1.0GB of actual content, APFS block overhead). Deleted the now-redundant compressed `.tgz` files post-verification to reclaim ~585MB, landing at ~4.9GB free. Added `artifacts/reference/` to `.gitignore`.

**Finding:** Memory was genuinely tight during this work (`vm_stat` showed ~70MB literally free pages at one point). Deliberately did **not** `json.load()` `first_disc.json` (747MB) in Python — too risky on this machine. Used `jq` (writing to disk, not stdout) for the two 147MB files, which worked fine. Derived `first_disc.json`'s structure analytically from the pinned source's loop parameters instead, cross-checked against the processed `results-disc/` filenames (which encode every (algorithm, cardinality, dephase_rate, seed) combination and are cheap to glob).

**Finding (real discrepancy, documented not resolved):** `first_grid.json`'s 9 entries span 3 distinct `algorithm` values (`spf-hops`, `minmax-dist`, **`spf-dist`**) — but the pinned `v1.0.1` source's `first_grid.py` only lists `["spf-hops", "minmax-dist"]`. `first_gridmp.json`/`first_gridmpvar.json` showed no such mismatch (both matched the pinned source's 4-policy `algos` list exactly). See `docs/REFERENCE_DATA_AUDIT.md`.

**Action:** Added `load_dat_count`/`load_dat_points` to `result_io.py`, matching `uiiit.simstat.Stat.export()`'s exact text format (confirmed by reading the source before writing the parser). Built `scripts/analyze_reference_data.py` using the existing `result_io`/`metrics`/`paper_figures` modules against the real archived data (no new scenario-specific plotting code — reused the generic framework from the earlier offline phase).

**Result:** Generated 5 real figures from actual author-provided data in `artifacts/figures/reference/`, each explicitly titled "Author-provided reference data ... NOT an independently executed NetSquid simulation": calibration (fidelity vs. chain distance, 3 noise combos — shows expected physical degradation with distance/dephasing), regular + irregular grid (normalized rate and fidelity vs. offered load, all 4 scheduling policies — rate drops under load as expected, fidelity stays roughly flat since it depends on link quality not congestion), irregular-grid average swaps vs. offered load, and a degree distribution across 192/200 disc replications (8 presumably discarded as disconnected topologies, consistent with the paper's model — not fabricated to hit exactly 200). All visually inspected and sane before accepting.

**Deferred:** Figs. 16-20 need a larger per-seed aggregation over `results-disc/`'s 265,824 files. Not attempted in this session given disk had dropped to **~3.9GB free (99% full)** by this point — flagged clearly in `docs/SESSION_HANDOFF.md` rather than pushed through.

**This entire session's output is reference-data analysis, not a NetSquid reproduction claim** — NetSquid itself remains uninstalled.
