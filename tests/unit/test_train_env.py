import pytest
import torch

from dqc.domain import DQCJob
from dqc.rl.network import ActorCritic
from dqc.rl.reward import epr_incentive, integrated_reward, latency_penalty
from dqc.rl.train_env import run_episode


def _job(id_, qpu_demand, epr_demand, exec_time_ns):
    return DQCJob(id=id_, circuit_type="ghz", n_qubits=5, qpu_demand=qpu_demand,
                  epr_demand=epr_demand, exec_time_ns=exec_time_ns, arrival_slot=0)


def test_episode_schedules_every_job_exactly_once():
    torch.manual_seed(0)
    jobs = [_job(f"j{i}", qpu_demand=2, epr_demand=i, exec_time_ns=10.0 + i) for i in range(5)]
    network = ActorCritic()
    transitions = run_episode(network, jobs, n_qpus=4, stochastic=True)
    assert len(transitions) == len(jobs)


def test_episode_reward_sum_matches_reward_py_pure_functions():
    """Replay the SAME wave/capacity bookkeeping run_episode uses (on the
    deterministic argmax action sequence it actually took) to independently
    reconstruct each job's (latency, wave, priority), then feed those into
    the already-tested pure functions in reward.py and confirm the episode's
    summed per-step reward equals Eq.29's integrated reward computed that way."""
    torch.manual_seed(0)
    jobs = [_job(f"j{i}", qpu_demand=2, epr_demand=(i % 3) + 1, exec_time_ns=5.0 + i) for i in range(6)]
    network = ActorCritic()
    transitions = run_episode(network, jobs, n_qpus=4, stochastic=False)
    actions = [t.action for t in transitions]

    n_qpus = 4
    remaining = list(jobs)
    free_capacity = n_qpus
    wave_jobs: list[DQCJob] = []
    cumulative_time = 0.0
    waves: list[list[float]] = []
    latencies: list[float] = []
    exec_times: list[float] = []

    for action in actions:
        feasible = [j.qpu_demand <= free_capacity for j in remaining]
        if not any(feasible):
            cumulative_time += max((j.exec_time_ns for j in wave_jobs), default=0.0)
            waves.append([j.epr_demand for j in wave_jobs])
            wave_jobs = []
            free_capacity = n_qpus
        job = remaining.pop(action)
        free_capacity -= job.qpu_demand
        wave_jobs.append(job)
        latencies.append(cumulative_time + job.exec_time_ns)
        exec_times.append(job.exec_time_ns)
    waves.append([j.epr_demand for j in wave_jobs])

    expected_r_lat = latency_penalty(latencies, sorted(exec_times, reverse=True))
    expected_r_epr = epr_incentive(waves)
    expected_total = integrated_reward(expected_r_lat, expected_r_epr)

    actual_total = sum(t.reward for t in transitions)
    assert actual_total == pytest.approx(expected_total, rel=1e-6)
