"""Link physics: paper Sec. 3.2.1, Eq. 1-2, Table 2-3.

Table 2/3 row correspondence verified in docs/assumptions_register.md (A2,
resolved): Bad<->Worst, Medium<->Medium, Good<->(Table 3's unlabeled 3rd
row). d is fixed at 0.1km for all link qualities (paper's Table 2 "d(km)"
column).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkEtaParams:
    """Table 2 row: eta parameters for a trapped-ion link at 0.1km."""
    eta_fc: float          # eta_FC^{ion->telecom}
    eta_det: float         # eta_det^{telecom}
    eta_penalty: float
    eta_ion: float
    alpha: float
    d_km: float


# Table 2, paper p.12, cited to [22].
LINK_QUALITIES: dict[str, LinkEtaParams] = {
    "Bad": LinkEtaParams(eta_fc=0.5, eta_det=0.75, eta_penalty=0.12, eta_ion=0.87, alpha=0.2, d_km=0.1),
    "Medium": LinkEtaParams(eta_fc=0.5, eta_det=0.75, eta_penalty=0.20, eta_ion=0.87, alpha=0.2, d_km=0.1),
    "Good": LinkEtaParams(eta_fc=0.7, eta_det=0.90, eta_penalty=0.20, eta_ion=0.87, alpha=0.2, d_km=0.1),
}


def entanglement_success_probability(p: LinkEtaParams) -> float:
    """Eq. 1: P_s(d) = (1/2) eta_penalty (eta_ion eta_FC eta_det)^2 10^{-(alpha/10)(d/2)}."""
    inner = p.eta_ion * p.eta_fc * p.eta_det
    return 0.5 * p.eta_penalty * inner**2 * 10 ** (-(p.alpha / 10) * (p.d_km / 2))


def state_delay_ns(t_cycle_ns: float, p_success: float) -> float:
    """Eq. 2: t_state = t_cycle / P_s."""
    return t_cycle_ns / p_success


# Table 3, paper p.12: t_cycle per link quality (ns), cited to [27] (Worst)
# and [22] (Good/high-quality laboratory setting).
T_CYCLE_NS: dict[str, float] = {
    "Bad": 1.8e6,     # "Worst" row
    "Medium": 1.0e6,
    "Good": 2.0e5,
}


