from dqc.rl.train import train


def test_train_runs_a_few_updates_and_logs_sane_values(monkeypatch):
    import dqc.rl.train as train_mod
    monkeypatch.setattr(train_mod, "BUFFER_SIZE", 64)  # keep the smoke test fast
    monkeypatch.setattr(train_mod, "MINIBATCH_SIZE", 16)

    result = train(lam=5, n_updates=2, n_qpu=4, seed=0)

    assert len(result.logs) == 2
    for log in result.logs:
        assert log.lr <= 1e-3
        assert log.wall_clock_s >= 0
        assert log.entropy >= 0  # entropy of a softmax distribution is non-negative
    assert result.logs[1].lr < result.logs[0].lr  # cosine schedule is decreasing
    assert result.peak_rss_mb > 0
