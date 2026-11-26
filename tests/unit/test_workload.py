import pytest

from dqc.workload import build_job_catalogue, generate_trace


def test_catalogue_has_30_templates_sorted_by_epr_demand():
    catalogue = build_job_catalogue()
    assert len(catalogue) == 30
    epr = [j.epr_demand for j in catalogue]
    assert epr == sorted(epr)


def test_same_seed_gives_identical_trace():
    t1 = generate_trace(seed=42, n_slots=5, lam=5, tau=0)
    t2 = generate_trace(seed=42, n_slots=5, lam=5, tau=0)
    ids1 = [[j.id for j in slot] for slot in t1.arrivals_by_slot]
    ids2 = [[j.id for j in slot] for slot in t2.arrivals_by_slot]
    assert ids1 == ids2


def test_different_seeds_give_different_traces():
    t1 = generate_trace(seed=1, n_slots=10, lam=5, tau=0)
    t2 = generate_trace(seed=2, n_slots=10, lam=5, tau=0)
    assert t1.arrivals_by_slot != t2.arrivals_by_slot


def test_arrivals_respect_truncation_bounds():
    trace = generate_trace(seed=0, n_slots=200, lam=5, tau=0, truncation_bounds=(0, 8))
    for slot_jobs in trace.arrivals_by_slot:
        assert 0 <= len(slot_jobs) <= 8


def test_higher_tau_biases_toward_higher_epr_jobs():
    catalogue = build_job_catalogue()
    uniform = generate_trace(seed=0, n_slots=500, lam=10, tau=0.0, catalogue=catalogue)
    biased = generate_trace(seed=0, n_slots=500, lam=10, tau=1.0, catalogue=catalogue)
    mean_epr_uniform = _mean_epr(uniform)
    mean_epr_biased = _mean_epr(biased)
    assert mean_epr_biased > mean_epr_uniform


def _mean_epr(trace):
    all_jobs = [j for slot in trace.arrivals_by_slot for j in slot]
    return sum(j.epr_demand for j in all_jobs) / len(all_jobs)


def test_jobs_carry_correct_arrival_slot():
    trace = generate_trace(seed=0, n_slots=5, lam=5, tau=0)
    for slot_idx, slot_jobs in enumerate(trace.arrivals_by_slot):
        for job in slot_jobs:
            assert job.arrival_slot == slot_idx
