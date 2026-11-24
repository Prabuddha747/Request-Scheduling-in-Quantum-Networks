# Matches the upstream repo's own tested environment (Python 3.7.6 on macOS / 3.6.9 on
# Ubuntu 18.04) as closely as practical, run under linux/amd64 emulation on Apple Silicon.
# Debian Buster is EOL, so apt must point at archive.debian.org -- see docs/ENVIRONMENT_SETUP.md.
FROM --platform=linux/amd64 python:3.7-slim-buster

RUN sed -i 's|deb.debian.org|archive.debian.org|g; s|security.debian.org|archive.debian.org|g' /etc/apt/sources.list \
    && apt-get -qq update \
    && apt-get -qq install -y --no-install-recommends build-essential gfortran git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# netsquid and pydynaa are NOT on public PyPI -- they require --extra-index-url
# https://pypi.netsquid.org with NetSquid forum credentials. Everything else here
# installs from public PyPI. Keeping this split means a credential-less `docker build`
# still produces a usable image for everything except the simulator itself; the two
# gated packages are installed afterward via scripts/install_netsquid.sh (never baked
# into this image, so credentials never land in an image layer or in version control).
COPY vendor/netsquid/requirements.txt /tmp/upstream-requirements.txt
RUN grep -vE '^(netsquid|pydynaa)' /tmp/upstream-requirements.txt > /tmp/requirements-public.txt \
    && pip install --no-cache-dir -r /tmp/requirements-public.txt

ENV PYTHONPATH=/workspace/vendor/netsquid
