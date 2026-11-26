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
**Resolution path:** RESOLVED (partially) 2026-11-26 — obtained ref [7] in
full (Ferrari, Bandini, Amoretti, "Execution Management of Distributed
Quantum Computing Jobs," QCE 2024, pp.150-154, via INSPIRE-HEP mirror,
DOI 10.1109/QCE60285.2024.10269 — no arXiv preprint exists for it). Findings:
- **R_j** (QPUs required) is not a formula — it is a direct output of the
  quantum compiler [ref 8, Ferrari/Carretta/Amoretti 2023] that partitions
  the monolithic circuit; it is simply read off the compiled job.
- **T_j** (execution time) is computed by building one directed-acyclic
  task graph per QPU-program in the job (vertices = tasks: single-qubit
  gate, two-qubit gate, entanglement generation, readout, wait-for-peer;
  edges = per-qubit timing costs from a hardware parameter table), then
  taking the length of the longest weighted path across all the job's
  per-QPU graphs. This is a *procedure* (compile → DAG → longest-path), not
  a closed-form function of qubit count.
- **E_j** is not named in ref [7] at all. Ref [7] instead counts `N_Ri`
  (number of non-local gates in job i) for its own "quantum network
  utilization" metric (Eq. 2 there) — not identical to but the likely
  ancestor of the 2026 paper's E_j (EPR pairs), since each non-local gate
  (TeleGate/CatEnt primitive, Fig.1) consumes exactly one EPR pair.
- **Hardware-constant mismatch, still open:** ref [7]'s Table I timing
  constants (carbon/electron init, 1-/2-qubit gate durations, readout,
  entanglement-generation time ≈0.35s) are for **color-center QPUs**. The
  2026 paper's own Table 2/3 are for **trapped-ion links** and only give
  EPR/entanglement parameters (t_cycle, P_s, fidelity, t_state) — it never
  states local single-/two-qubit gate durations or qubit-init/readout
  times for its own hardware model. So "the same procedure as in [7]"
  (DAG + longest path) is now well understood, but the local-gate timing
  constants to plug into that procedure for the 2026 paper's trapped-ion
  setting are still missing from both papers.
**Remaining impact:** T_j can be computed exactly for the network
(EPR/non-local) portion of a job's critical path using Eq.1-2 + Table 2/3,
but the local-gate portion of T_j has no published constants in either
paper. Any T_j we compute must either (a) use ref [8]'s compiler output
directly if obtainable, or (b) declare placeholder local-gate timing
constants as an explicit `EXTENSION`/assumption, clearly distinguished from
the paper-sourced network-timing portion, and label resulting makespans
`SCHEDULER_MODEL_REPRODUCTION`.

**Follow-up: obtained and read ref [8] in full** 2026-11-26 (Ferrari,
Carretta, Amoretti, "A Modular Quantum Compilation Framework for
Distributed Quantum Computing," IEEE TQE vol.4, 2023, arXiv:2305.02969).
This is where ref [7]'s "quantum compiler" actually comes from. Findings:
- **R_j** (QPU count/partition): the circuit's qubit-interaction graph
  (vertices=qubits, edge weight=number of 2-qubit gates between a pair) is
  split via METIS multilevel k-way partitioning, then locally refined by a
  greedy qubit-move pass minimizing cross-partition communication cost. k
  (the number of QPUs/partitions) is a compiler *input*, not something
  derived from the circuit — so "R_j required" really means "R_j targeted."
- **E_j** (EPR pairs): produced by their Algorithm 1 ("Remote Gates
  Scheduler"), which greedily chooses TeleData vs TeleGate per non-local
  gate by comparing cost = (n_EPR/n_cov)*(delay/d̄_t) (their Eq.1 — n_EPR =
  EPR pairs consumed, n_cov = gates covered by that teleportation, delay =
  link-reuse wait time, d̄_t = mean qubit decoherence time), then counting
  consumed EPR pairs.
- **T_j** (depth/execution time): read off the final compiled circuit after
  a local SWAP-routing pass (Sec.3.3); again an output, not a formula.
- **Bottom line:** none of R_j/E_j/T_j have closed-form expressions over
  (circuit type, qubit count) in refs [7] or [8]. Getting them exactly
  requires actually running this pipeline: build qubit-interaction graph →
  METIS k-way partition + greedy refinement → Algorithm 1's per-gate
  TeleData/TeleGate cost rule → local SWAP routing → read off depth/EPR
  count/partition sizes. This is real, scoped software (not a missing
  constant), and the authors' own compiler code is not published alongside
  either paper (no code link found for refs [7]/[8]; only the top-level
  paper's own Qoala-based evaluation code is on Zenodo).
**Decision needed before Phase 2 locks in `DQCJob`:** (a) implement a scoped
version of this mini-compiler (METIS partitioning via `pymetis`/`metis`
Python bindings — not yet verified on arm64/Python 3.12 — plus Algorithm
1's cost rule) and label resulting job attributes
`SCHEDULER_MODEL_REPRODUCTION`; or (b) use a simpler declared proxy (e.g.
R_j/E_j/T_j as a function of circuit type + qubit count, calibrated by hand
against ref [8]'s reported example numbers) and label it `EXTENSION`,
trading fidelity for implementation time.
**DECIDED 2026-11-26 (user):** go with (a), the scoped mini-compiler.
**Verified 2026-11-26:** `pymetis` installs cleanly via pip on arm64/Python
3.12 (prebuilt wheel, no toolchain needed) and correctly partitions a
4-node sanity-check graph. Added to `docs/phase0_dependency_freeze.txt`.
No blocker; Phase 2 can proceed with the mini-compiler plan.

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
