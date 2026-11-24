# Dependency Audit

## Upstream `requirements.txt` (pinned, do not upgrade)
```
certifi==2020.6.20
cycler==0.10.0
cysignals==1.10.2        <- compiled C extension, historically fragile on Apple Silicon
Cython==0.29.21          <- compiled
kiwisolver==1.2.0        <- compiled
matplotlib==3.3.2
netsquid==0.9.8          <- compiled, closed-source wheel, registration required
numpy==1.19.2            <- compiled, pre-dates official arm64 wheels (numpy arm64 wheels start ~1.21+)
pandas==1.1.3            <- compiled
patsy==0.5.1
Pillow==8.1.1            <- compiled
pydynaa==0.3.3           <- NetSquid's discrete-event engine, compiled
pyparsing==2.4.7
python-dateutil==2.8.1
pytz==2020.1
scipy==1.5.3             <- compiled, pre-dates official arm64 wheels
six==1.15.0
statsmodels==0.12.0      <- compiled
```

**Red flag:** nearly every dependency here is a compiled C/C++ extension pinned to versions that predate Apple Silicon (arm64) wheel availability on PyPI (numpy/scipy arm64 wheels generally arrived from ~2021 onward, these pins are from 2020). `cysignals` in particular has a known history of build problems on macOS/arm64. This strongly suggests **native arm64 installation of this exact pinned stack is unlikely to succeed** without building several packages from source (requiring Xcode command-line tools, Fortran compiler for scipy, etc.) — and `netsquid==0.9.8` itself is a closed-source compiled wheel from a private index, so there is no way to build it from source if no arm64 wheel was published for it in 2020.

## This machine
- macOS 26.2 (Darwin 25.2.0), **arm64** (Apple Silicon, M1)
- System Python: 3.14.7 (arm64) — far too new; not usable for this stack regardless of architecture
- Homebrew's oldest available Python formula: `python@3.9` — **no `python@3.7` formula available via Homebrew** on this system
- No `pyenv` installed (pyenv could in principle build an old CPython from source, but building CPython 3.7 from source on current macOS/Xcode is itself known to be troublesome)
- Rosetta 2: **installed and working** (`arch -x86_64 /usr/bin/true` succeeded)
- Docker Desktop: **installed**, but daemon was not running at audit time (no `docker info` response) — needs to be started and its VM disk budget checked
- Disk free: **4.3 GB of 228 GB (98% full)** — this is the single biggest practical blocker right now, independent of Python/arm64 questions (see below)
- RAM: 8 GB total, confirmed

## Network
- GitHub: reachable
- `netsquid.org` and `pypi.netsquid.org`: **both timed out (curl exit 28)** from this sandboxed shell. This could be (a) the sandbox's network allowlist blocking an unrecognized domain, or (b) a genuine outage/DNS issue. Not yet distinguishable — needs a check from the user's own unrestricted terminal, and in any case a NetSquid forum account (https://forum.netsquid.org/ucp.php?mode=register) is required before `pip install` will work at all.

## Compatibility path assessment (feeds the PRD's decision tree)
1. **Native arm64 Python 3.7 + this exact stack**: low confidence of success — no Python 3.7 toolchain readily available on this machine, and several pinned compiled packages predate arm64 wheel availability.
2. **Rosetta 2 + x86_64 Python 3.7**: Rosetta itself works, but Homebrew does not offer an x86_64 Python 3.7 bottle either (Homebrew now only distributes 3.9+). An x86_64 Python 3.7 would need to come from python.org's official 3.7 macOS installer (which does publish Intel-only 3.7.x pkgs) run under Rosetta, or `pyenv` with an x86_64 shell. This is plausible but unverified.
3. **x86_64 Linux via Docker/VM**: Docker Desktop is already installed, which is the cleanest fit — an `x86_64` (or even arm64, since many scientific wheels for Linux have aarch64 builds unlike 2020-era macOS) Debian/Ubuntu 18.04-era container with Python 3.6.9 (the other version the upstream README explicitly tested) would most closely match the authors' own tested environment and sidesteps all macOS wheel-availability guesswork. **This is the most likely path to actually work**, pending the disk-space issue below.
4. **Colab**: explicitly de-prioritized per TRD unless independently proven compatible — not evaluated.

## Disk space — blocking concern, independent of architecture
With only 4.3 GB free:
- A Docker base image + Python 3.6/3.7 + the compiled scientific stack could easily consume 1–3 GB.
- The authors' own precomputed result archives are 272 MB + 313 MB (~585 MB) if used as a cross-check/fallback.
- Full local experiment reruns (grid: 10,000 slots × multiple configs × 50 workers' worth of output; disc: 200 replications × 1,000 slots) will generate raw JSON that is hard to size-estimate without running a scaled-down version first, but the authors' own 272 MB raw archive for their *full* run is a reasonable order-of-magnitude anchor.
- **Recommendation: free up disk space before any environment installation.** This is independent of every other decision in this audit and should be resolved first.

## No installation has been performed. No compatibility claim is made yet — this is a documentation-only audit per Phase 0/1 scope.
