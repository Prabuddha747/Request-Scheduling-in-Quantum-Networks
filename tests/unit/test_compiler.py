import pytest

from dqc.compiler import circuit_two_qubit_gates, compile_job

CIRCUIT_TYPES = ["ghz", "graph", "qaoa", "qft", "vqe"]


@pytest.mark.parametrize("circuit_type", CIRCUIT_TYPES)
@pytest.mark.parametrize("n_qubits", [5, 8, 15])
@pytest.mark.parametrize("n_qpus", [1, 2, 3])
def test_compile_job_invariants(circuit_type, n_qubits, n_qpus):
    job = compile_job("j0", circuit_type, n_qubits, n_qpus, arrival_slot=0)
    total_gates = len(circuit_two_qubit_gates(circuit_type, n_qubits))
    assert 0 <= job.epr_demand <= total_gates
    assert 1 <= job.qpu_demand <= min(n_qpus, n_qubits)
    assert job.exec_time_ns >= 0
    assert job.n_qubits == n_qubits


def test_single_qpu_has_no_epr_demand():
    job = compile_job("j0", "ghz", 10, n_qpus=1, arrival_slot=0)
    assert job.epr_demand == 0
    assert job.qpu_demand == 1


def test_fully_connected_qft_has_more_epr_pressure_than_sparse_vqe():
    # QFT's interaction graph is a clique (all pairs); VQE's is a path.
    # Splitting a clique across QPUs should cost at least as many cross
    # edges as splitting a path of the same size, for the same partition count.
    qft_job = compile_job("j0", "qft", 10, n_qpus=2, arrival_slot=0)
    vqe_job = compile_job("j1", "vqe", 10, n_qpus=2, arrival_slot=0)
    assert qft_job.epr_demand >= vqe_job.epr_demand


def test_ghz_gate_pairs_are_star_from_qubit_zero():
    assert circuit_two_qubit_gates("ghz", 5) == [(0, 1), (0, 2), (0, 3), (0, 4)]


def test_unknown_circuit_type_rejected():
    with pytest.raises(ValueError):
        circuit_two_qubit_gates("bogus", 5)
