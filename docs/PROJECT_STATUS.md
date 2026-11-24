# Project Status

**Current phase:** Phase 0, 1, 2 complete. Phase 3 (environment), Phase 4 (tests) complete for
everything not requiring the NetSquid package index. **Revised strategy (this entry):** while
netsquid.org stays down, the project now also uses the authors' own published reference-result
archives (downloaded, MD5-verified, partially plotted) to make real progress on Phases 8-9 —
see `docs/REFERENCE_DATA_AUDIT.md`. This is explicitly *analysis of author-provided results*,
not a NetSquid reproduction; the eventual real reproduction (Phase 3 `minimal.py` onward) is
still fully blocked on the outage. Re-check with `./scripts/check_netsquid_access.sh`.

## Completed
- Confirmed all 4 docs present in `docs/` (3 PRD/Plan/TRD PDFs + the research paper PDF).
- Read PRD, Implementation Plan, TRD in full.
- Shallow-cloned `ccicconetti/netsquid` @ `v1.0.1` into scratchpad (not vendored into the project yet) and audited its actual structure, scripts, and parameters against the PRD/TRD.
- Resolved and recorded the pinned commit SHA: `fece16a66507520a976dea31038e2e6754fbab88`.
- Produced `SOURCE_CODE_AUDIT.md`, `FIGURE_MAPPING.md`, `DEPENDENCY_AUDIT.md`, `RESEARCH_METHODOLOGY.md`.
- Ran Mac/arch/Python/disk/RAM/network preflight checks (see `DEPENDENCY_AUDIT.md`).

## Pending
- **Confirmed blocked on a real netsquid.org outage**, not an environment/sandbox issue — user verified `https://netsquid.org` doesn't load in their own browser either. Nothing to do here but wait and retry periodically, or reach out to the NetSquid maintainers/forum if it stays down.
- Once reachable: register at the NetSquid forum, then `scripts/install_netsquid.sh` inside the container, then `minimal.py` smoke test (completes Phase 3) — exact commands in `docs/ENVIRONMENT_SETUP.md` / `docs/SESSION_HANDOFF.md`.
- Phases 5 onward (calibration, grid, random/disc, figures, final report) blocked on the above.

## Resolved
- **Disk space** — freed from 4.3 GB to 9.8 GB free by deleting regenerable app caches (`~/Library/Caches/Google`, partial `dotslash`) and 3 already-installed `.dmg` installers from Downloads. No project or user data touched.
- **Environment path decision** — Docker `linux/amd64`, Python 3.7, confirmed empirically rather than assumed: `python:3.7-slim-buster` runs fine under Apple Silicon emulation, and the full non-gated pinned scientific stack (numpy/scipy/pandas/matplotlib/cysignals) builds and imports successfully. Image tagged `qnr-repro:py3.7`. `netsquid`/`pydynaa` are confirmed to require the gated index (not on public PyPI) and are deliberately deferred to a runtime install step so credentials never enter the image or git history.
- **Project scaffolding (Phase 2)** — git repo initialized, `vendor/netsquid` submodule pinned at `v1.0.1` (SHA `fece16a66507520a976dea31038e2e6754fbab88`, matches audit), directory structure created, 4 scenario configs written with source-verified parameters, `README.md`/`LICENSE`/`CITATION.cff`/`Dockerfile`/`scripts/install_netsquid.sh` added. Committed as `7feeda2`.
- **Upstream unit tests (part of Phase 4)** — all 80 tests in `uiiit/test_{stat,topology,utils,traffic}.py` pass inside `qnr-repro:py3.7` (none of these 4 files import netsquid/pydynaa, so they're unblocked by the outage).
- **Offered-load wiring open question** (from the Phase 0 audit) — resolved by reading `graphs/grid-success.plt`'s actual gnuplot command: `cardinality` *is* the offered-load (1/λ) axis for the multipath scripts, normalized by `timeslots`. See `docs/SOURCE_CODE_AUDIT.md`.
- **Project-owned framework (`src/qnr_repro/`)** — built and unit-tested without touching netsquid:
  - `manifests.py`: `RunManifest` dataclass with the exact fields the PRD/TRD require (run_id, scenario, params, seed, repo_sha, env, status lifecycle including a `blocked` state), JSON round-trip.
  - `result_io.py`: thin wrapper around upstream's own `uiiit.simstat.MultiStat`/`Stat` — reuses their JSON parsing and their 95%-CI implementation (`statsmodels`) rather than reimplementing either, per the PRD's "don't alter metric definitions" rule. Confirmed `uiiit.simstat` imports fine with zero netsquid dependency.
  - `metrics.py`: `normalized_entanglement_rate` (formula taken verbatim from `grid-success.plt`, not invented), `average_fidelity_ci`, `average_swaps` — all built on `Stat.get_avg_ci`.
  - `validation.py`: scenario-config validation (fails loudly on missing keys / out-of-range values) and `require_metric` (raises instead of silently treating a missing metric as 0).
  - `paper_figures.py`: two generic, reusable plot shapes (x-y with CI, distribution boxplot) covering the structural pattern behind all of Figs. 11-20, each requiring labels/units/sample size as arguments rather than optional kwargs. Self-check demo uses data explicitly labeled "SYNTHETIC FIXTURE — not a research result".
  - 18 unit tests across `tests/test_{manifest,result_io,metrics,validation}.py`, all passing in the Docker environment.
- **`scripts/check_netsquid_access.sh`** — one-shot reachability check (website vs. package index, no retries, no credential printing). Run manually, not on a timer. Logged current status in `docs/NETSQUID_ACCESS_STATUS.md`.
- **Reference-data analysis (revised strategy)** — downloaded and MD5-verified both archives linked from the experiment README (272MB raw JSON, 313MB processed results); extracted (~2.8GB) into `artifacts/reference/` (gitignored, never committed); audited structure in `docs/REFERENCE_DATA_AUDIT.md`, including a genuine discrepancy (`first_grid.json` contains an `algorithm` value not in the pinned source). Built `scripts/analyze_reference_data.py`, which produced 5 real figures in `artifacts/figures/reference/` (calibration, grid rate+fidelity regular/irregular, irregular-grid swaps, disc degree distribution from 192/200 replications) — every one explicitly labeled as author-provided-data analysis, not a simulation run. Figs. 16-20 (rate/fidelity/delay distributions, serving probability) have data available in `results-disc/` but are not yet built, deferred given disk pressure (see below).

## Failed tests
None. 80 upstream `uiiit` tests + 18 project-owned tests all pass. Tests that would need
`netsquid`/`pydynaa` (upstream's other `test_*.py` files were confirmed in the audit to not
need it either, so there currently are zero tests in a BLOCKED state — the gate is earlier,
at `import netsquid` itself).

## Environment status
`qnr-repro:py3.7` Docker image built and verified (Python 3.7.17, linux/amd64 emulation on
Apple Silicon). Full non-gated pinned stack installs and imports. `netsquid`/`pydynaa` not
installed — blocked on the netsquid.org outage, see `docs/NETSQUID_ACCESS_STATUS.md`.

## Simulation status
Not run — requires `netsquid`, which requires the gated package index, which is down.

## Generated outputs
None from the simulator. Project-owned code/tests/docs only.

## Known limitations
- `pypi.netsquid.org`/`netsquid.org` unreachable from this sandbox (needs independent confirmation).
- Disk nearly full (4.3 GB free) — a hard blocker, independent of the Python/architecture question.
- Several upstream pinned dependencies (numpy/scipy/cysignals, pinned to 2020-era versions) predate official Apple Silicon wheel support, making native arm64 install unlikely to succeed cleanly.
- Two open questions about the source's own semantics (offered-load wiring, queue-expiry constant) not yet resolved by code reading.

## Next recommended action
1. **Disk is now at ~3.9GB free (99% full)** — this is the most pressing item. `artifacts/reference/` (2.8GB) can be deleted and re-extracted on demand later (re-download+verify+extract takes a few minutes, both MD5s confirmed good) if more headroom is needed before further work.
2. If continuing reference-data figures: Figs. 16-20 need a per-seed aggregation pass over `results-disc/`'s 265,824 files — build incrementally (stream file-by-file, don't glob everything into memory at once), per the existing pattern in `scripts/analyze_reference_data.py`'s degree-distribution function.
3. Periodically re-run `./scripts/check_netsquid_access.sh` (by hand) until it reports REACHABLE — nothing automated polls it.
4. Once reachable: register at the NetSquid forum if not already done, run `scripts/install_netsquid.sh` inside the container, then `minimal.py` as the Phase 3 smoke-test gate (exact commands in `docs/SESSION_HANDOFF.md`). This is still the only way to get a genuine NetSquid-reproduction result, as opposed to reference-data analysis.
