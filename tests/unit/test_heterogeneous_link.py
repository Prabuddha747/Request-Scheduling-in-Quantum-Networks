from dqc.network import LINK_QUALITIES, build_heterogeneous_link_weight


def test_heterogeneous_link_weight_covers_every_pair():
    qpus = [f"q{i}" for i in range(5)]
    weight = build_heterogeneous_link_weight(qpus, seed=0)
    assert len(weight) == 5 * 4 // 2


def test_heterogeneous_link_weight_uses_more_than_one_quality():
    qpus = [f"q{i}" for i in range(10)]
    weight = build_heterogeneous_link_weight(qpus, seed=0)
    assert len(set(weight.values())) > 1  # genuinely heterogeneous, not all one value


def test_heterogeneous_link_weight_deterministic_per_seed():
    qpus = [f"q{i}" for i in range(6)]
    w1 = build_heterogeneous_link_weight(qpus, seed=42)
    w2 = build_heterogeneous_link_weight(qpus, seed=42)
    assert w1 == w2


def test_heterogeneous_link_weight_values_match_known_t_state_values():
    # every weight must be one of the 3 known t_state values (sanity check
    # against Table 3's published numbers, same fixture as test_network.py)
    qpus = ["q0", "q1"]
    known = set()
    from dqc.network import T_CYCLE_NS, entanglement_success_probability, state_delay_ns
    for quality, params in LINK_QUALITIES.items():
        p_s = entanglement_success_probability(params)
        known.add(round(state_delay_ns(T_CYCLE_NS[quality], p_s), 2))
    weight = build_heterogeneous_link_weight(qpus, seed=0)
    for v in weight.values():
        assert round(v, 2) in known
