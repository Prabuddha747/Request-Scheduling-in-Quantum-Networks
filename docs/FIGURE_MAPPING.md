# Figure → Source Script Mapping

| Paper figure | Script(s) that actually produce it | Policies/axes involved | Status |
|---|---|---|---|
| Fig. 11 (calibration) | `first_calibration.py` → `first_calibration_plot.py` | dephase/depol sweep, chain-length sweep, 4-point distance sweep | Not run yet |
| Fig. 12 (grid normalized entanglement rate, Strict FIFO) | `first_gridmp.py` or `first_gridmpvar.py` at `cardinality=1`, `algo` without skip suffix (Strict FIFO) — **not** `first_grid.py`, despite the name | regular vs irregular grid, offered load | Not run yet |
| Fig. 13 (grid fidelity across policies) | `first_gridmp.py`/`first_gridmpvar.py`, all 4 `algos` values, `cardinality=1` | Strict/Best/Random FIFO × SPF/MinMax | Not run yet |
| Fig. 14 (irregular grid avg swaps) | `first_gridmpvar.py` | same as above, irregular only | Not run yet |
| Fig. 15 (random topology degree distribution) | `first_disc.py` (topology generation, independent of policy) | 200 replications | Not run yet |
| Figs. 16–17 (random rate distributions, fidelity 0 / 0.9) | `first_disc.py` → `export.py` → `first_disc_lenrate.py` | 1/λ 1..5, 200 reps × 1000 slots | Not run yet |
| Fig. 18 (random fidelity distribution, 1/λ=5) | `first_disc.py` | per-policy | Not run yet |
| Fig. 19 (random delay distribution, 1/λ=5) | `first_disc.py` | per-policy | Not run yet |
| Fig. 20 (serving probability vs graph distance, 1/λ=5) | `first_disc.py` + post-processing (exact script TBD — likely `manip.py` or custom) | per-policy | Not run yet |

## Confidence notes
- Calibration and grid-vs-irregular-grid mappings are confirmed by direct script inspection (see `SOURCE_CODE_AUDIT.md`).
- Fig. 20's exact post-processing path is **not yet confirmed** — none of the visible scripts obviously compute "serving probability by graph distance" by name; this needs a grep pass over `manip.py` and the `graphs/*.plt` scripts in Phase 3 before claiming a pipeline for it.
- All "Not run yet" statuses will be updated to REPRODUCED / PARTIALLY REPRODUCED / BLOCKED / DEVIATED only after Phase 9, with evidence, per the PRD's acceptance rule (no shape-only claims).
