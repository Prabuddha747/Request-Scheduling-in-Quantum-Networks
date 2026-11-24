# Quantum Network Request Scheduling — Reproduction

Reproduction of: Cicconetti, C., Conti, M., & Passarella, A. (2021). *Request Scheduling in
Quantum Networks*. IEEE Transactions on Quantum Engineering, 2. DOI: [10.1109/TQE.2021.3090532](https://doi.org/10.1109/TQE.2021.3090532).

This repository is a reproducibility/analysis layer around the authors' own NetSquid
implementation. It does not reimplement the quantum network simulator or any scheduling
algorithm — see `docs/` for the full requirements and `vendor/netsquid` (pinned submodule)
for the simulation code itself.

## Status

See `docs/PROJECT_STATUS.md` for the current phase, `docs/REPRODUCTION_LOG.md` for the
experiment-by-experiment log, and `docs/SESSION_HANDOFF.md` for exactly what to do next.

## Structure

```
docs/           PRD, implementation plan, TRD, paper PDF, and all audit/status docs
vendor/netsquid Git submodule, pinned to tag v1.0.1 (authors' source of truth)
configs/        Declarative scenario parameters for this reproduction (see docs/TRD)
scripts/        Project-owned CLI wrappers around the upstream experiment scripts
src/qnr_repro/  Project-owned library code (manifests, result parsing, metrics, figures)
tests/          Tests for project-owned code
artifacts/      Run outputs (raw/processed ignored by git; figures/manifests curated)
```

## Clone

```
git clone --recurse-submodules <this-repo-url>
cd phdproject
git submodule status   # should show vendor/netsquid pinned at v1.0.1 / fece16a66507520a976dea31038e2e6754fbab88
```

## Environment

NetSquid 0.9.8 requires Python 3.7-era dependencies with several compiled extensions that
predate Apple Silicon wheel support. This project runs the simulator inside a `linux/amd64`
Docker container (Python 3.7) rather than natively on macOS arm64. See
`docs/DEPENDENCY_AUDIT.md` and `docs/ENVIRONMENT_SETUP.md` for the full rationale and setup
steps.

Installing the simulator requires a free NetSquid account (https://forum.netsquid.org/ucp.php?mode=register)
to access its private package index.
