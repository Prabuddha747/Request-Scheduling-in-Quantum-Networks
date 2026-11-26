import pytest

from dqc.rl.reward import epr_incentive, integrated_reward, latency_penalty


def test_latency_penalty_hand_calc():
    # 2 jobs, latencies [2, 4], exec times descending [5, 3].
    # numerator = 2+4 = 6. denominator = (2-1+1)*5 + (2-2+1)*3 = 2*5+1*3 = 13.
    r_lat = latency_penalty([2.0, 4.0], [5.0, 3.0])
    assert r_lat == pytest.approx(6 / 13)


def test_latency_penalty_empty_is_zero():
    assert latency_penalty([], []) == 0.0


def test_epr_incentive_hand_calc_single_step():
    # one step (v=0), two jobs with E_j=[2,4] in priority order o_j=0,1.
    # D_prev=0 (D_0=0, gamma term vanishes).
    # term_0 = 1/(0.5*2*(0+1)+0.8*0) = 1/1.0 = 1.0
    # term_1 = 1/(0.5*4*(1+1)+0.8*0) = 1/4.0 = 0.25
    # total_jobs = 2 -> R_EPR = (1.0+0.25)/2 = 0.625
    r_epr = epr_incentive([[2.0, 4.0]])
    assert r_epr == pytest.approx(0.625)


def test_epr_incentive_two_steps_uses_prev_max_as_d():
    # step0: E=[2], o_j=0 -> term=1/(0.5*2*1+0.8*0)=1/1=1.0; D after step0 = max([2])=2
    # step1: E=[3], o_j=0 -> term=1/(0.5*3*1+0.8*2)=1/(1.5+1.6)=1/3.1
    r_epr = epr_incentive([[2.0], [3.0]])
    expected = (1.0 + 1 / 3.1) / 2
    assert r_epr == pytest.approx(expected)


def test_integrated_reward_matches_eq29():
    assert integrated_reward(r_lat=0.5, r_epr=0.8, iota=0.3) == pytest.approx(-0.5 + 0.3 * 0.8)
