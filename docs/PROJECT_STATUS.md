# Project Status

**Current phase:** Phase 0 (source audit) complete; Phase 1 (Mac preflight) complete as a documentation pass. Awaiting user approval before any installation (Phase 2 onward).

## Completed
- Confirmed all 4 docs present in `docs/` (3 PRD/Plan/TRD PDFs + the research paper PDF).
- Read PRD, Implementation Plan, TRD in full.
- Shallow-cloned `ccicconetti/netsquid` @ `v1.0.1` into scratchpad (not vendored into the project yet) and audited its actual structure, scripts, and parameters against the PRD/TRD.
- Resolved and recorded the pinned commit SHA: `fece16a66507520a976dea31038e2e6754fbab88`.
- Produced `SOURCE_CODE_AUDIT.md`, `FIGURE_MAPPING.md`, `DEPENDENCY_AUDIT.md`, `RESEARCH_METHODOLOGY.md`.
- Ran Mac/arch/Python/disk/RAM/network preflight checks (see `DEPENDENCY_AUDIT.md`).

## Pending
- User decision on environment path (native arm64 attempt vs. Rosetta x86_64 vs. Docker Linux container) — see `DEPENDENCY_AUDIT.md` recommendation (Docker Linux most likely to work).
- User needs a NetSquid forum account (pypi.netsquid.org credentials) before any `pip install` of the simulator stack can succeed; `netsquid.org`/`pypi.netsquid.org` reachability from this sandboxed shell is unconfirmed (timed out) and needs checking from the user's own terminal.
- Everything from Phase 2 (project scaffolding / git init) onward.

## Resolved
- **Disk space** — freed from 4.3 GB to 9.8 GB free by deleting regenerable app caches (`~/Library/Caches/Google`, partial `dotslash`) and 3 already-installed `.dmg` installers from Downloads. No project or user data touched.

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
