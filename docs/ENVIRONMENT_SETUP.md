# Environment Setup

## Decision: Docker `linux/amd64` container, Python 3.7

Native arm64 was ruled out (see `DEPENDENCY_AUDIT.md`): the pinned stack (numpy 1.19.2,
scipy 1.5.3, cysignals 1.10.2, pydynaa 0.3.3) predates Apple Silicon wheel availability, and
no Python 3.7 toolchain exists on this machine outside Docker. A `linux/amd64` container
under Docker Desktop's emulation on Apple Silicon was tested directly and confirmed to work.

## What's been verified (no NetSquid credentials required)

- `python:3.7-slim-buster` runs under `linux/amd64` emulation on this M1.
- Debian Buster is EOL; apt needs `archive.debian.org` instead of the default mirrors (handled
  in the `Dockerfile`).
- The full non-gated pinned stack (`numpy`, `scipy`, `pandas`, `matplotlib`, `cysignals`, etc.)
  builds and imports successfully once `build-essential`/`gfortran` are present — `cysignals`
  fails to build a wheel (a modern Cython pulled in during its own build triggers a
  `noexcept`-syntax incompatibility) but falls back to `setup.py install` successfully, which is
  sufic ient; this is a known upstream packaging quirk of `cysignals==1.10.2`, not something
  this project should "fix" by changing the pin.
- Image built and tagged `qnr-repro:py3.7`; `Dockerfile` is in the project root.

## What's NOT yet verified (needs your NetSquid credentials)

- `netsquid==0.9.8` and `pydynaa==0.3.3` are **not on public PyPI** — both come only from
  `https://pypi.netsquid.org`, which requires a free account
  (https://forum.netsquid.org/ucp.php?mode=register).
- `pypi.netsquid.org` timed out from this sandboxed environment on a raw TCP level (DNS
  resolves fine, port 443 connect times out) — this needs to be checked from your own regular
  browser/terminal before anything else here can proceed.

## How to finish the install once you have credentials and confirmed reachability

```bash
docker run --rm -it -v "$PWD":/workspace -w /workspace qnr-repro:py3.7 bash
# inside the container:
NETSQUID_USER=<your_username> NETSQUID_PASS=<your_password> scripts/install_netsquid.sh
```

This installs only `netsquid`/`pydynaa` at container runtime — never during `docker build` —
so credentials never get baked into an image layer or committed to git. If you'd rather not
pass the password as an env var, run `scripts/install_netsquid.sh` without the env vars and
`pip` will prompt interactively.

Expected final check (from inside the container):
```bash
python3 -c "import netsquid; import uiiit.qnetwork; print('imports OK')"
```

## Rebuilding the image
```bash
docker build --platform linux/amd64 -t qnr-repro:py3.7 .
```
