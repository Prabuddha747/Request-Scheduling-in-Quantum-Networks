from dqc.domain import DQCJob, SchedulingState
from dqc.schedulers.asap import ASAPScheduler
from dqc.schedulers.epr import EPRNodeSelectionScheduler, EPRScheduler
from dqc.schedulers.list_scheduler import ListScheduler
from dqc.schedulers.node_selection import select_best_node_subset
from dqc.schedulers.resource_priority import ResourcePriorityScheduler


def _job(id_, qpu_demand, epr_demand=0, exec_time_ns=10.0):
    return DQCJob(id=id_, circuit_type="ghz", n_qubits=5, qpu_demand=qpu_demand,
                  epr_demand=epr_demand, exec_time_ns=exec_time_ns, arrival_slot=0)


# --- Resource-Priority ---

def test_resource_priority_maximizes_node_usage_over_arrival_order():
    # j0 (arrives first) alone uses 1 of 4 nodes; {j1, j2} together use all 4
    # -- Resource-Priority must prefer the strictly higher-utilization combo
    # even though j0 is first in arrival order (unlike FIFO).
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2", "q3"}),
        queued_jobs=(_job("j0", 1), _job("j1", 2), _job("j2", 2)),
    )
    decision = ResourcePriorityScheduler().select(state)
    assert {a.job_id for a in decision.assignments} == {"j1", "j2"}


def test_resource_priority_tie_break_prefers_shorter_total_time():
    # Both combos use all 2 nodes; {j0} alone (qpu=2, time=100) vs {j1,j2}
    # (qpu=1+1=2, time=1+1=2) -- same total node usage, pick the shorter one.
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0", "q1"}),
        queued_jobs=(_job("j0", 2, exec_time_ns=100), _job("j1", 1, exec_time_ns=1), _job("j2", 1, exec_time_ns=1)),
    )
    decision = ResourcePriorityScheduler().select(state)
    assert {a.job_id for a in decision.assignments} == {"j1", "j2"}


# --- EPR ---

def test_epr_orders_by_epr_demand_not_arrival():
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0"}),
        queued_jobs=(_job("j0", 1, epr_demand=5), _job("j1", 1, epr_demand=1)),
    )
    decision = EPRScheduler().select(state)
    assert [a.job_id for a in decision.assignments] == ["j1"]


def test_epr_stops_at_first_non_fitting_job_like_fifo():
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2"}),
        queued_jobs=(_job("j0", 2, epr_demand=1), _job("j1", 2, epr_demand=2), _job("j2", 1, epr_demand=3)),
    )
    decision = EPRScheduler().select(state)
    assert [a.job_id for a in decision.assignments] == ["j0"]


# --- Node selection (Algorithm 3) ---

def test_select_best_node_subset_minimizes_pairwise_weight():
    weights = {("q0", "q1"): 10.0, ("q0", "q2"): 1.0, ("q1", "q2"): 1.0}
    chosen = select_best_node_subset(["q0", "q1", "q2"], 2, weights)
    assert set(chosen) == {"q0", "q2"} or set(chosen) == {"q1", "q2"}


def test_epr_node_selection_picks_best_linked_pair():
    weights = {("q0", "q1"): 10.0, ("q0", "q2"): 1.0, ("q1", "q2"): 1.0}
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2"}),
        queued_jobs=(_job("j0", 2, epr_demand=1),),
        link_weight=weights,
    )
    decision = EPRNodeSelectionScheduler().select(state)
    assert set(decision.assignments[0].qpu_ids) in ({"q0", "q2"}, {"q1", "q2"})


# --- ASAP ---

def test_asap_bypasses_like_list():
    state = SchedulingState(
        time_ns=0, free_qpu_ids=frozenset({"q0", "q1", "q2"}),
        queued_jobs=(_job("j0", 2), _job("j1", 2), _job("j2", 1)),
    )
    asap_decision = ASAPScheduler().select(state)
    list_decision = ListScheduler().select(state)
    assert {a.job_id for a in asap_decision.assignments} == {a.job_id for a in list_decision.assignments}
