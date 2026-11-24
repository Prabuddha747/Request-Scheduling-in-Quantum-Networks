# Session Handoff

**As of:** 2026-11-24, end of the reference-data-analysis pivot. netsquid.org/pypi.netsquid.org
remain down (confirmed real outage). **Disk is tight: ~3.9GB free, 99% full — read the disk
note below before doing anything else.**

## Revised project strategy (this entry)
The authors publish their own precomputed result archives (linked from the experiment README).
While NetSquid itself stays blocked, this project now also analyzes those archives directly —
**explicitly labeled as author-provided-data analysis, not an independently executed
simulation**, per the task's restrictions. This does not replace the eventual real
reproduction; it's parallel, unblocked work.

## What's done (full history; see docs/REPRODUCTION_LOG.md for narrative detail)
- Phase 0/1: source audit, Mac preflight.
- Phase 2: git repo, `vendor/netsquid` submodule @ `v1.0.1` (SHA `fece16a...`), project
  structure, scenario configs. Commit `7feeda2`.
- Phase 3 (non-gated): `qnr-repro:py3.7` Docker image, full pinned stack verified. Commit `9ccf20f`.
- Phase 4 (non-gated): 80 upstream unit tests pass. Commit `d6c00a4`.
- Offline framework: `src/qnr_repro/` (manifests, result I/O reusing upstream's own
  `uiiit.simstat`, metrics, validation, reusable figure plotting), 18 tests. Commit `054865b`.
- **This session (not yet committed):**
  - Downloaded + MD5-verified both reference archives (272MB JSON, 313MB results) — matched exactly.
  - Extracted into `artifacts/reference/` (~2.8GB, gitignored).
  - Audited structure: `docs/REFERENCE_DATA_AUDIT.md`. Found a real discrepancy (`first_grid.json`
    has an `algorithm` value — `spf-dist` — not in the pinned `v1.0.1` source).
  - Added `load_dat_count`/`load_dat_points` to `result_io.py` (matches upstream's `Stat.export()` format, confirmed by reading `uiiit/simstat.py` first).
  - Built `scripts/analyze_reference_data.py`, generated 5 real figures in
    `artifacts/figures/reference/` (calibration, grid rate+fidelity ×2 topologies, irregular-grid
    swaps, disc degree distribution — 192/200 replications). All labeled as reference-data
    analysis in-figure.
  - Updated `docs/FIGURE_MAPPING.md`, `docs/PROJECT_STATUS.md` with the revised plan.

## Immediate next step — commit this session's work
```bash
cd /Users/prabuddhaverma/development/summit/phdproject
git add .gitignore docs/REFERENCE_DATA_AUDIT.md docs/FIGURE_MAPPING.md docs/PROJECT_STATUS.md \
        docs/SESSION_HANDOFF.md src/qnr_repro/result_io.py scripts/analyze_reference_data.py \
        artifacts/figures/reference
git status --short   # review -- artifacts/reference/ must NOT appear (gitignored)
git commit -m "feat: analyze authors' published reference archives"
```

## The disk situation (read before extracting/downloading anything else)
`artifacts/reference/` is ~2.8GB (1.0GB raw JSON + 1.8GB processed results — the gap vs. the
~1GB of actual file content is APFS overhead from 266,592 tiny files). This pushed free disk
from ~4.9GB down to **~3.9GB (99% full)**. Both archives' MD5s are verified and recorded, so
`artifacts/reference/` can be safely deleted and re-extracted later in a few minutes if the
space is needed:
```bash
rm -rf artifacts/reference
# later, to restore:
curl -L -o /tmp/json.tgz https://turig.iit.cnr.it/~claudio/public/netsquid-001-json.tgz
curl -L -o /tmp/results.tgz https://turig.iit.cnr.it/~claudio/public/netsquid-001-results.tgz
md5 /tmp/json.tgz /tmp/results.tgz   # compare against docs/REFERENCE_DATA_AUDIT.md
mkdir -p artifacts/reference/raw-json artifacts/reference/results
tar -xzf /tmp/json.tgz -C artifacts/reference/raw-json/
tar -xzf /tmp/results.tgz -C artifacts/reference/results/
```

## What's NOT done yet from this archive
Figs. 16-20 (random-topology rate/fidelity/delay distributions, serving probability by graph
distance) — the data exists in `results-disc/`'s 265,824 files, but needs a larger per-seed
aggregation (stream file-by-file, same pattern as the degree-distribution function in
`scripts/analyze_reference_data.py`). Deferred given the disk pressure above, not because it's
hard — pick this up once disk headroom is confirmed comfortable again.

## The real NetSquid blocker (unchanged, separate from the above)
```bash
./scripts/check_netsquid_access.sh   # run by hand, no auto-retry
```
Once it reports REACHABLE:
```bash
docker run --rm -it -v "$PWD":/workspace -w /workspace qnr-repro:py3.7 bash
NETSQUID_USER=<user> NETSQUID_PASS=<pass> scripts/install_netsquid.sh
cd vendor/netsquid/experiments/001-Scheduling-and-path-selection
python3 minimal.py   # compare against docs/SOURCE_CODE_AUDIT.md's recorded expected output
```

## Resource notes
- Disk: ~3.9GB free (99% full) — tightest it's been this session. Do not run further large
  downloads/extractions without rechecking `df -h .` first.
- RAM: the 147MB JSON files were parsed via `jq` writing to disk (not Python `json.load`) after
  observing genuinely tight free memory (~70MB free pages at one point) — `first_disc.json`
  (747MB) was deliberately never loaded directly; its structure was derived from source code +
  the processed `.dat` filenames instead.
- All archive downloads/extractions/figure generation ran one at a time, nothing in parallel.
