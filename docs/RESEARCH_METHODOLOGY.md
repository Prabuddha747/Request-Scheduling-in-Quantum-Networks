# Research Methodology Summary

Source: Cicconetti, Conti, Passarella, "Request Scheduling in Quantum Networks," IEEE TQE 2021 (DOI 10.1109/TQE.2021.3090532); PDF present at `docs/Request_Scheduling_in_Quantum_Networks.pdf`. This summary is built from the PRD/TRD extraction plus the source-code audit; a full close-read of paper sections III–V and the MinMax appendix is deferred to Phase 5–9 when results are being validated against it figure-by-figure (reading the paper in isolation now, before any simulation exists to compare, would not change any Phase 0/1 decision).

## Model
- Time-slotted quantum network; a central Oracle knows which local entanglement links succeeded this slot (the "reduced graph") before deciding routing.
- Two separable decisions per slot: **scheduling** (which pending requests to serve) and **path selection** (which path in the reduced graph).
- Requests arrive Poisson; source/destination pairs drawn uniformly (with replacement) from node pairs; a request is dropped if unserved after more than `max_delay` (nominally 10 slots — exact enforcement point not yet located in `uiiit/oracle.py`, to confirm in Phase 3/4).
- Local entanglement pairs are not carried over between slots.

## Scheduling policies (confirmed against `uiiit/oracle.py`)
- **Strict FIFO** (`skip_policy="none"`): never skip a valid path in the first pass.
- **Best FIFO** (`skip_policy="always-skip"`): skip a path whose cost exceeds the running average; unskipped requests get a second pass.
- **Random FIFO** (`skip_policy="random-skip"`): skip with probability `max(0, 1 − E[c]/c(σ))`; second pass as above.

## Path-selection algorithms (confirmed)
- `spf` with metric `hops` or `dist` (shortest-path-first).
- `minmax` (MinMax cost; metric argument unused for this algorithm per the oracle's own parameter docstring).

## Scenarios (see `DEPENDENCY_AUDIT.md`/`SOURCE_CODE_AUDIT.md` for exact source-code parameter cross-check)
1. **Calibration** — chain topology; fixed 15 km total length with 3–15 nodes, and a 4-point (1/2.5/5/7.5 km) distance sweep at 3 nodes; dephase/depol swept around the baseline.
2. **Grid** — 25 nodes (5×5), regular (1.8 km) and irregular (`[1.08, 2.52]` km) spacing; scheduling-policy comparison lives in the multipath scripts at `cardinality=1`, not in the plain `first_grid.py`.
3. **Random/disc** — 25 nodes in a 6 km radius disc, 2 km link threshold, disconnected topologies regenerated, 200 replications × 1,000 slots.

## Metrics (see PRD §9 / TRD §8–9 for the full table — not duplicated here)
Normalized entanglement rate, average fidelity, average swaps, serving probability by graph distance, and the raw per-path `fidelity-X`/`latency-X`/`delay`/`meas`/`length` fields emitted directly by `minimal.py`-style runs.

## Open items carried into later phases
- Confirm exact offered-load (`1/λ`) wiring in `uiiit/traffic.py` (flagged in `SOURCE_CODE_AUDIT.md`).
- Confirm the 10-slot queue-expiry constant's actual location/value in code.
- Do the full paper read (sections III–V, MinMax appendix) once a smoke-test run exists, so paper claims can be checked against real output rather than against intent.
