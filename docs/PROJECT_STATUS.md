# Project Status

**Current phase:** Phase 0, 1, 2 complete. Phase 3 (environment) is partially complete — the credential-free portion of the Docker environment is built and verified; blocked on NetSquid account/credentials for the rest.

## Completed
- Confirmed all 4 docs present in `docs/` (3 PRD/Plan/TRD PDFs + the research paper PDF).
- Read PRD, Implementation Plan, TRD in full.
- Shallow-cloned `ccicconetti/netsquid` @ `v1.0.1` into scratchpad (not vendored into the project yet) and audited its actual structure, scripts, and parameters against the PRD/TRD.
- Resolved and recorded the pinned commit SHA: `fece16a66507520a976dea31038e2e6754fbab88`.
- Produced `SOURCE_CODE_AUDIT.md`, `FIGURE_MAPPING.md`, `DEPENDENCY_AUDIT.md`, `RESEARCH_METHODOLOGY.md`.
- Ran Mac/arch/Python/disk/RAM/network preflight checks (see `DEPENDENCY_AUDIT.md`).

## Pending
- User needs a NetSquid forum account (pypi.netsquid.org credentials) and to confirm `pypi.netsquid.org` is reachable from their own browser/terminal (it timed out, TCP-level, from this sandbox — DNS resolves fine). See `docs/ENVIRONMENT_SETUP.md` for exact next command once that's confirmed.
- Phase 3 remainder: `scripts/install_netsquid.sh` inside the container, then run `minimal.py` smoke test (Phase 3 proper).
- Phases 4 onward (tests, calibration, grid, random/disc, figures, final report) all blocked on the above.

## Resolved
- **Disk space** — freed from 4.3 GB to 9.8 GB free by deleting regenerable app caches (`~/Library/Caches/Google`, partial `dotslash`) and 3 already-installed `.dmg` installers from Downloads. No project or user data touched.
- **Environment path decision** — Docker `linux/amd64`, Python 3.7, confirmed empirically rather than assumed: `python:3.7-slim-buster` runs fine under Apple Silicon emulation, and the full non-gated pinned scientific stack (numpy/scipy/pandas/matplotlib/cysignals) builds and imports successfully. Image tagged `qnr-repro:py3.7`. `netsquid`/`pydynaa` are confirmed to require the gated index (not on public PyPI) and are deliberately deferred to a runtime install step so credentials never enter the image or git history.
- **Project scaffolding (Phase 2)** — git repo initialized, `vendor/netsquid` submodule pinned at `v1.0.1` (SHA `fece16a66507520a976dea31038e2e6754fbab88`, matches audit), directory structure created, 4 scenario configs written with source-verified parameters, `README.md`/`LICENSE`/`CITATION.cff`/`Dockerfile`/`scripts/install_netsquid.sh` added. Committed as `7feeda2`.

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
