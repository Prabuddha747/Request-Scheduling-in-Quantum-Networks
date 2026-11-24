# NetSquid Access Status

Checked with `scripts/check_netsquid_access.sh` (one-shot, no retries, no credentials printed).

| Date (UTC) | Website (netsquid.org) | Package index (pypi.netsquid.org) |
|---|---|---|
| 2026-11-24T12:22Z (session check) | UNREACHABLE (TCP timeout) | UNREACHABLE (TCP timeout) |
| 2026-11-24T13:11Z (this script) | UNREACHABLE | UNREACHABLE |

**User-confirmed from their own browser (not this sandbox): also unreachable.** This rules out
a sandbox-specific network block — it's a real outage or access issue on the NetSquid side.

## How to re-check

```bash
./scripts/check_netsquid_access.sh
```

Run this by hand when you want to know if it's back — it does not retry or poll on its own,
and nothing in this project should poll it automatically either (see the PRD's rule against
repeated installation attempts).

## What's blocked by this

- Installing `netsquid`/`pydynaa` (both confirmed to require this index — neither is on public PyPI).
- Everything from the `minimal.py` smoke test onward (Phase 3 proper through Phase 10).

## What's NOT blocked (see docs/PROJECT_STATUS.md for what's been done instead)

- Source-code audit, project scaffolding, Docker environment build for the non-gated stack,
  upstream `uiiit` unit tests that don't import netsquid, and the project-owned experiment
  management / result-processing / figure-plotting framework (`src/qnr_repro/`).
