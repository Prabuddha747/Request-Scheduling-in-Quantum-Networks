# Session Handoff

**As of:** 2026-11-24, end of Phase 2 + Phase 3 (partial — environment built up to the NetSquid credential gate).

## What's done
- Phase 0/1 audit docs (see prior entry below) — repo audited, Mac preflight run.
- Phase 2: git repo initialized (`main` branch), `vendor/netsquid` submodule pinned at `v1.0.1`
  (SHA `fece16a66507520a976dea31038e2e6754fbab88`), project structure + 4 scenario configs +
  README/LICENSE/CITATION.cff committed (`7feeda2`).
- Phase 3 (partial): Docker environment decision validated empirically, not assumed —
  `qnr-repro:py3.7` image built (`Dockerfile` in repo root) with the full non-gated pinned
  scientific stack installed and import-verified. `netsquid`/`pydynaa` confirmed to require the
  gated `pypi.netsquid.org` index (not on public PyPI at all) and deliberately deferred to a
  runtime-only script (`scripts/install_netsquid.sh`) so credentials never touch an image layer
  or git history.
- Disk space resolved (4.3GB -> 9.8GB free).

## Exactly what's blocking progress right now
`pypi.netsquid.org` times out at the TCP level (port 443) from both this sandboxed shell and
from inside a Docker container — DNS resolves fine, connection just hangs. GitHub/PyPI work
fine from the same paths. **This needs the user to check `https://netsquid.org` from their own
regular browser.**

## Exact next action once that's confirmed reachable
```bash
# register at https://forum.netsquid.org/ucp.php?mode=register if not already done
docker run --rm -it -v "$PWD":/workspace -w /workspace qnr-repro:py3.7 bash
# inside the container:
NETSQUID_USER=<user> NETSQUID_PASS=<pass> scripts/install_netsquid.sh
# then the actual Phase 3 gate:
cd experiments/001-Scheduling-and-path-selection   # path inside vendor/netsquid
python3 export.py -h
python3 minimal.py
```
Compare `minimal.py`'s output against the exact values recorded in
`docs/SOURCE_CODE_AUDIT.md` / the upstream experiment README (degree-max=4, degree-min=2,
tsduration=107965.09..., etc.) — any mismatch beyond floating-point noise is a real
regression to investigate before going any further, per the PRD's regression-testing rule.

## Still pending after that
- Phase 4 (tests), Phase 5 (calibration), Phase 6 (grid), Phase 7 (random/disc), Phase 8
  (metrics), Phase 9 (figures), Phase 10 (final report), Phase 11 (push to a user-supplied
  GitHub remote — not done, no remote configured yet).
- Open source-code questions still to resolve in Phase 3/4 per `SOURCE_CODE_AUDIT.md`: exact
  offered-load (`1/λ`) wiring in `uiiit/traffic.py`, and the 10-slot queue-expiry constant's
  exact location.

## Context/resource notes
- One Docker image built (`qnr-repro:py3.7`), ~couple hundred MB, well within the now-9.8GB
  free disk.
- No simulation run yet (gated on NetSquid credentials), so no RAM/runtime data to report yet.
