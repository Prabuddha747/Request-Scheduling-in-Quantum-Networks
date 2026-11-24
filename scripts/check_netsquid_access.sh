#!/bin/bash
# One-shot reachability check for netsquid.org / its package index. Does NOT
# retry, does NOT install anything, does NOT print credentials. Run it by hand
# when you want to know if the outage has cleared -- not on a timer/loop.
set -uo pipefail

check() {
    local name="$1" url="$2"
    if curl -sI --max-time 8 "$url" >/dev/null 2>&1; then
        echo "$name: REACHABLE ($url)"
    else
        echo "$name: UNREACHABLE ($url)"
    fi
}

echo "=== NetSquid access check ($(date -u +%Y-%m-%dT%H:%M:%SZ)) ==="
check "Website"       "https://netsquid.org"
check "Package index" "https://pypi.netsquid.org"
echo "=== done (run again manually later -- this script does not retry) ==="
