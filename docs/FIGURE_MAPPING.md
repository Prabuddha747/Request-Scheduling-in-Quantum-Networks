# Figure → Source Script Mapping

**Two separate data sources now exist, and figures must say which one they're from:**
1. **NetSquid simulation** (would be `artifacts/raw/` + `artifacts/processed/`) — blocked on the
   netsquid.org outage, nothing generated this way yet.
2. **Authors' own published reference archives** (`artifacts/reference/`, see
   `docs/REFERENCE_DATA_AUDIT.md`) — downloaded, MD5-verified, and partially plotted already.
   Every figure from this source is explicitly labeled "Author-provided reference data ... NOT
   an independently executed NetSquid simulation" in its title, per the task's restriction.

| Paper figure | Script(s) that would produce it from scratch | Reference-archive status |
|---|---|---|
| Fig. 11 (calibration) | `first_calibration.py` → `first_calibration_plot.py` | **Generated from reference data** — `artifacts/figures/reference/REFERENCE_fig11_calibration.png` |
| Fig. 12 (grid normalized entanglement rate) | `first_gridmp.py`/`first_gridmpvar.py` at `cardinality=1` — **not** `first_grid.py` | **Generated from reference data** (all 4 policies, not just Strict FIFO) — `REFERENCE_fig12_13_grid_{regular,irregular}.png` |
| Fig. 13 (grid fidelity across policies) | `first_gridmp.py`/`first_gridmpvar.py`, all 4 `algos` | **Generated** (same files as Fig. 12, right subplot) |
| Fig. 14 (irregular grid avg swaps) | `first_gridmpvar.py` | **Generated from reference data** — `REFERENCE_fig14_irregular_grid_swaps.png` |
| Fig. 15 (random topology degree distribution) | `first_disc.py` (topology generation) | **Generated from reference data** (192/200 replications — `REFERENCE_fig15_disc_degree_distribution.png`; 8 likely discarded disconnected topologies, consistent with the model) |
| Figs. 16–17 (random rate distributions, fidelity 0 / 0.9) | `first_disc.py` → `export.py` → `first_disc_lenrate.py` | Data present in `results-disc/` (265,824 files) — **not yet built**, deferred for a larger per-seed aggregation pass (see `REFERENCE_DATA_AUDIT.md`) |
| Fig. 18 (random fidelity distribution, 1/λ=5) | `first_disc.py` | Data present, not yet built |
| Fig. 19 (random delay distribution, 1/λ=5) | `first_disc.py` | Data present, not yet built |
| Fig. 20 (serving probability vs graph distance, 1/λ=5) | `first_disc.py` + post-processing (exact script still unconfirmed — see below) | Data likely present, not yet built; post-processing path unresolved |

## Confidence notes
- Calibration and grid-vs-irregular-grid mappings are confirmed by direct script inspection (see `SOURCE_CODE_AUDIT.md`).
- Fig. 20's exact post-processing path is **not yet confirmed** — none of the visible scripts obviously compute "serving probability by graph distance" by name; still needs a grep pass over `manip.py` and the `graphs/*.plt` scripts.
- **A real discrepancy was found and is not papered over**: `first_grid.json` in the reference archive contains an `algorithm` value (`spf-dist`) not present in the pinned `v1.0.1` source's `first_grid.py` (`algos=["spf-hops","minmax-dist"]`). See `docs/REFERENCE_DATA_AUDIT.md` for detail. `first_gridmp.json`/`first_gridmpvar.json` showed no such mismatch.
- None of the reference-archive figures are a "NetSquid reproduction" status — they're
  author-provided-data analysis, a distinct category the PRD/TRD didn't originally anticipate
  as a fallback, used here only because netsquid.org is down. Once NetSquid is installed and
  `minimal.py`/the real scenarios run, genuine REPRODUCED/PARTIALLY REPRODUCED/BLOCKED/DEVIATED
  statuses (comparing *our own simulation* against the paper) still need to be assigned per the
  PRD's acceptance rule — comparing against the authors' own archive is not the same claim.
