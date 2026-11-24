# Session Handoff

**As of:** 2026-11-24, end of the offline development phase. Blocked on a confirmed real
netsquid.org/pypi.netsquid.org outage (user-verified from their own browser) — everything
that doesn't need that index is done.

## What's done
- Phase 0/1: source audit, Mac preflight (see earlier log entries).
- Phase 2: git repo (`main`), `vendor/netsquid` submodule pinned at `v1.0.1`
  (SHA `fece16a66507520a976dea31038e2e6754fbab88`), project structure, 4 scenario configs,
  README/LICENSE/CITATION.cff. Commit `7feeda2`.
- Phase 3 (non-gated part): `qnr-repro:py3.7` Docker image (`linux/amd64`, Python 3.7.17),
  full pinned scientific stack verified importable. `Dockerfile` + `scripts/install_netsquid.sh`
  (runtime-only install step, keeps credentials out of the image/git). Commit `9ccf20f`.
- Phase 4 (non-gated part): all 80 upstream `uiiit` unit tests pass (none of them import
  netsquid). Commit `d6c00a4`.
- Offline phase: resolved the offered-load wiring question (see `SOURCE_CODE_AUDIT.md`), built
  `src/qnr_repro/` (manifests, result I/O reusing upstream's own `uiiit.simstat`, metrics,
  validation, reusable figure plotting), 18 passing project-owned tests, and
  `scripts/check_netsquid_access.sh` + `docs/NETSQUID_ACCESS_STATUS.md`. **Not yet committed —
  do that next** (see below).

## Immediate next step (before anything else)
```bash
cd /Users/prabuddhaverma/development/summit/phdproject
git add docs/SOURCE_CODE_AUDIT.md docs/NETSQUID_ACCESS_STATUS.md scripts/check_netsquid_access.sh \
        src tests docs/PROJECT_STATUS.md docs/REPRODUCTION_LOG.md docs/SESSION_HANDOFF.md
git status --short   # review
git commit -m "feat: add offline experiment management/result/figure framework"
```

## The one real blocker
`netsquid.org` / `pypi.netsquid.org`: confirmed unreachable both from this environment and
from the user's own browser — a real outage, not a sandbox artifact. Re-check by hand with:
```bash
./scripts/check_netsquid_access.sh
```
Do not script automatic retries/polling of this (PRD explicitly says don't repeatedly attempt
installation).

## Exact next action once it's back
```bash
docker run --rm -it -v "$PWD":/workspace -w /workspace qnr-repro:py3.7 bash
# inside the container:
NETSQUID_USER=<user> NETSQUID_PASS=<pass> scripts/install_netsquid.sh
cd vendor/netsquid/experiments/001-Scheduling-and-path-selection
python3 export.py -h
python3 minimal.py
```
Compare `minimal.py`'s output against the values recorded in `docs/SOURCE_CODE_AUDIT.md` /
upstream's experiment README (degree-max=4, degree-min=2, tsduration=107965.09..., etc.) — any
mismatch beyond floating-point noise is a real regression to investigate (PRD regression rule).

## Still pending after that
Phase 5 (calibration) through Phase 11 (git delivery to a user-supplied remote — none
configured yet). Two still-open source-code questions for Phase 3/4 proper: the exact 10-slot
queue-expiry constant's location in `uiiit/oracle.py`, and confirming the `0.995` vs `1.0`
constant in the normalized-rate formula once real data exists.

## Resource notes
- Disk: 6.9GB free (dropped from 9.8GB after the Docker image + build layers, ~1GB total;
  pruned dangling build cache already). Recheck before any large experiment batch.
- RAM: not exercised yet — only unit tests and a tiny matplotlib self-check have run, nothing
  resembling a real simulation workload.
- Context: this session did a bounded source audit, built ~6 small project-owned modules, and
  ran everything inside the one Docker container at a time (no parallel heavy workloads) —
  no exact token count is claimable, so none is given.
