# Assumptions Register

Unresolved details not yet pinned to an exact paper statement. Nothing here
should be treated as settled; each entry blocks a `PAPER_REPRODUCTION` label
on the affected result until resolved.

## A1. PPO training data provenance
**Issue:** Paper Section 6.6.5 says "Training datasets are generated using
the Qoala Simulator [26]." Our primary backend is SimPy, not Qoala.
**Why it matters:** PPO policies trained on SimPy-generated trajectories may
differ from the paper's Qoala-trained policies, even with identical reward/
state/action definitions.
**Current treatment:** None yet — PPO is Phase 6, gated behind Phase 0-5.
**Impact:** Any PPO result from our SimPy backend must be labeled
`SCHEDULER_MODEL_REPRODUCTION`, never `PAPER_REPRODUCTION`, unless Qoala
access is obtained (Phase 8).
**Resolution path:** Attempt Qoala/NetSquid install (Phase 8, optional,
credential-gated). Otherwise stays labeled as model reproduction.

## A2. Link-quality label mismatch between Table 2 and Table 3
**Issue:** Table 2 names link qualities "Bad / Medium / Good". Table 3 names
them "Worst / Medium / [third row unlabeled in page 12 crop, needs re-check]".
**Why it matters:** Need to confirm whether Table 3's three rows map 1:1 to
Table 2's three rows in the same order, since t_cycle/P_s/F/t_state in Table 3
must be derived from Table 2's eta parameters via Eq. 1-2.
**Current treatment:** Not implemented; flagged for re-reading page 12 at full
resolution before coding the network link model.
**Impact:** Wrong mapping would silently swap link-quality behavior across
all schedulers that are link-quality-aware (EPR Node Selection, PPO Node
Selection).
**Resolution path:** Re-extract Table 3 at high zoom; verify row correspondence
and recompute Eq.1-2 by hand against the published t_cycle/P_s/F values as a
unit-test fixture.

## A3. QFT and VQE job definitions — RESOLVED (all 5 job types now read)
**Issue:** Was blocked pending pages 21-22. Now read in full: QAOA (Eq.36-39,
Fig.11, MaxCut cost Hamiltonian), QFT (Eq.40, recursive controlled-phase
rotations, Fig.12), VQE (Eq.41, EfficientSU2 ansatz: R_Y+R_Z per qubit,
linear-nearest-neighbor CNOT entanglement, params random in [0,2π], Fig.13).
**Remaining gap:** The paper defines the *circuits* but never states, for a
given qubit count (5-15) and circuit type, what E_j (EPR/non-local demand),
R_j (QPU count) and T_j (execution time estimate) actually evaluate to —
that mapping is said to follow "the same procedure and parameters as in [7]"
(Ferrari, Bandini, Amoretti 2024, ref [7], not in our possession). This is
the real remaining blocker for the job catalogue, not the circuit defs.
**Current treatment:** Circuit definitions (A.1-A.5) are fully transcribed
into the traceability ledger; E_j/R_j/T_j derivation stays open until ref [7]
is obtained or the compilation procedure is otherwise pinned down.
**Resolution path:** Locate ref [7] ("Execution management of distributed
quantum computing jobs", 2024 IEEE QCE) for its E_j/R_j/T_j procedure, or
treat a declared proxy as an explicit `EXTENSION`/assumption per the master
prompt's Section 6 guidance.

## A4. Job catalogue construction / truncated-Poisson bounds
**Issue:** Master prompt notes the paper may omit exact truncation bounds
for the Poisson arrival distribution and the exact enumerated job catalogue
(how many distinct circuit instances per type/qubit-count exist in set
Gamma referenced in Eq. 31-32).
**Why it matters:** Needed to regenerate the authors' exact job queue traces.
**Current treatment:** Unresolved. The downloaded Zenodo archive
(`data/reference/zenodo_21060605/data/*.json`) contains the actual job
traces used to produce the paper's tables — these can be used as ground
truth input data directly, sidestepping trace-regeneration ambiguity for
regression tests, but a *fresh* 1000-slot paper-matrix run (Phase 7) still
needs the arrival/catalogue rules spelled out if we are not simply replaying
the archived traces.
**Resolution path:** CHECKED (2026-11-26) — `data/*.json` files contain only
per-scheduler, per-metric result series (`Makespan`, `SNP`, `Fairness`,
`QPU Utilization`, `Network Utilization`), one list per metric, no raw
per-job records (no qubit count, EPR demand, or arrival trace). So the
archive cannot be replayed as ground-truth input; it is only useful for
output-level regression comparison (Phase 9 / Table 4-13 cross-check), not
for resolving the job catalogue or truncation bounds. This assumption stays
open — still blocks exact trace regeneration until the catalogue/truncation
bounds are found in the paper body or cited references ([4],[6],[21]).

## A5. Zenodo record used by the master prompt was the wrong version
**Issue:** The master prompt pointed at
`https://zenodo.org/records/19108938`. The paper's actual Data Availability
DOI (`10.5281/zenodo.18802412`) resolves to a different, newer record:
`https://zenodo.org/records/21060605` (different zip size: 3,198,072 bytes
vs 2,273,813 bytes for the same filename).
**Why it matters:** Using the wrong record risks validating against
non-canonical data.
**Current treatment:** RESOLVED — downloaded and used 21060605. Its
`data/avg_summary_lambda_*.txt` numbers were spot-checked against the
paper's Table 5 (EPR, lambda=10, tau=0.5: makespan mean 38.4979s / std
18.6104s) and matched exactly.
**Resolution path:** Closed. Keep 19108938 unused; note it only so a future
session doesn't re-fetch it by mistake.

## A6. Homebrew Python is 3.14, not 3.12
**Issue:** `/opt/homebrew/bin/python3.12` does not exist; Homebrew's python3
resolves to 3.14.7. A separate Python.framework install at
`/Library/Frameworks/Python.framework/Versions/3.12` (invoked as
`/usr/local/bin/python3.12`) is 3.12.1 and already has pip 25.0.1.
**Why it matters:** Project pins Python 3.12 for SeQUeNCe compatibility.
**Current treatment:** Use `/usr/local/bin/python3.12` (the
Python.framework build) for the project venv.
**Resolution path:** `/usr/local/bin/python3.12 -m venv .venv` at repo root.
