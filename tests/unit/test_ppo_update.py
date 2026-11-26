import pytest
import torch

from dqc.rl.ppo_update import compute_gae, ppo_clipped_loss


def test_gae_hand_calc_two_step_trajectory():
    # rewards=[1,1], values=[0,0], next_value=0, no dones, gamma=1, lam=1
    # delta_1 = 1 + 1*0*1 - 0 = 1; gae_1 = 1
    # delta_0 = 1 + 1*0*1 - 0 = 1; gae_0 = 1 + 1*1*1*1 = 2
    advantages, returns = compute_gae([1.0, 1.0], [0.0, 0.0], next_value=0.0, dones=[False, False], gamma=1.0, lam=1.0)
    assert advantages == pytest.approx([2.0, 1.0])
    assert returns == pytest.approx([2.0, 1.0])


def test_gae_resets_at_done():
    # done at t=0 should zero out bootstrap from t=1 onward's effect on t=0.
    advantages, _ = compute_gae([1.0, 1.0], [0.0, 0.0], next_value=5.0, dones=[True, False], gamma=0.99, lam=0.95)
    # delta_0 = 1 + 0.99*values[1]*mask(0) - 0 = 1 (mask=0 since done[0]=True... but mask applies to next_v which is values[1] here for t=0? )
    assert advantages[0] == pytest.approx(1.0)  # no bootstrap across the done boundary


def test_ppo_loss_clips_large_positive_ratio_with_positive_advantage():
    old_lp = torch.tensor([0.0])
    new_lp = torch.tensor([2.0])  # ratio = e^2 >> 1+eps
    advantages = torch.tensor([1.0])
    values = torch.tensor([0.0])
    returns = torch.tensor([0.0])
    entropy = torch.tensor([0.0])
    loss = ppo_clipped_loss(old_lp, new_lp, advantages, values, returns, entropy)
    # clipped surrogate caps the policy loss contribution at -(1+eps)*1 = -1.2
    assert loss.item() == pytest.approx(-1.2, abs=1e-4)


def test_ppo_update_step_changes_network_weights():
    """Training-mechanics smoke test: one PPO update step on a tiny batch
    actually moves the actor/critic weights (loss.backward + optimizer.step
    wired correctly), without claiming any trained/converged policy."""
    from dqc.rl.network import ActorCritic

    torch.manual_seed(0)
    network = ActorCritic()
    optimizer = torch.optim.Adam(network.parameters(), lr=1e-2)
    before = [p.clone() for p in network.parameters()]

    state = torch.rand(3, 4)
    logits = network.action_logits(state)
    old_log_probs = torch.log_softmax(logits, dim=-1).detach()
    value = network.value(state)

    new_logits = network.action_logits(state)
    new_log_probs = torch.log_softmax(new_logits, dim=-1)
    advantages = torch.tensor([1.0, -1.0, 0.5])
    returns = torch.tensor([1.0, 1.0, 1.0])
    entropy = -(new_log_probs.exp() * new_log_probs)

    loss = ppo_clipped_loss(old_log_probs, new_log_probs, advantages,
                             value.expand(3), returns, entropy)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    after = list(network.parameters())
    assert any(not torch.equal(b, a) for b, a in zip(before, after))
