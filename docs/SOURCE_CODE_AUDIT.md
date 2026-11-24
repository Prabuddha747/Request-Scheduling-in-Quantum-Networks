# Source Code Audit — ccicconetti/netsquid @ v1.0.1

## Provenance
- Repo: https://github.com/ccicconetti/netsquid
- Tag: `v1.0.1`
- Resolved commit SHA: `fece16a66507520a976dea31038e2e6754fbab88`
  (tag object SHA: `006a8025611df544d4b750e27e30b453e9f997ee`)
- Repo size at this tag: 732 KB (code only, no data)
- License: MIT (preserved on vendoring)
- Audited via a throwaway shallow clone in the scratchpad (not yet vendored into the project — that's Phase 2).

## Top-level layout
```
README.md, LICENSE, requirements.txt, .gitignore
experiments/001-Scheduling-and-path-selection/   <- the only experiment relevant to this paper
scripts/statexport.py
uiiit/            <- the NetSquid extension library + unit tests (test_*.py)
Sandbox/, Tutorial/   <- not relevant to the paper reproduction
```

## `experiments/001-Scheduling-and-path-selection/` contents
| File | Role |
|---|---|
| `minimal.py` | Documented smoke test: 3×3 grid, 100 time slots, fixed params. Prints metrics to stdout (no JSON file). |
| `first_calibration.py` | Calibration sweeps (chain topology). **Not included in `run_all.sh`** — must be run separately. |
| `first_calibration_plot.py` | Plots calibration output → Fig. 11-style. |
| `first_grid.py` | Grid, **single-path only**, `algos = ["spf-hops", "minmax-dist"]`. No skip-policy suffix present → **skip_policy always resolves to `"none"` (Strict FIFO only)**. `num_nodes = [3,4,5]` is the grid *side length* (so 5×5 = 25 nodes, matching the paper's 25-node grid); `grid_length=9` km ⇒ `node_distance = 9/5 = 1.8 km` for the 25-node case — matches PRD's regular-grid spacing exactly. `nworkers = 50` (parallel socket workers). |
| `first_gridmp.py` | Grid, **multipath**, `algos = ["spf-hops", "minmax", "always-skip", "random-skip"]`, `cardinalities = 1..10`. **This is where Strict/Best/Random FIFO are actually compared** (via substring match on skip-policy in `run_simulation.py`), using `cardinality=1` for the single-path case. |
| `first_gridmpvar.py` | Same as `first_gridmp.py` but with variable (irregular) link length — this is the "irregular grid" scenario. |
| `first_disc.py` | Random/disc topology. `num_nodes=25`, `disc_radius=6` km, `num_runs=200` (replications), `timeslots=1000`, `cardinalities=[1,3,5]`, same 4-way `algos` list as above. Matches PRD exactly. |
| `first_disc_lenrate.py` | Post-processing for disc results. |
| `manip.py` | Generic post-processing helper. |
| `export.py` | CLI: `export.py <statfile.json> [--outdir DIR] [--factor cardinality]`. Converts raw `MultiStat` JSON dumps into per-metric result directories. |
| `run_all.sh` | Runs `grid`, `gridmp`, `gridmpvar`, `disc` only — **excludes calibration**. |
| `export_all.sh` | Runs `export.py` over `disc`/`grid` (no `--factor`) and `gridmp`/`gridmpvar` (`--factor cardinality`), then `first_disc_lenrate.py`. |
| `graphs/*.plt` | Gnuplot scripts mapping fairly directly to paper figures (e.g. `grid-fidelity.plt`, `disc-degree.plt`, `calibration-fidelity-*.plt`). |

### Published pre-computed results (important for resource planning)
The experiment README links the authors' own precomputed archives:
- Raw JSON results: `netsquid-001-json.tgz` (272 MB, MD5 `208815839ff3a815e946fd0a8b9ab7aa`)
- Processed results: `netsquid-001-results.tgz` (313 MB, MD5 `754d5db3b246ede9d9aa9874abf75167`)
- Host: `http://turig.iit.cnr.it/~claudio/public/...` (plain HTTP, not yet verified reachable from this environment)

These are a legitimate, citable fallback/cross-check for figure generation if full local reruns are infeasible on this machine — they are the authors' own output, not fabricated data. Reachability and currency of that link need to be checked in Phase 3 before relying on it.

## Scheduling-policy → skip_policy mapping (confirmed in `run_simulation.py` + `uiiit/oracle.py`)
```python
skip_policy = "none"
if "random-skip" in conf["algorithm"]: skip_policy = "random-skip"
elif "always-skip" in conf["algorithm"]: skip_policy = "always-skip"
```
- `"none"` → **Strict FIFO**
- `"always-skip"` → **Best FIFO**
- `"random-skip"` → **Random FIFO**

Path-selection algorithm/metric is a separate substring match: `"spf"`/`"minmax"` × `"hops"`/`"dist"`.

## Parameter cross-check against PRD/TRD baseline values
| Parameter | PRD/TRD value | Source code | Match |
|---|---|---|---|
| p_loss_init | 0.1 | `p_loss_init=0.1` (first_grid.py) | ✅ |
| fibre attenuation η | 0.1 dB/km | `p_loss_length=0.1` | ✅ (same param, different name) |
| dephase_rate baseline | 1 MHz | `dephase_rate=1e6` (grid) | ✅ |
| depol_rate baseline | 5 kHz | `depol_rate=5e3` (grid) | ✅ |
| gate_duration | 10 ns | `gate_duration=10` | ✅ |
| Grid: 25 nodes, 1.8 km spacing | yes | `num_nodes=5` (→25), `node_distance=9/5=1.8` | ✅ |
| Grid: offered load 1..10 | yes | not found as `1/λ` directly in `first_grid.py`/`first_gridmp.py`'s visible slice — **needs deeper read of `cardinalities`/app wiring in Phase 3**; `cardinalities=1..10` in multipath scripts may be a *different* axis (multipath fan-out) than offered load 1/λ. **Flagging as open question, not resolved.** | ⚠️ open |
| Disc: 25 nodes, radius 6 km, 200 reps, 1000 slots | yes | exact match in `first_disc.py` | ✅ |
| Calibration: 15 km chain, 3–15 nodes | yes | `total_length=15`, `range(3,16)` | ✅ |
| Calibration: distance sweep 1–7.5 km | "swept from 1 to 7.5 km" | only 4 discrete points: `[1, 2.5, 5, 7.5]` km, `num_nodes=3` fixed | ⚠️ PRD's "swept" language overstates granularity — it's 4 points, not continuous |
| Queue expiry > 10 slots | yes | not yet located in `uiiit/oracle.py` beyond `max_delay` param; needs confirmation in Phase 3/4 | ⚠️ open |

## Deviations / open questions to resolve before claiming any figure "REPRODUCED"
1. ~~**Offered load (1/λ) wiring**~~ **RESOLVED** by reading `graphs/grid-success.plt`'s actual plot command:
   `'results-gridmp/algorithm=spf-hops.success-0.9.dat' u 1:($2/$1*0.995e-4)` — column 1 is the
   `--factor cardinality` value `export.py` exported, column 2 is the `success-X` count. So
   **`cardinality` *is* the offered-load (1/λ) axis** for the multipath scripts, and
   `0.995e-4 ≈ 1/10000` (the grid scenario's `timeslots=10000`) is the normalizing denominator.
   Exact derivation of the `0.995` factor (vs. a clean `1.0`) is deferred to Phase 8 when real
   data exists to sanity-check against — not invented now.
2. **`nworkers = 50`** in `first_grid.py`/likely similar in other scripts — must be overridden to a low value (see Resource section) on the 8 GB M1 Air. This is a deliberate *execution* deviation, not a scientific one — document per-run in the manifest.
3. **`run_all.sh` omits calibration** — calibration must be run and exported manually; `export_all.sh` has no calibration branch either, so Fig. 11 export path is also likely manual (post-processing is `first_calibration_plot.py`, not `export.py`).
4. **Figures 12–14 are produced from `first_gridmp.py`/`first_gridmpvar.py` at `cardinality=1`**, not from `first_grid.py` — despite `first_grid.py` superficially looking like "the grid experiment." Any config/manifest naming must make this explicit to avoid silently reporting the wrong script as the source of a figure.

## Unit tests available upstream
`uiiit/test_utils.py`, `test_traffic.py`, `test_stat.py`, `test_topology.py` — run via `python -m unittest` from inside `uiiit/`, documented in root README.
