# Project Status

**Current phase:** Phase 0, 1, 2 complete. Phase 3 (environment), Phase 4 (tests), and the
project-owned experiment-management/result-processing/figure framework (parts of Phases 8-9)
are each complete for everything that doesn't require the NetSquid package index. Remaining
work in every phase is blocked on a **confirmed real outage** of netsquid.org/pypi.netsquid.org
(user-verified from their own browser, not a sandbox artifact). Re-check with
`./scripts/check_netsquid_access.sh` (one-shot, no auto-retry).

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
1. Periodically re-run `./scripts/check_netsquid_access.sh` (by hand, not automated) until it reports REACHABLE.
2. Once reachable: register at the NetSquid forum if not already done, run `scripts/install_netsquid.sh` inside the container, then `minimal.py` as the Phase 3 smoke-test gate. Exact commands in `docs/SESSION_HANDOFF.md`.
3. After that passes: Phase 5 (calibration) is next in sequence — do not skip ahead to grid/disc.
4. Disk is at 6.9GB free (down from 9.8GB after Docker image/cache growth, still healthy) — recheck before any large experiment batch per the PRD's RAM/disk policy.
