import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COLUMN_MAP, KPI_COLUMNS
from skills.anomaly.anomaly_skill import detect_all_kpis, METHOD_LABELS
from skills.insights.insights_skill import get_insights, get_recommendations


def render(df: pd.DataFrame):
    st.subheader("Anomaly Detection")

    # ── Method selector ───────────────────────────────────────────────────────
    method = st.radio(
        "Select Detection Method",
        METHOD_LABELS,
        key="anomaly_method",
        horizontal=True,
    )

    # ── Method explanation card ───────────────────────────────────────────────
    _METHOD_INFO = {
        "Z-Score (Standard Score) Method": {
            "what": (
                "Z-Score measures how many standard deviations a data point sits away from the "
                "overall mean of the series. It assumes that the metric is roughly normally distributed "
                "and that most values cluster tightly around the average."
            ),
            "how": (
                "For each daily value, the algorithm computes **z = (value − mean) / std**. "
                "Any point where the absolute z-score exceeds **3.0** is flagged as an anomaly — "
                "meaning it lies more than 3 standard deviations from the mean, a threshold that "
                "captures roughly the top 0.3% of extreme observations under a normal distribution."
            ),
            "best_for": "Metrics with a stable, bell-shaped distribution — e.g. Impressions, Reach, Spend on steady campaigns.",
        },
        "IQR (Interquartile Range) Method": {
            "what": (
                "The IQR method is a rank-based, distribution-free approach. Instead of relying on "
                "the mean and standard deviation (which are sensitive to outliers), it uses the middle "
                "50% of the data — the spread between the 25th percentile (Q1) and the 75th percentile (Q3)."
            ),
            "how": (
                "The algorithm calculates **IQR = Q3 − Q1** and defines fences at "
                "**Q1 − 1.5 × IQR** (lower) and **Q3 + 1.5 × IQR** (upper). "
                "Any value outside these fences is flagged as an anomaly. "
                "Because it ignores the tails entirely, this method is robust even when the data "
                "contains existing extreme values."
            ),
            "best_for": "Skewed or heavily tailed metrics — e.g. Conversions, CPA, CPC — where a few large values would inflate the mean.",
        },
        "Time Series Statistical Method": {
            "what": (
                "This method evaluates each day's value relative to its recent local context rather "
                "than the global dataset average. It captures the idea that what counts as 'normal' "
                "for a campaign can shift over time — e.g. spend ramps up mid-flight."
            ),
            "how": (
                "A **7-day rolling window** is applied to compute a local mean and standard deviation "
                "for each point. A value is flagged if it falls more than **2 rolling standard "
                "deviations** above or below the rolling mean — i.e. it is unusually high or low "
                "relative to its immediate neighbourhood in time, regardless of the overall campaign baseline."
            ),
            "best_for": "Metrics with trends or seasonal patterns — e.g. CTR, VTR, Frequency — where global statistics would miss local spikes.",
        },
    }

    info = _METHOD_INFO.get(method, {})
    if info:
        with st.expander(f"About: {method}", expanded=True):
            st.markdown(f"**What it is:** {info['what']}")
            st.markdown(f"**How it detects anomalies:** {info['how']}")
            st.caption(f"Best for: {info['best_for']}")

    execute = st.button("Execute Anomaly Detection", type="primary", key="anomaly_execute")

    if execute:
        with st.spinner(f"Running **{method}** on all KPIs…"):
            results = detect_all_kpis(df, method)
        st.session_state["anomaly_results"]      = results
        st.session_state["anomaly_method_used"]  = method

    results      = st.session_state.get("anomaly_results")
    method_used  = st.session_state.get("anomaly_method_used", method)

    if not results:
        return

    # ── KPI tabs ──────────────────────────────────────────────────────────────
    available_kpis = [k for k in KPI_COLUMNS if k in results]
    if not available_kpis:
        st.info("No KPI columns found in the uploaded data.")
        return

    st.markdown("---")
    tabs = st.tabs(available_kpis)

    date_col     = COLUMN_MAP["date"]
    campaign_col = COLUMN_MAP["campaign_id"]
    brand_col    = COLUMN_MAP["brand"]
    channel_col  = COLUMN_MAP["channel"]

    for tab, kpi in zip(tabs, available_kpis):
        with tab:
            anomaly_df, scores = results[kpi]
            normal_mask = ~df.index.isin(anomaly_df.index)

            # ── Time series chart ─────────────────────────────────────────────
            fig = go.Figure()

            # Normal points
            fig.add_trace(go.Scatter(
                x=df.loc[normal_mask, date_col],
                y=df.loc[normal_mask, kpi],
                mode="lines+markers",
                name="Normal",
                line=dict(color="steelblue", width=1.5),
                marker=dict(color="steelblue", size=4),
                opacity=0.75,
            ))

            # Anomaly points
            if not anomaly_df.empty:
                fig.add_trace(go.Scatter(
                    x=anomaly_df[date_col],
                    y=anomaly_df[kpi],
                    mode="markers",
                    name="Anomaly",
                    marker=dict(
                        color="red",
                        size=10,
                        symbol="circle-open",
                        line=dict(width=2.5),
                    ),
                ))

            fig.update_layout(
                title=f"{kpi} — Anomaly Detection ({method_used})",
                xaxis_title="Date",
                yaxis_title=kpi,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Summary count ─────────────────────────────────────────────────
            n_anom  = len(anomaly_df)
            n_total = len(df)
            pct     = 100 * n_anom / n_total if n_total else 0
            if n_anom:
                st.warning(f"**{n_anom} anomalies** detected in {kpi} ({pct:.1f}% of rows)")
            else:
                st.success(f"No anomalies detected in {kpi} using {method_used}.")

            # ── Anomaly table ─────────────────────────────────────────────────
            if not anomaly_df.empty:
                display_cols = [
                    c for c in [date_col, campaign_col, brand_col, channel_col, kpi, "_anomaly_score"]
                    if c in anomaly_df.columns
                ]
                st.dataframe(
                    anomaly_df[display_cols].sort_values(date_col).reset_index(drop=True),
                    use_container_width=True,
                )

            # ── Insights & Recommendations ────────────────────────────────────
            with st.expander("Insights (Descriptive Analytics)"):
                st.markdown(get_insights(anomaly_df, kpi, method_used))

            with st.expander("Recommendations (Prescriptive Analytics)"):
                st.markdown(get_recommendations(anomaly_df, kpi, method_used))
