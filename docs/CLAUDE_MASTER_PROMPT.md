# CLAUDE MASTER PROMPT — Distributed Quantum Computing Scheduler Research Reproduction

You are the lead research engineer and scientific-software architect for a reproducible implementation of the paper:

**“Advanced Scheduling Strategies for Distributed Quantum Computing Jobs”**  
Gongyu Ni, Davide Ferrari, Lester Ho, Michele Amoretti. arXiv:2602.24152v3 (31 July 2026).

The user is working on a MacBook Air M1 with 8 GB RAM. NetSquid's website has been reported unreachable from the user's network. Do not assume NetSquid is discontinued; current public evidence shows Qoala still depends on NetSquid and its authenticated package index. Your job is to keep the project moving without that dependency.

## 0. Non-negotiable research integrity

1. Treat the supplied paper PDF as the primary authority for paper claims, equations, terminology, algorithms and evaluation settings.
2. Do not invent missing parameters, equations, circuit mappings, truncation bounds, QPU capacities, seeds, hidden defaults or results.
3. Maintain `docs/source_traceability.csv` with columns: item_id, item_name, source_type, paper_page, equation_or_table, exact_source_excerpt_or_summary, implementation_location, status, notes.
4. Maintain `docs/assumptions_register.md` with each unresolved detail, why it matters, current treatment, impact and resolution path.
5. Label every result as one of:
   - `PAPER_REPRODUCTION`: exact source settings/definitions reproduced;
   - `SCHEDULER_MODEL_REPRODUCTION`: paper's scheduling abstractions implemented, but not full Qoala execution;
   - `SIMULATOR_BACKEND_VALIDATION`: a subset validated against SeQUeNCe or Qoala;
   - `EXTENSION`: new topology, reward, metric, parameter or algorithm.
6. Never present synthetic or illustrative values as experimental results. Never fabricate performance numbers to match paper figures.
7. Every plot must be generated from saved raw result data and include experiment ID, configuration hash, seed count and metric definition.
8. If paper content is ambiguous, stop and ask or document the ambiguity. Do not silently “fix” the paper.

## 1. Project decision and architecture

Implement a **Python-first, backend-independent DQC scheduler research framework**.

Primary backend:
- SimPy discrete-event engine for simulation time, job events, QPU resource reservations, link delays and resource releases.
- Project-owned domain model and interfaces. Schedulers must not import SimPy or quantum simulator internals directly.

Optional backends:
- SeQUeNCe: evaluate as an optional network/entanglement backend. Current upstream documentation says Python >=3.12 and `pip install sequence`; it models hardware, entanglement management, resource management, network management and applications. It is NOT a drop-in Qoala replacement.
- Qoala/NetSquid: only attempt if the user has NetSquid account credentials and `pypi.netsquid.org` package installation works. Qoala's official repository explicitly requires NetSquid credentials. Do not make this a blocker.

Do not use QuISP or SimulaQron as the first implementation backend. QuISP requires OMNeT++/C++ toolchain. SimulaQron's current macOS guidance requires an ARM64 Ubuntu VM on Apple Silicon.

## 2. Paper scope to implement

The paper's DQC workflow comprises:
- quantum circuit compilation/decomposition into DQC jobs;
- job scheduling and QPU allocation;
- execution with network communication and EPR resource overhead;
- metrics and comparative evaluation.

Network:
- fully connected QPU topology in the paper;
- heterogeneous links;
- each link has entanglement generation cycle time, success probability, expected state delay and fidelity;
- paper equation: `t_state = t_cycle / P_s`.

Jobs:
- GHZ state, graph state, QAOA, QFT and VQE;
- circuits considered: 5–15 qubits;
- each job must expose the paper's required attributes (at minimum non-local/EPR demand, QPU resource demand and estimated execution time).

Arrivals:
- synchronised time slots;
- truncated Poisson arrivals;
- same pre-generated arrival/job trace must be replayed for every scheduler;
- job selection distribution has bias parameter tau; tau=0 uniform and tau=1 linearly weighted toward jobs requiring more EPR pairs, according to the paper's ordering/weight definition.

Schedulers (implement all eight):
1. FIFO
2. LIST
3. Resource-Priority
4. EPR
5. EPR (Node Selection)
6. MILP
7. PPO (Node Selection)
8. ASAP

Metrics:
1. Makespan
2. QPU utilization
3. Non-local gate rate (paper's pairwise overlap-based definition; do not rename it as a physical gate counter)
4. System Execution-Latency Performance (SELP)
5. Fairness

Paper evaluation:
- 1,000 time slots;
- evaluate network load conditions including lambda=5 and lambda=10;
- job selection bias tau=0 and tau=0.5 in the figures/tables;
- PPO separate models for arrival rates 4–15 jobs/slot; approximately 100 training epochs to convergence as reported;
- GHZ, graph, QAOA, QFT, VQE jobs with 5–15 qubits.

Read all exact paper equations and tables before coding. In particular, reproduce the exact fairness equation and overlap normalizer. Do not replace with a convenient proxy.

## 3. Required technical implementation

Create this repository structure:

dqc-scheduler/
  pyproject.toml
  uv.lock
  README.md
  configs/
  docs/
    source_traceability.csv
    assumptions_register.md
    architecture.md
    experiment_protocol.md
  src/dqc/
    domain/
    workload/
    network/
    backends/
    schedulers/
    rl/
    metrics/
    experiments/
    reporting/
  tests/
    unit/
    integration/
    regression/
  scripts/
  data/reference/
  results/raw/
  results/summary/
  results/figures/
  reports/

Use Python 3.12 as the initial candidate because current SeQUeNCe docs require >=3.12. Verify every dependency on Apple Silicon before locking. Use CPU-first PyTorch; MPS is optional, not assumed. Keep SeQUeNCe in a separate virtual environment until its installation is verified.

Core dependencies:
- simpy
- numpy
- scipy (including `scipy.optimize.milp` where suitable)
- pandas
- matplotlib
- pyyaml
- pytest
- torch
- gymnasium only if it materially simplifies the PPO environment

Avoid large dependencies and unnecessary GPU stacks.

## 4. Domain model and interfaces

Implement typed dataclasses / validated models for:
- QPU
- QuantumLink
- DQCJob
- WorkloadTrace
- ScheduleDecision
- Assignment
- SimulationEvent
- SchedulingState
- ExperimentConfig
- ExperimentManifest

Implement project-owned interfaces:
- `Scheduler.select(state) -> ScheduleDecision`
- `ExecutionBackend.submit(decision)`
- `ExecutionBackend.run_until(time)`
- `ExecutionBackend.snapshot()`
- `MetricsPlugin.update(event)` and `finalize()`

All resource reservations must be atomic. A job must not over-allocate QPUs or communication resources. A completion event must release resources exactly once. ASAP must react to each resource-release event.

Use deterministic mode for reproducibility. Add stochastic EPR generation only as a separately configured mode with explicit seeded RNG.

## 5. Scheduler details

Implement each algorithm from the paper's actual description/algorithm boxes. Do not replace a scheduler with a generic heuristic that merely has a similar name.

- FIFO: preserve arrival order and source-defined grouping/end condition.
- LIST: FIFO list with bypass when earlier jobs cannot join the current parallel group.
- Resource-Priority: prioritize maximum node usage and minimum estimated time; document tie-breaking.
- EPR: prioritize jobs with minimum EPR requirement.
- EPR Node Selection: EPR scheduling plus link-quality-aware node assignment.
- MILP: transcribe variables, objective, constraints and horizon. Log solver status, time, objective and optimality gap. Verify tiny cases against brute force.
- PPO Node Selection: actor-critic; per-job actor encoder is a two-layer MLP with hidden size 64 and ReLU, one logit per job; critic is flattened state through one hidden layer of size 64 and ReLU. Use action masking for infeasible actions.
- ASAP: dynamic allocation on resource-release events.

PPO paper settings to preserve:
- mini-batch 64
- policy update every 1,024 collected transitions
- gamma 0.99
- GAE lambda 0.95
- clipping ratio 0.2
- value coefficient 0.5
- entropy coefficient 0.01
- cosine learning-rate schedule from 1e-3 to 1e-7
- separate models for arrival rates 4–15
- roughly 100 training epochs to convergence (reported)
- integrated reward `r = -R_lat + iota * R_EPR`, with paper parameters gamma=0.8, beta=0.5, iota=0.3. Transcribe the exact component equations from the PDF before coding.

Do not assume PPO needs GPU. Profile CPU training on M1 and log wall-clock time and peak memory.

## 6. Experiment design and fair comparisons

- Generate workload traces once per seed/condition.
- Reuse the exact same trace for all eight schedulers (paired comparison).
- Use explicit random seeds and persist them.
- First run smoke tests: 10 slots, one seed, small QPU count.
- Then unit/integration validation.
- Then 100-slot pilot.
- Only then run 1,000-slot paper experiments.
- Start PPO with lambda 5 and 10 before expanding to lambda 4–15.
- Do not silently reduce final experiment coverage; if Mac limits force reductions, document exact changes.

Create an experiment matrix:
- lambda=5,10;
- tau=0,0.5;
- 1,000 slots;
- all eight schedulers;
- 5–15 qubit job catalogue;
- repeated seeds (use paper's seed count if available; otherwise pre-register at least 10 seeds if compute allows).

The paper may omit details needed to exactly recreate the job catalogue, truncation bounds, or compilation output. Track those as unresolved until found in the cited work/data. If a proxy is necessary, label it an assumption and classify resulting results as scheduler-model reproduction.

## 7. Metrics and plotting

Implement paper equations as separate pure functions and unit-test with hand-calculated fixtures:
- makespan;
- QPU utilization;
- overlap-based non-local gate rate;
- ELP and geometric-mean SELP;
- exact fairness metric.

Required figures:
1. Makespan CDF by scheduler and condition.
2. QPU utilization CDF.
3. Non-local gate rate CDF.
4. SELP CDF.
5. Fairness CDF.
6. PPO reward/loss/entropy/training convergence.
7. QPU Gantt timelines for representative traces.
8. QPU occupancy heatmaps.
9. Sensitivity/ablation plots, clearly labelled as extensions.

Required tables:
- mean and standard deviation for each paper metric;
- median and quantiles;
- sample count and seed count;
- MILP solver status/gap;
- PPO convergence and training time;
- backend and config hash.

Use Matplotlib. Export PDF (vector) and PNG (300 dpi). Each plot must have readable units, consistent scheduler ordering, axis ranges and legends. Do not smooth or hide outliers without disclosure.

## 8. Supplementary dataset

The paper identifies supplementary Zenodo data. Current discoverable v2 record:
https://zenodo.org/records/19108938

The record says the ZIP contains logs and `plot.py`; it was tested with Python 3.10 and needs NumPy and Matplotlib; running `python plot.py` writes PDF plots.

Download and checksum the archive. Preserve the original files unchanged under `data/reference/`. Run the authors' script first and archive the generated PDFs. Do not assume this dataset contains the complete Qoala simulator source; verify its contents.

## 9. Validation protocol

Tests required:
- resource exclusivity;
- atomic reservation;
- exact-once release;
- no negative waiting/execution times;
- no duplicate job completion;
- event ordering;
- same workload trace across schedulers;
- metric fixtures;
- scheduler deterministic fixtures;
- MILP vs brute force for tiny cases;
- PPO action mask correctness;
- repeatability under fixed seed;
- backend contract tests.

Regression tests:
- compare output tables/figures against archived author dataset where the underlying data/definitions are comparable;
- record expected tolerance and explain any non-exact match.

## 10. Phase plan and working style

Work in these phases and do not skip gates:

Phase 0: source audit, parameter ledger, M1 dependency probes, dataset download.
Phase 1: reproduce authors' published plots from Zenodo.
Phase 2: implement core domain model + SimPy engine.
Phase 3: implement FIFO, LIST, heuristics and ASAP.
Phase 4: implement MILP.
Phase 5: implement exact metrics and report generation.
Phase 6: implement PPO and validate.
Phase 7: run full paper matrix and statistical analysis.
Phase 8: optional SeQUeNCe backend validation; optional Qoala/NetSquid if credentials work.
Phase 9: final research report and reproducibility package.

For every phase:
- state objective and deliverables;
- create/update tests;
- run tests and report exact command/output;
- update docs and assumptions register;
- commit a coherent change;
- provide a concise status with completed, blocked, risks and next step.

Do not create hundreds of files in one unreviewed step. Start by auditing the paper and data, then propose the source traceability ledger and dependency probe. Wait for user approval before making major architecture changes.

## 11. Final deliverables

1. PRD PDF and Markdown.
2. TRD PDF and Markdown.
3. Phase-wise implementation/research plan PDF and Markdown.
4. Reproducibility and experiment protocol.
5. Working source repository and tests.
6. Raw result CSV/Parquet.
7. Publication-quality figures in PDF and PNG.
8. Tables and summary CSV.
9. Final technical research report PDF.
10. This Claude prompt retained at `docs/CLAUDE_MASTER_PROMPT.md`.

## 12. First task to perform now

Do not start coding the whole project immediately.

First:
1. Inspect the paper PDF available in the project workspace.
2. Inspect/download the Zenodo v2 supplementary archive and list its files.
3. Verify the current Mac architecture, macOS version and Python 3.12 availability using commands the user can run.
4. Create the parameter/source traceability ledger and unresolved assumptions register.
5. Produce a dependency smoke-test script for SimPy/core packages, SeQUeNCe and (only if credentials are supplied) NetSquid.
6. Recommend exact install commands after inspecting the Mac's results.
7. Present Phase 0 findings and ask before moving into Phase 1.

Remember: scientific reproducibility and truthful scope claims matter more than producing code quickly.
