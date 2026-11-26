import pytest

from dqc.metrics import (
    execution_latency_performance,
    fairness,
    makespan,
    non_local_gate_rate,
    qpu_utilization,
    selp,
)


def test_makespan_hand_calc():
    # job0: [2, 10], job1: [0, 7] -> max finish=10, min start=0 -> M=10
    assert makespan([2, 0], [10, 7]) == 10


def test_qpu_utilization_hand_calc():
    # p=[4,6], q=[2,1], M=10, n_qpu=3
    # sum(p*q) = 4*2+6*1 = 14; U = 14/(10*3) = 14/30
    assert qpu_utilization([4, 6], [2, 1], makespan_value=10, n_qpu=3) == pytest.approx(14 / 30)


def test_qpu_utilization_zero_makespan_is_zero_not_divzero():
    assert qpu_utilization([1], [1], makespan_value=0, n_qpu=1) == 0.0


def test_non_local_gate_rate_full_overlap_is_one():
    # two jobs with identical [0,5] window -> full overlap
    assert non_local_gate_rate([0, 0], [5, 5]) == pytest.approx(1.0)


def test_non_local_gate_rate_no_overlap_hand_calc():
    # job0: [0,5], job1: [5,10] -> overlap=0; T_max = min(5,5)=5 -> rate=0
    assert non_local_gate_rate([0, 5], [5, 10]) == 0.0


def test_non_local_gate_rate_partial_overlap_hand_calc():
    # job0: [0,10], job1: [5,15]
    # overlap = min(10,15)-max(0,5) = 10-5 = 5
    # T_max = min(10-0, 15-5) = min(10,10) = 10
    # rate = 5/10 = 0.5
    assert non_local_gate_rate([0, 5], [10, 15]) == pytest.approx(0.5)


def test_non_local_gate_rate_single_job_edge_case_is_one():
    assert non_local_gate_rate([0], [5]) == 1.0


def test_elp_hand_calc():
    assert execution_latency_performance([4, 9], [8, 9]) == pytest.approx([0.5, 1.0])


def test_selp_hand_calc():
    # ELP = [0.5, 2.0] -> geometric mean = sqrt(0.5*2.0) = sqrt(1.0) = 1.0
    assert selp([2, 4], [4, 2]) == pytest.approx(1.0)


def test_fairness_hand_calc():
    # ELP = [0.5, 1.5] -> population stdev = 0.5 -> fairness = 1 - 0.5 = 0.5
    assert fairness([1, 3], [2, 2]) == pytest.approx(0.5)


def test_fairness_perfect_when_all_elp_equal():
    assert fairness([1, 1, 1], [1, 1, 1]) == pytest.approx(1.0)


def test_fairness_single_job_edge_case_is_one():
    assert fairness([1], [2]) == 1.0
