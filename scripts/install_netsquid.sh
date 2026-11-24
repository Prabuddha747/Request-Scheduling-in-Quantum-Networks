#!/bin/bash
# Installs the two NetSquid-gated packages (netsquid, pydynaa) from the private
# index. Run this INSIDE the container, never at image-build time, so credentials
# never land in a Docker layer or in git history:
#
#   docker run --rm -it -v "$PWD":/workspace qnr-repro bash
#   NETSQUID_USER=you NETSQUID_PASS=yourpass scripts/install_netsquid.sh
#
# pip will also prompt interactively for username/password if the env vars are unset.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -n "${NETSQUID_USER:-}" ] && [ -n "${NETSQUID_PASS:-}" ]; then
    INDEX_URL="https://${NETSQUID_USER}:${NETSQUID_PASS}@pypi.netsquid.org"
else
    INDEX_URL="https://pypi.netsquid.org"  # pip will prompt for credentials
fi

grep -E '^(netsquid|pydynaa)' vendor/netsquid/requirements.txt \
    | pip install --no-cache-dir --extra-index-url "$INDEX_URL" -r /dev/stdin

python3 -c "import netsquid; import uiiit.qnetwork; print('NetSquid + uiiit imports OK')"
