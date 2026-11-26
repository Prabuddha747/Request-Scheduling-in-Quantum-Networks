import pytest

from dqc.network import LINK_QUALITIES, T_CYCLE_NS, entanglement_success_probability, state_delay_ns

# Table 3 published values (paper p.12); this is the regression fixture for
# ASSUMPTION A2 (Table2<->Table3 row mapping, resolved).
EXPECTED = {
    "Bad": (6.37e-3, 2.83e8),
    "Medium": (1.06e-2, 9.42e7),
    "Good": (2.99e-2, 6.67e6),
}


@pytest.mark.parametrize("quality", list(LINK_QUALITIES))
def test_eq1_eq2_match_table3(quality):
    params = LINK_QUALITIES[quality]
    p_s = entanglement_success_probability(params)
    t_state = state_delay_ns(T_CYCLE_NS[quality], p_s)
    expected_p_s, expected_t_state = EXPECTED[quality]
    assert p_s == pytest.approx(expected_p_s, rel=0.01)
    assert t_state == pytest.approx(expected_t_state, rel=0.01)
