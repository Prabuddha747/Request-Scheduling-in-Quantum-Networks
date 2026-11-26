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

## A2. Link-quality label mismatch between Table 2 and Table 3 — RESOLVED
**Issue:** Table 2 names link qualities "Bad / Medium / Good". Table 3 names
them "Worst / Medium / [third row has no text label in the PDF]".
**Resolution (2026-11-26, re-read page 12 at full resolution):** Table 3's
third row is genuinely unlabeled in the typeset PDF (not a crop/OCR
artifact), but its caption resolves the mapping explicitly: "t_cycle for
the worst-case link quality is estimated based on the experiments in [27],
whereas the lowest t_cycle for a high-quality link uses the optimistic
laboratory setting in [22]." This confirms positional correspondence:
Table 2 row 1 (Bad) ↔ Table 3 row 1 (Worst); row 2 (Medium) ↔ row 2
(Medium); row 3 (Good) ↔ row 3 (unlabeled, = "high-quality"/best link,
t_cycle=2.0e5ns, P_s=2.99e-2, F=0.95, t_state=6.67e6ns).
**Impact:** None remaining — link-quality-aware schedulers (EPR Node
Selection, PPO Node Selection) can use Table 3's 3 rows in Table 2's row
order with no ambiguity.
**Status:** Closed. Eq.1-2 hand-verification against Table 3's published
values is still a good unit-test fixture for Phase 2, but the row-mapping
question itself is settled.

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

**IMPLEMENTED 2026-11-26** — `src/dqc/compiler.py` (56 passing pytest
invariant tests). Two further simplifications made explicit here (both
already in `docs/source_traceability.csv`'s COMPILER row):
1. **TeleGate-only remote-gate handling** — every cross-partition 2-qubit
   gate costs exactly one EPR pair; the TeleData/TeleGate cost comparison
   (ref[8] Alg.1, Eq.1) is not implemented because it needs mean qubit
   decoherence time d̄_t, which neither source paper gives for trapped-ion
   hardware. This is NOT an invented shortcut — ref[8] Sec.4 itself
   evaluates a TeleGate-only configuration as one of its two tested modes.
2. **Local-gate timing constant still missing** (carried over from above):
   `LOCAL_GATE_TIME_NS = 500_000` borrowed from ref[7]'s color-center
   2-qubit gate duration, a different hardware platform than the 2026
   paper's trapped-ion links. This is the one open numeric placeholder left
   in the whole job-attribute pipeline. Upgrade path: replace if a
   trapped-ion local-gate time constant is ever sourced (neither paper nor
   their references [9],[10],[22],[27] give one for *compute* gates, only
   for entanglement generation).
All `DQCJob` instances built by this compiler are `SCHEDULER_MODEL_REPRODUCTION`,
never `PAPER_REPRODUCTION`, per master-prompt labeling rules.

## A4. Job catalogue construction / truncated-Poisson bounds — MOSTLY RESOLVED
**Issue:** Master prompt notes the paper may omit exact truncation bounds
for the Poisson arrival distribution and the exact enumerated job catalogue
(how many distinct circuit instances per type/qubit-count exist in set
Gamma referenced in Eq. 31-32).
**Why it matters:** Needed to regenerate the authors' exact job queue traces.
**Checked (2026-11-26):** `data/*.json` files contain only per-scheduler,
per-metric result series (no raw per-job records) — not useful as a replay
trace. **But** `data/reference/zenodo_21060605/data/o.log` (215,993 lines)
is the authors' actual Qoala-based run log, and it IS a goldmine:
- **Job catalogue (set Gamma) found exactly:** the log's job names are
  `{ghz,graph,qaoa,qft,vqe}_{5,7,9,11,13,15}` — i.e. all 5 circuit types ×
  6 ODD qubit counts (5,7,9,11,13,15), exactly 30 distinct job templates.
  The paper's "5-15 qubits" is not a continuous range nor all integers —
  it's specifically the odd counts in that range. This fully resolves the
  job-catalogue part of A4.
- **Total QPU count found:** node ids in the log run `node0`..`node9` — the
  network has exactly **10 QPUs**, resolving the previously-unspecified
  "QPU capacities" parameter (master prompt flagged this as unresolved).
- **Slot/condition count confirmed:** exactly 4000 `time slot:` lines =
  4 conditions (λ∈{5,10} × selection∈{random,biased}) × 1000 slots each,
  matching the paper's reported 1,000-slot evaluation per condition exactly.
- **PPO model files confirmed:** log lines show `Loading PPO model:
  ppo_weights_{rate}_r.pth` for various integer rates, confirming separate
  trained models per arrival rate as the paper states.
- **Truncated-Poisson bounds:** NOT found in this log (it shows realized
  arrivals per slot like `arrivals: 8`, not the generating distribution's
  truncation bounds) — this specific sub-item of A4 stays open.
**Remaining gap:** per-job EPR demand (E_j) is still not in this log output
(only job name + assigned node list per round), so our mini-compiler is
still the only way to get E_j/T_j; but we now know with certainty which
30 (circuit_type, qubit_count) pairs to run it on, and that the network has
10 QPUs. This removes the single biggest ambiguity blocking a fresh
1000-slot paper-matrix run in Phase 7.
**Status:** Catalogue and network size resolved; only the exact Poisson
truncation bounds remain open (low-impact: arrivals are visible per slot in
the log if we need to characterize the empirical distribution directly
rather than regenerate it from a formula).

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

## A7. Algorithm 3's link weight w(u,v) is not numerically defined
**Issue:** Algorithm 3 (node selection) minimizes "sum of pairwise link
weights" but the paper never states what w(u,v) actually is numerically —
only that it reflects link quality.
**Why it matters:** EPR (Node Selection) and PPO (Node Selection) both
depend on this to pick which QPUs to use.
**Current treatment:** `src/dqc/schedulers/node_selection.py` is weight-
agnostic (takes `link_weight: dict[(str,str), float]` as a parameter); the
caller (`SchedulingState.link_weight`) is expected to populate it. We use
`t_state_ns` (Eq.2, lower = better/faster link) as the natural "lower is
better" interpretation when building that dict.
**Impact:** This is a declared interpretation of an underspecified
function, not an invented numeric result — but it means EPR/PPO
Node-Selection outputs are `SCHEDULER_MODEL_REPRODUCTION` at best for the
node-choice *logic*, pending confirmation that t_state_ns (vs. e.g.
inverse-fidelity, or (1-fidelity)) is the right interpretation.
**Resolution path:** No further paper source found for this; stays an
open interpretation choice. Re-visit if the Zenodo archive's `o.log` file
(data/reference/zenodo_21060605/data/o.log, not yet inspected) turns out to
contain the authors' own link-weight values.

## A8. MILP scheduler's time-indexed horizon doesn't scale to raw nanoseconds — RESOLVED
**Issue:** `src/dqc/schedulers/milp.py` implements the paper's exact Eq.20-24
time-indexed RCPSP formulation, but the horizon H = sum(T_j) over integer
time steps. DQCJob.exec_time_ns values are ~1e5-1e9 ns, so a literal
nanosecond-granularity horizon would need billions of binary variables --
computationally infeasible.
**Fixed 2026-11-26:** `time_scale_ns` now defaults to `None` (auto), which
derives a scale EACH call from the current queue's own total duration,
targeting `target_horizon_steps` (default 500) discrete steps regardless of
the actual ns magnitudes. The final Assignment still carries the job's
real, unrounded exec_time_ns — only the internal search grid is coarsened.
**Verified:** solving the FULL 30-template catalogue (all queued at once,
10 QPUs) — the exact scenario that previously forced the Phase 7 smoke test
to use a restricted 5/7-qubit subset — now completes in ~3s (horizon
auto-scaled to 508 steps, status=optimal, gap=0.0).
**Remaining, smaller caveat:** the paper itself reports MILP results at
full scale (1000 slots, Tables 4/5) with no stated discretization — we
still don't know if our chosen `target_horizon_steps=500` default
resembles whatever granularity the authors effectively used. Precision vs.
tractability is now an explicit, tunable tradeoff (`target_horizon_steps`)
instead of a blocking unknown.

## A9. PPO critic needs a fixed-size input; paper gives no max queue length
**Issue:** The actor is per-job (works for any queue length), but the
critic processes "a flattened state representation through a single-hidden-
layer MLP" — a flattened |J|x4 state needs |J| fixed ahead of time, and the
paper never gives a maximum queue/job-batch size.
**Current treatment:** `src/dqc/rl/network.py` adds a `max_jobs` constructor
parameter (default 32) that zero-pads (or truncates) the state before
flattening for the critic only; the actor is unaffected since it scores
jobs independently.
**Why it matters:** `max_jobs` is an implementation necessity, not a
sourced paper value — if ever tuned, it should be set generously above the
largest realistic per-slot queue length (per `o.log`, arrivals-per-slot
examples seen were single digits at λ=5, so 32 is a comfortable margin, not
a tight fit).
**Impact:** Low — `max_jobs` only affects the critic's value estimate
(training-time bookkeeping), never the actor's job-selection behavior or
Assignment outputs.
**Resolution path:** Not resolved further; no paper source addresses this.
Flagging here is enough so a future reader doesn't mistake 32 for a sourced
constant.

## A10. Truncated-Poisson arrival bounds are not stated in the paper
**Issue:** The paper says arrivals follow a truncated Poisson distribution
with "specified lower and upper bounds" but never states what they are.
**Current treatment:** `src/dqc/workload.generate_trace()` defaults to
`[0, 3*lambda]`, a generous bound chosen so truncation rarely binds for
typical Poisson tail behavior, not derived from any source.
**Impact:** Affects the realized arrival-count distribution at the tails;
low-impact for mean-based comparisons, more relevant for any analysis of
rare high-load slots.
**Resolution path:** Not resolved; no source found. Exposed as an explicit
`truncation_bounds` parameter so a future run can override it if a source
is ever found (e.g. re-reading refs [4]/[6]/[21] in more depth).

## A11. Per-job target QPU count (compiler's k) has no paper source
**Issue:** The mini-compiler (ref[8]) needs a target partition count k as
an INPUT, but neither paper states what k the authors used per job/circuit
type.
**Current treatment:** `src/dqc/workload._default_qpu_count()` uses
`round(n_qubits/5)` capped to the network size (10) -- an arbitrary but
documented heuristic, not sourced.
**Impact:** Directly changes every job's R_j/E_j/T_j (via the compiler),
so it's the single biggest source-fidelity gap in the whole workload
pipeline. Different k choices could noticeably shift all five metrics.
**Resolution path:** Not resolved; no source found. This is the most
important remaining item if closer paper-number matching is ever wanted —
worth revisiting before treating any metric results as more than
`SCHEDULER_MODEL_REPRODUCTION`.

## A12. Phase 7 smoke run: a real cross-scheduler run, but scoped down
**What ran (2026-11-26):** `scripts/run_smoke_experiment.py` — all 8
schedulers against the SAME generated trace (paired comparison, seed=7,
10 slots, λ=3, τ=0, 4 QPUs), using only the catalogue's 5/7-qubit templates
(10 of the 30 full templates). Results: `results/raw/smoke_*.csv`,
`results/summary/smoke_experiment_summary.csv`.
**Why scoped down, explicitly:** the full 30-template catalogue includes
jobs up to ~7s of simulated exec time (qft_15 at n_qpu_network=10, or
proportionally large at smaller N); at smoke scale (10 slots, 4 QPUs) this
backlogs the queue enough to hit two already-documented complexity
ceilings: ResourcePriorityScheduler's O(2^n) combination search (A-less,
see its own ponytail comment) and MILPScheduler's time-indexed horizon
(A8). This is a REAL limitation surfaced by actually running the code, not
a hypothetical — restricting qubit_counts to (5,7) was the fix for this run.
**What this run does NOT show:** because the smoke catalogue's jobs all
have qpu_demand=1 and epr_demand=0, the schedulers barely differentiate
(FIFO/LIST/EPR/EPR-NS all produce byte-identical summary metrics here) —
there's no resource contention or EPR-pressure variation at this scope to
exercise their actual differences. MILP's lower SELP/fairness in this run
should NOT be compared to the paper's Table 10-13 trends (which show
MILP/ASAP both low) — this run's ASAP is actually the fairest, the
opposite pattern, purely an artifact of the narrow smoke scope.
**Status:** `SCHEDULER_MODEL_REPRODUCTION` / smoke-scale infrastructure
validation only. The full 1000-slot/10-QPU/full-30-template paper matrix
(λ∈{5,10}, τ∈{0,0.5}) has NOT been run — it needs: (1) a `time_scale_ns`
decision for MILP at that scale (A8), (2) a much larger `slot_duration_ns`
or a redesigned arrival/dispatch scheme to avoid backlog blowup with the
full catalogue's largest jobs, and (3) a trained PPO policy (A1) rather
than the untrained network used here. None of that is done yet.

## A6. Homebrew Python is 3.14, not 3.12
**Issue:** `/opt/homebrew/bin/python3.12` does not exist; Homebrew's python3
resolves to 3.14.7. A separate Python.framework install at
`/Library/Frameworks/Python.framework/Versions/3.12` (invoked as
`/usr/local/bin/python3.12`) is 3.12.1 and already has pip 25.0.1.
**Why it matters:** Project pins Python 3.12 for SeQUeNCe compatibility.
**Current treatment:** Use `/usr/local/bin/python3.12` (the
Python.framework build) for the project venv.
**Resolution path:** `/usr/local/bin/python3.12 -m venv .venv` at repo root.
