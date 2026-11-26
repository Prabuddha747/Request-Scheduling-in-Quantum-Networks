import torch

from dqc.domain import DQCJob, SchedulingState
from dqc.rl.network import ActorCritic
from dqc.rl.ppo_scheduler import PPOScheduler, masked_softmax


def _job(id_, qpu_demand, exec_time_ns=10.0, epr_demand=0):
    return DQCJob(id=id_, circuit_type="ghz", n_qubits=5, qpu_demand=qpu_demand,
                  epr_demand=epr_demand, exec_time_ns=exec_time_ns, arrival_slot=0)


def test_masked_softmax_assigns_zero_probability_to_infeasible_actions():
    logits = torch.tensor([10.0, 10.0, 10.0])  # all equal, would tie without masking
    mask = torch.tensor([True, False, True])
    probs = masked_softmax(logits, mask)
    assert probs[1].item() == 0.0
    assert probs[0].item() > 0 and probs[2].item() > 0


def test_ppo_scheduler_never_selects_job_that_does_not_fit():
    torch.manual_seed(0)
    network = ActorCritic()
    scheduler = PPOScheduler(network, deterministic=True)
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0"}),
        queued_jobs=(_job("too_big", qpu_demand=5), _job("fits", qpu_demand=1)),
    )
    decision = scheduler.select(state)
    assert [a.job_id for a in decision.assignments] == ["fits"]


def test_ppo_scheduler_respects_atomic_capacity_across_multiple_picks():
    torch.manual_seed(0)
    network = ActorCritic()
    scheduler = PPOScheduler(network, deterministic=True)
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0", "q1"}),
        queued_jobs=(_job("j0", qpu_demand=1), _job("j1", qpu_demand=1), _job("j2", qpu_demand=1)),
    )
    decision = scheduler.select(state)
    used = [q for a in decision.assignments for q in a.qpu_ids]
    assert len(used) == len(set(used)) == 2  # exactly 2 of the 3 jobs fit, no double-booking
