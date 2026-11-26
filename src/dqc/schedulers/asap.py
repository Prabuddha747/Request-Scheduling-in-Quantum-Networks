"""ASAP scheduler. Paper Algorithm 4: for the currently free nodes, scan
queued jobs in order, assigning each that currently fits and skipping
(bypassing) those that don't -- identical per-call logic to LIST (compare
list_scheduler.py). The only paper-described difference is invocation
cadence: ASAP must be re-run on every resource-release event (Table 1
Update="when nodes available"), not just at the end of a parallel group
like LIST (Update="end of parallelized job set"). That cadence is an
experiment-runner/engine concern, not something a per-call select()
can express -- so we reuse ListScheduler's logic rather than duplicate it.
"""
from __future__ import annotations

from dqc.domain import ScheduleDecision, SchedulingState
from dqc.schedulers.list_scheduler import ListScheduler


class ASAPScheduler:
    def __init__(self) -> None:
        self._list_logic = ListScheduler()

    def select(self, state: SchedulingState) -> ScheduleDecision:
        return self._list_logic.select(state)
