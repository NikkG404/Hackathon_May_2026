import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COLUMN_MAP, KPI_COLUMNS
from skills.eda.eda_skill import (
    compute_overview,
    compute_campaign_activity,
    compute_channels_per_campaign,
    compute_kpi_summary,
    compute_null_counts,
    compute_kpi_over_time,
    generate_overview_insights,
    generate_activity_insights,
    generate_channel_insights,
    generate_kpi_insights,
    generate_null_insights,
)


def _bullets(points: list[str], header: str = "Key Insights"):
    st.markdown(f"**{header}**")
    st.markdown("\n".join(f"- {p}" for p in points))


def render(df: pd.DataFrame):
    st.subheader("Basic EDA — Exploratory Data Analysis")

    with st.spinner("Computing EDA metrics…"):
        overview  = compute_overview(df)
        activity  = compute_campaign_activity(df)
        channels  = compute_channels_per_campaign(df)
        kpi_summ  = compute_kpi_summary(df)
        nulls     = compute_null_counts(df)

    # ── Overview metrics ──────────────────────────────────────────────────────
    st.markdown("#### Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Start Date",        str(overview["time_period_start"].date()))
    c2.metric("End Date",          str(overview["time_period_end"].date()))
    c3.metric("Unique Campaigns",  overview["unique_campaigns"])
    c4.metric("Unique Brands",     overview["unique_brands"])
    c5.metric("Total Rows",        f"{overview['total_rows']:,}")
    _bullets(generate_overview_insights(overview))
    st.markdown("---")

    # ── Campaign activity ─────────────────────────────────────────────────────
    st.markdown("#### Campaign Activity — Active Days")
    col_most, col_least = st.columns(2)
    with col_most:
        st.markdown("**Most Active Campaigns (top 10)**")
        st.dataframe(activity.head(10), use_container_width=True, hide_index=True)
    with col_least:
        st.markdown("**Least Active Campaigns (bottom 10)**")
        st.dataframe(activity.tail(10), use_container_width=True, hide_index=True)

    fig_act = px.bar(
        activity.head(25),
        x=COLUMN_MAP["campaign_id"],
        y="Active_Days",
        title="Top 25 Campaigns by Active Days",
        color="Active_Days",
        color_continuous_scale="Blues",
    )
    fig_act.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
    st.plotly_chart(fig_act, use_container_width=True)
    _bullets(generate_activity_insights(activity))
    st.markdown("---")

    # ── Channels per campaign × brand ─────────────────────────────────────────
    if not channels.empty:
        st.markdown("#### Channels per Campaign × Brand")
        st.dataframe(channels, use_container_width=True, hide_index=True)
        _bullets(generate_channel_insights(channels))
        st.markdown("---")

    # ── KPI summary per campaign ──────────────────────────────────────────────
    st.markdown("#### KPI Summary — per Campaign (min / max / mean / median)")
    available_kpis = [c for c in KPI_COLUMNS if c in df.columns]

    if available_kpis and not kpi_summ.empty:
        kpi_tabs = st.tabs(available_kpis)
        for tab, kpi in zip(kpi_tabs, available_kpis):
            with tab:
                stat_cols = [c for c in kpi_summ.columns if c.startswith(f"{kpi}_")]
                if stat_cols:
                    display_cols = [COLUMN_MAP["campaign_id"]] + stat_cols
                    st.dataframe(
                        kpi_summ[[c for c in display_cols if c in kpi_summ.columns]],
                        use_container_width=True,
                        hide_index=True,
                    )

                # Trend chart: daily aggregate
                daily = compute_kpi_over_time(df, kpi)
                fig_trend = px.line(
                    daily,
                    x=COLUMN_MAP["date"],
                    y=kpi,
                    title=f"{kpi} — Daily Total (all campaigns)",
                    markers=False,
                )
                fig_trend.update_traces(line_color="steelblue")
                st.plotly_chart(fig_trend, use_container_width=True)
                _bullets(generate_kpi_insights(df, kpi, kpi_summ))
    st.markdown("---")

    # ── Null counts ───────────────────────────────────────────────────────────
    st.markdown("#### Null Count per Column")
    st.dataframe(nulls, use_container_width=True, hide_index=True)
    _bullets(generate_null_insights(nulls, overview["total_rows"]))
