# Project Status

**Current phase:** Phase 0, 1, 2 complete. Phase 3 (environment) and Phase 4 (tests) are each partially complete — everything not requiring the NetSquid package index is done and verified; the rest is blocked on a **confirmed real outage** of netsquid.org/pypi.netsquid.org (not a sandbox issue — the user checked from their own browser and it doesn't load for them either).

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

## Failed tests
None yet — no code has been run against the simulator.

## Environment status
Not installed. No Python 3.7/3.6 interpreter available on this machine yet (Homebrew's oldest is 3.9). See `DEPENDENCY_AUDIT.md` for the full compatibility assessment.

## Simulation status
Not run. Only read-only source inspection has occurred so far.

## Generated outputs
None (no experiments executed yet).

## Known limitations
- `pypi.netsquid.org`/`netsquid.org` unreachable from this sandbox (needs independent confirmation).
- Disk nearly full (4.3 GB free) — a hard blocker, independent of the Python/architecture question.
- Several upstream pinned dependencies (numpy/scipy/cysignals, pinned to 2020-era versions) predate official Apple Silicon wheel support, making native arm64 install unlikely to succeed cleanly.
- Two open questions about the source's own semantics (offered-load wiring, queue-expiry constant) not yet resolved by code reading.

## Next recommended action
1. User frees disk space (target: comfortably more than ~5 GB free, ideally well more, since Docker images and experiment raw output both consume non-trivial space).
2. User confirms/creates NetSquid forum credentials and verifies `pypi.netsquid.org` reachability from a normal (non-sandboxed) terminal.
3. User picks an environment strategy from `DEPENDENCY_AUDIT.md` (Docker Linux x86_64/Ubuntu-18.04-style container recommended).
4. Only then proceed to Phase 2 (project scaffolding, git init, submodule) and Phase 3 (actual environment creation + smoke test).
