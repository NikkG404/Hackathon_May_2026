import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from skills.correlation.correlation_skill import (
    get_numeric_columns,
    compute_correlation_matrix,
    compute_pairwise_stats,
    generate_pairwise_insights,
    generate_heatmap_insights,
)


def _bullets(points: list[str], header: str = "Key Insights"):
    st.markdown(f"**{header}**")
    st.markdown("\n".join(f"- {p}" for p in points))


def render(df: pd.DataFrame):
    st.subheader("Correlation Analysis")
    st.caption("Performs correlation analysis between any 2 selected numerical columns.")

    numeric_cols = get_numeric_columns(df)
    if len(numeric_cols) < 2:
        st.warning("At least 2 numeric KPI columns are required for correlation analysis.")
        return

    # ── Column selector ───────────────────────────────────────────────────────
    with st.expander("Select Columns", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            col1 = st.selectbox("First KPI", numeric_cols, key="corr_col1")
        with col_b:
            default_idx = 1 if len(numeric_cols) > 1 else 0
            col2 = st.selectbox("Second KPI", numeric_cols, index=default_idx, key="corr_col2")

        show_all = st.checkbox(
            "Show full correlation matrix (all numeric KPIs)", value=False, key="corr_all"
        )
        submitted = st.button("Submit", type="primary", key="corr_submit")

    if submitted:
        st.session_state["corr_done"] = True

    if not st.session_state.get("corr_done", False):
        return

    cols_to_use = numeric_cols if show_all else [col1, col2]

    with st.spinner("Computing correlations…"):
        corr_matrix = compute_correlation_matrix(df, cols_to_use)

    # ── Pairwise stats ────────────────────────────────────────────────────────
    st.markdown(f"#### `{col1}` vs `{col2}`")
    pair_stats = compute_pairwise_stats(df, col1, col2)

    m1, m2, m3 = st.columns(3)
    m1.metric("Pearson r",   str(pair_stats["r"])       if pair_stats["r"]       is not None else "N/A")
    m2.metric("p-value",     str(pair_stats["p_value"]) if pair_stats["p_value"] is not None else "N/A")
    m3.metric("Sample Size", f"{pair_stats['n']:,}")

    # Scatter plot with OLS trendline (pure NumPy — no statsmodels)
    scatter_df = df[[col1, col2]].dropna()
    m, b = np.polyfit(scatter_df[col1], scatter_df[col2], 1)
    x_line = np.array([scatter_df[col1].min(), scatter_df[col1].max()])
    y_line = m * x_line + b

    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=scatter_df[col1], y=scatter_df[col2],
        mode="markers",
        marker=dict(color="steelblue", opacity=0.55, size=6),
        name="Data",
    ))
    fig_scatter.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode="lines",
        line=dict(color="firebrick", width=2, dash="dash"),
        name="OLS Trendline",
    ))
    fig_scatter.update_layout(
        title=f"{col1} vs {col2}  (r = {pair_stats['r']})",
        xaxis_title=col1,
        yaxis_title=col2,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    _bullets(generate_pairwise_insights(pair_stats, col1, col2))
    st.markdown("---")

    # ── Heatmap ───────────────────────────────────────────────────────────────
    st.markdown(f"#### Correlation Heatmap — `{', '.join(cols_to_use)}`")
    fig_heat = px.imshow(
        corr_matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Pearson Correlation Matrix",
        aspect="auto",
    )
    fig_heat.update_layout(height=max(350, 80 * len(cols_to_use)))
    st.plotly_chart(fig_heat, use_container_width=True)
    _bullets(generate_heatmap_insights(corr_matrix))
