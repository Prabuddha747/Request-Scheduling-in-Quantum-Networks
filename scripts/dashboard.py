"""DQC Scheduler research dashboard. Run with: streamlit run scripts/dashboard.py

Presents the paper's formulas, this project's assumptions/scope labels, and
the REAL results produced by scripts/run_*.py -- reads only from
results/summary/*.csv and results/raw/*.csv, never fabricates numbers.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_DIR = ROOT / "results" / "summary"

st.set_page_config(page_title="DQC Scheduler Reproduction", layout="wide")

st.title("Distributed Quantum Computing Scheduler — Reproduction Dashboard")
st.caption(
    "Reproduction of *Advanced Scheduling Strategies for Distributed Quantum "
    "Computing Jobs* (Ni, Ferrari, Ho, Amoretti; arXiv:2602.24152v3). "
    "Every number on this page is read from a results CSV this project "
    "actually generated — nothing here is illustrative or fabricated."
)

LABEL_NOTE = (
    "**Label on every result below: `SCHEDULER_MODEL_REPRODUCTION`.** "
    "This project implements the paper's scheduling algorithms and metric "
    "definitions faithfully, but runs them on a SimPy-based engine with a "
    "custom mini-compiler for job attributes — not the authors' own Qoala/"
    "NetSquid pipeline (unavailable without NetSquid credentials). See "
    "`docs/assumptions_register.md` for every declared assumption."
)

tab_findings, tab_overview, tab_formulas, tab_results, tab_assumptions = st.tabs(
    ["Findings", "Overview", "Formulas", "Results", "Assumptions & Scope"]
)

# ---------------------------------------------------------------- Overview
with tab_overview:
    st.header("What this is")
    st.markdown(LABEL_NOTE)
    st.markdown(
        """
### Pipeline
1. **Domain model & SimPy engine** (`src/dqc/domain.py`, `engine.py`) — atomic QPU
   reservation, exactly-once completion, deterministic simulated time.
2. **Mini-compiler** (`src/dqc/compiler.py`) — turns a (circuit type, qubit count)
   into job attributes R_j/E_j/T_j by actually partitioning the circuit's
   qubit-interaction graph with METIS (ref [8]'s method), not a formula.
3. **Workload generator** (`src/dqc/workload.py`) — the 30-template job
   catalogue (5 circuit types × odd qubit counts 5-15, found in the authors'
   own `o.log`), truncated-Poisson arrivals, τ-biased job selection (Eq.31-32).
4. **Eight schedulers** (`src/dqc/schedulers/`, `src/dqc/rl/`) — FIFO, LIST,
   Resource-Priority, EPR, EPR (Node Selection), MILP, PPO (Node Selection,
   trained), ASAP — each implementing the paper's own Algorithm 1-5.
5. **Five metrics** (`src/dqc/metrics.py`) — Makespan, QPU Utilization,
   Non-Local Gate Rate, SELP, Fairness (paper Eq.12-19).

See the **Findings** tab for this project's own result charts: PPO training
curves and per-metric scheduler comparisons from the real experiment runs.
"""
    )
    st.header("Source material")
    st.markdown(
        """
- Paper: arXiv:2602.24152v3
- Ref [7]: Ferrari, Bandini, Amoretti — *Execution Management of DQC Jobs* (QCE 2024)
- Ref [8]: Ferrari, Carretta, Amoretti — *A Modular Quantum Compilation Framework
  for DQC* (IEEE TQE 2023, arXiv:2305.02969)
- Zenodo data: record 21060605 (the paper's own supplementary plots/logs),
  archived unchanged under `data/reference/zenodo_21060605/`
"""
    )

# ---------------------------------------------------------------- Formulas
with tab_formulas:
    st.header("Network & link model")
    st.latex(r"P_s(d) = \frac{1}{2}\,\eta_{penalty}\,(\eta_{ion}\,\eta_{FC}^{ion\to telecom}\,\eta_{det}^{telecom})^2 \cdot 10^{-(\alpha/10)(d/2)}")
    st.caption("Eq. 1 — entanglement generation success probability. Verified by hand-calc against Table 3 (exact match).")
    st.latex(r"t_{state} = \frac{t_{cycle}}{P_s}")
    st.caption("Eq. 2 — expected entangled-state delay.")

    st.header("Scheduling formalism")
    st.latex(r"\pi_t : \mathcal{A}_t \to 2^{\mathcal{N}}, \quad \bigcup_{j \in \mathcal{A}_t} \pi_t(j) \subseteq \mathcal{N}")
    st.caption("Eq. 3-6 — static schedule: a job-to-QPU-subset mapping respecting capacity.")

    st.header("Metrics")
    st.latex(r"M = \max_j(t_j^f) - \min_j(t_j^s)")
    st.caption("Eq. 12 — Makespan.")
    st.latex(r"U_{QPU} = \frac{\sum_j p_j q_j}{M \cdot n_{QPU}}")
    st.caption("Eq. 13 — QPU Utilization (p_j = exec time, q_j = QPUs required).")
    st.latex(r"U_g = \frac{T_{overlap}}{T_{max}}, \quad T_{overlap}=\sum_{j<k}\max(0,\min(t_j^f,t_k^f)-\max(t_j^s,t_k^s))")
    st.caption("Eq. 14-16 — Non-Local Gate Rate: a pairwise EXECUTION-TIME-OVERLAP ratio, "
               "not a literal non-local-gate counter (paper's own terminology, kept as-is).")
    st.latex(r"\mathrm{ELP}_j = \frac{e_j}{l_j}, \quad \mathrm{SELP} = \left(\prod_j \mathrm{ELP}_j\right)^{1/|\mathcal{J}|}")
    st.caption("Eq. 17-18 — Execution-Latency Performance and its geometric mean across the queue.")
    st.latex(r"f = 1 - \sigma(\mathrm{ELP})")
    st.caption("Eq. 19 — Fairness (1 minus the standard deviation of ELP across jobs).")

    st.header("MILP (Algorithm 5, Eq. 20-24)")
    st.latex(r"\min M \quad \text{s.t.} \quad M \ge (m_j+T_j)x_{j,m},\ \ \sum_m x_{j,m}=1,\ \ \sum_{j,m \le t < m+T_j} R_j x_{j,m} \le |\mathcal{N}|")
    st.caption("Time-indexed RCPSP, solved with scipy.optimize.milp (HiGHS). Brute-force verified exact on tiny instances.")

    st.header("PPO (Sec. 6.6, Eq. 25-30)")
    st.latex(r"\pi_\theta(a_j|S) = \frac{\exp(\tilde\ell_j/\kappa)}{\sum_i \exp(\tilde\ell_i/\kappa)}")
    st.caption("Eq. 26 — masked softmax action selection over job logits (κ=1).")
    st.latex(r"r = -R_{lat} + \iota R_{EPR}, \quad \iota=0.3,\ \beta=0.5,\ \gamma=0.8")
    st.caption("Eq. 29 — integrated training reward. Verified in tests against an independent hand-reconstruction.")

# ---------------------------------------------------------------- Findings
with tab_findings:
    st.header("Scheduler comparison across all 5 metrics (this project's runs)")
    matrix_path = SUMMARY_DIR / "matrix_experiment_summary.csv"
    if matrix_path.exists():
        mdf = pd.read_csv(matrix_path)
        mdf["condition"] = "λ=" + mdf["lambda"].astype(str) + ", τ=" + mdf["tau"].astype(str)
        condition = st.selectbox("Condition", sorted(mdf["condition"].unique()))
        cdf = mdf[mdf["condition"] == condition].set_index("scheduler")
        metric_cols = ["makespan_ns", "qpu_utilization", "non_local_gate_rate", "selp", "fairness"]
        for metric in metric_cols:
            st.subheader(metric)
            st.bar_chart(cdf[[metric]])
        st.caption(
            "Real output of scripts/run_matrix_experiment.py — full 30-template "
            "catalogue, heterogeneous links, trained PPO. See docs/assumptions_register.md "
            "A14/A15 for scope and known limitations of this run."
        )
    else:
        st.info("No matrix experiment results yet — run scripts/run_matrix_experiment.py.")

    st.header("PPO training curves")
    st.markdown(
        "Real per-update training logs from `scripts/train_ppo.py` "
        "(`results/raw/ppo_training_lambda_{5,10}.csv`) — reward, policy "
        "loss, value loss, entropy, and learning rate across the 100 PPO "
        "updates run for each arrival rate (see docs/assumptions_register.md A13)."
    )
    for lam in (5, 10):
        path = ROOT / "results" / "raw" / f"ppo_training_lambda_{lam}.csv"
        if path.exists():
            df = pd.read_csv(path)
            st.subheader(f"λ={lam}")
            st.line_chart(df.set_index("update")[["mean_reward", "policy_loss", "value_loss", "entropy"]])
        else:
            st.info(f"No training log found for λ={lam} yet — run scripts/train_ppo.py.")

# ---------------------------------------------------------------- Results
with tab_results:
    st.header("Real experiment results")
    available = sorted(SUMMARY_DIR.glob("*.csv")) if SUMMARY_DIR.exists() else []
    if not available:
        st.warning("No results yet. Run scripts/run_smoke_experiment.py, "
                    "run_full_catalogue_experiment.py, or run_matrix_experiment.py first.")
    else:
        choice = st.selectbox("Result set", [p.name for p in available])
        df = pd.read_csv(SUMMARY_DIR / choice)
        st.dataframe(df, use_container_width=True)

        metric_cols = [c for c in ["makespan_ns", "qpu_utilization", "non_local_gate_rate", "selp", "fairness"] if c in df.columns]
        if metric_cols and "scheduler" in df.columns:
            metric = st.selectbox("Metric to chart", metric_cols)
            if "lambda" in df.columns and "tau" in df.columns:
                df["condition"] = "λ=" + df["lambda"].astype(str) + ", τ=" + df["tau"].astype(str)
                chart_df = df.pivot_table(index="scheduler", columns="condition", values=metric)
            else:
                chart_df = df.set_index("scheduler")[[metric]]
            st.bar_chart(chart_df)

        st.caption(
            "Scope labels for this result set are documented in "
            "docs/source_traceability.csv and docs/assumptions_register.md "
            "(search for PHASE7-SMOKE / PHASE7-FULLCAT / the matrix-run entry)."
        )

# ------------------------------------------------------------ Assumptions
with tab_assumptions:
    st.header("Declared assumptions and scope limits")
    st.markdown(
        "Every number on the Results tab was produced under the assumptions "
        "below. None are hidden — each is logged with its rationale and "
        "impact in `docs/assumptions_register.md`."
    )
    assumptions_path = ROOT / "docs" / "assumptions_register.md"
    if assumptions_path.exists():
        st.markdown(assumptions_path.read_text())
    else:
        st.warning("docs/assumptions_register.md not found.")
