"""Algorithm 3 (Node-selection algorithm), shared by EPR (Node Selection)
and PPO (Node Selection). Brute-force over all K-node subsets of the
available nodes, minimizing the sum of pairwise link weights.

ponytail: O(C(n,k)) brute force, matching the paper's own pseudocode
exactly. Fine for the paper's small per-job QPU demands (jobs need a
handful of QPUs, not dozens); upgrade to a greedy/MST heuristic if node
counts ever grow large enough for this to matter.
"""
from __future__ import annotations

from itertools import combinations


def select_best_node_subset(
    available: list[str], k: int, link_weight: dict[tuple[str, str], float]
) -> tuple[str, ...]:
    if k > len(available):
        raise ValueError(f"cannot select {k} nodes from {len(available)} available")
    best_subset: tuple[str, ...] | None = None
    best_weight = float("inf")
    for subset in combinations(sorted(available), k):
        weight = sum(
            link_weight.get((a, b), link_weight.get((b, a), 0.0))
            for a, b in combinations(subset, 2)
        )
        if weight < best_weight:
            best_weight = weight
            best_subset = subset
    assert best_subset is not None
    return best_subset
