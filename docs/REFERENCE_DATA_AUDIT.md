# Reference Data Audit — Authors' Published Result Archives

These are the authors' own precomputed outputs, linked from the experiment README
(`vendor/netsquid/experiments/001-Scheduling-and-path-selection/README.md`). This is
**analysis of author-provided results, not output from an independently executed
NetSquid simulation** — NetSquid itself remains uninstalled (blocked on the
netsquid.org outage, see `docs/NETSQUID_ACCESS_STATUS.md`). Every figure generated
from this data says so in its title.

## Provenance and integrity

| Archive | URL | Documented size | HTTP Content-Length | MD5 (README) | MD5 (verified) |
|---|---|---|---|---|---|
| Raw JSON | `https://turig.iit.cnr.it/~claudio/public/netsquid-001-json.tgz` | 272 MB | 285,130,710 B | `208815839ff3a815e946fd0a8b9ab7aa` | **MATCH** |
| Processed results | `https://turig.iit.cnr.it/~claudio/public/netsquid-001-results.tgz` | 313 MB | 327,880,369 B | `754d5db3b246ede9d9aa9874abf75167` | **MATCH** |

Both MD5s verified against the exact values in the experiment README on download. Note the
original link is `http://` and 301-redirects to `https://turig.iit.cnr.it/...` — followed
automatically by `curl -L`.

## Disk footprint (measured, not estimated)

- Compressed archives: 272 MB + 313 MB ≈ 585 MB (deleted after extraction + MD5 verification —
  redundant once extracted and checksummed; re-downloadable from the URLs above if needed again).
- Extracted `raw-json/`: 1.0 GB (5 files — see below).
- Extracted `results/`: 1.8 GB on disk despite ~1.0 GB of file content — the gap is APFS
  per-file block overhead from 266,592 small `.dat` files, not a measurement error.
- **Total: ~2.8 GB** in `artifacts/reference/` (gitignored — never committed; see `.gitignore`).
- This pushed disk from ~4.9 GB free down to **~3.9 GB free (99% full)**. Flagging this as a
  real constraint: do not extract anything else here without checking `df -h .` first, and
  consider whether `artifacts/reference/` should be deleted and re-extracted on demand once
  the current analysis pass is done (re-download+extract+verify takes well under 5 minutes).

## Raw JSON archive (`artifacts/reference/raw-json/`)

| File | Size | Entries (Stat objects) | Notes |
|---|---|---|---|
| `first_calibration.json` | 664 KB | 96 | Loaded fully (safe at this size) |
| `first_grid.json` | 7.6 MB | 9 | Loaded fully |
| `first_gridmp.json` | 147 MB | 40 | Parsed via `jq` to disk, not `json.load` in Python |
| `first_gridmpvar.json` | 147 MB | 40 | Same |
| `first_disc.json` | 747 MB | **not parsed** | Too large to safely `json.load` on this 8GB machine (tight free memory observed during this session — see below). Structure derived analytically instead (see next section). |

### Why `first_disc.json` was not parsed directly
At audit time, `vm_stat`/`memory_pressure` showed only ~70 MB of literally free pages (macOS
reclaims inactive/compressed pages dynamically, so this isn't a hard ceiling, but it's not a
margin to gamble a 747 MB `json.load()` against on an 8 GB laptop with other apps running).
`jq`'s default mode also fully parses into memory and was judged too risky at this size (it
was fine for the two 147 MB files). Its *structure* is known with confidence anyway, from:
- The pinned `first_disc.py` source: `num_nodes=25`, `disc_radius=6`, `num_runs=200` (seeds),
  `timeslots=1000`, `cardinalities=[1,3,5]`, `algos=[spf-hops, minmax, always-skip, random-skip]`,
  `dephase_rates=[1e5, 1e6]` → up to 200×3×4×2 = **4,800 possible `Stat` entries** (some may be
  absent if a topology was disconnected and regenerated with a different effective seed/skip).
- Direct confirmation from the **processed** `results-disc/` filenames (see below), which encode
  every `(algorithm, cardinality, dephase_rate, seed)` combination as a filename and are cheap to
  `glob()` without touching the raw JSON at all.

**If a figure ever needs the raw per-slot JSON data for the disc scenario**, read it with a true
streaming parser (e.g. `ijson`, not currently installed — small, pure-Python-plus-C, would need
adding to `requirements-analysis.txt`) rather than `json.load()`. Not needed yet: the processed
`.dat` files already cover every metric used by Figs. 15-20 at per-seed granularity.

## Processed results archive (`artifacts/reference/results/`)

| Directory | File count | Granularity |
|---|---|---|
| `results-calibration/` | 24 | per (depol_rate, dephase_rate) sweep axis |
| `results-grid/` | 242 | per (algorithm, node_distance, num_nodes) |
| `results-gridmp/` | 238 | per (algorithm, metric) — x-axis (cardinality) is columns, not filenames |
| `results-gridmpvar/` | 234 | same, irregular grid |
| `results-disc/` | **265,824** | per (algorithm, cardinality, dephase_rate, **seed**) — true per-replication data |
| `results-disc-lenrate/` | 24 | per (algorithm, cardinality, dephase_rate), lenrate only |

Every `.dat` file matches `uiiit.simstat.Stat.export()`'s format exactly (confirmed by reading
`uiiit/simstat.py` before writing any parser): a count metric is `"sum count\n"`, a point metric
is one value per line. `src/qnr_repro/result_io.py` now has `load_dat_count`/`load_dat_points`
for this format.

## Discrepancy found: `first_grid.json` has an algorithm not in the pinned source

`first_grid.json`'s 9 entries span **3** distinct `algorithm` values: `spf-hops`, `minmax-dist`,
and **`spf-dist`**. The pinned `v1.0.1` source's `first_grid.py` only lists
`algos = ["spf-hops", "minmax-dist"]` — no `spf-dist`. Two plausible explanations, neither
confirmed: (a) the archived data was generated by a slightly different version of the script
than what's tagged `v1.0.1`, or (b) the archive bundles output from more than one run across
versions. **Not resolved, not papered over** — this means `first_grid.json`'s exact 1:1
correspondence to the pinned source's `first_grid.py` is not guaranteed, so any figure built
from it should be labeled as "from the published archive," not "reproduces `first_grid.py` at
the pinned commit." (`first_gridmp.json`/`first_gridmpvar.json` showed no such mismatch — their
4 algorithm values matched the pinned source exactly.)

## What was actually generated from this data

See `docs/FIGURE_MAPPING.md` for the updated status table. `scripts/analyze_reference_data.py`
produced 5 figures in `artifacts/figures/reference/`, each labeled
"Author-provided reference data ... NOT an independently executed NetSquid simulation":
calibration fidelity-vs-distance, regular-grid rate+fidelity vs offered load (all 4 policies),
irregular-grid average swaps vs offered load, and a degree distribution from 192/200 disc
replications (8 presumably discarded as disconnected topologies, consistent with the paper's
model). Figs. 16-20 (rate/fidelity/delay distributions, serving probability by graph distance)
are not yet built — the data exists in `results-disc/` but needs a larger per-seed aggregation
pass; deferred given the current disk pressure (see above) rather than rushed.
