"""
EDA skill: compute exploratory statistics from campaign performance data.
Pure Python — no Streamlit imports. All rendering is handled in pages/eda.py.
"""
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COLUMN_MAP, KPI_COLUMNS


def compute_overview(df: pd.DataFrame) -> dict:
    """Return high-level dataset metrics."""
    date_col = COLUMN_MAP["date"]
    campaign_col = COLUMN_MAP["campaign_id"]
    brand_col = COLUMN_MAP["brand"]

    return {
        "time_period_start": df[date_col].min(),
        "time_period_end":   df[date_col].max(),
        "unique_campaigns":  df[campaign_col].nunique(),
        "unique_brands":     df[brand_col].nunique() if brand_col in df.columns else 0,
        "total_rows":        len(df),
    }


def compute_campaign_activity(df: pd.DataFrame) -> pd.DataFrame:
    """Return all campaigns ranked by number of active days (descending)."""
    date_col     = COLUMN_MAP["date"]
    campaign_col = COLUMN_MAP["campaign_id"]

    activity = (
        df.groupby(campaign_col)[date_col]
        .nunique()
        .reset_index()
        .rename(columns={date_col: "Active_Days"})
        .sort_values("Active_Days", ascending=False)
        .reset_index(drop=True)
    )
    return activity


def compute_channels_per_campaign(df: pd.DataFrame) -> pd.DataFrame:
    """Return unique channel count for each campaign × brand combination."""
    campaign_col = COLUMN_MAP["campaign_id"]
    brand_col    = COLUMN_MAP["brand"]
    channel_col  = COLUMN_MAP["channel"]

    if brand_col not in df.columns or channel_col not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby([campaign_col, brand_col])[channel_col]
        .nunique()
        .reset_index()
        .rename(columns={channel_col: "Unique_Channels"})
        .sort_values([brand_col, campaign_col])
        .reset_index(drop=True)
    )


def compute_kpi_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return min / max / mean / median for each KPI column, grouped by campaign."""
    campaign_col   = COLUMN_MAP["campaign_id"]
    available_kpis = [c for c in KPI_COLUMNS if c in df.columns]

    if not available_kpis:
        return pd.DataFrame()

    agg_dict = {col: ["min", "max", "mean", "median"] for col in available_kpis}
    summary  = df.groupby(campaign_col).agg(agg_dict)
    summary.columns = ["_".join(parts) for parts in summary.columns]
    return summary.reset_index()


def compute_null_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Return per-column null counts, sorted descending."""
    counts = df.isnull().sum().reset_index()
    counts.columns = ["Column", "Null_Count"]
    return counts.sort_values("Null_Count", ascending=False).reset_index(drop=True)


def compute_kpi_over_time(df: pd.DataFrame, kpi_col: str) -> pd.DataFrame:
    """Return daily aggregate (sum) of a KPI across all campaigns — for trend charts."""
    date_col = COLUMN_MAP["date"]
    daily = df.groupby(date_col)[kpi_col].sum().reset_index()
    daily.columns = [date_col, kpi_col]
    return daily.sort_values(date_col)


# ── Insight generators ────────────────────────────────────────────────────────

def generate_overview_insights(overview: dict) -> list[str]:
    start    = overview["time_period_start"]
    end      = overview["time_period_end"]
    span     = (end - start).days + 1
    avg_rows = overview["total_rows"] / max(overview["unique_campaigns"], 1)
    return [
        f"The dataset spans **{span} calendar days** from {start.date()} to {end.date()}.",
        f"**{overview['unique_campaigns']} campaigns** run across **{overview['unique_brands']} brands**, averaging **{avg_rows:.1f} daily records per campaign**.",
        f"A total of **{overview['total_rows']:,} daily data points** are available — higher row counts per campaign indicate longer or more continuously active flights.",
    ]


def generate_activity_insights(activity: pd.DataFrame) -> list[str]:
    campaign_col = COLUMN_MAP["campaign_id"]
    most      = activity.iloc[0]
    least     = activity.iloc[-1]
    avg_days  = activity["Active_Days"].mean()
    above_avg = int((activity["Active_Days"] > avg_days).sum())
    day_gap   = int(most["Active_Days"]) - int(least["Active_Days"])
    return [
        f"**{most[campaign_col]}** ran the longest with **{int(most['Active_Days'])} active days**, suggesting a sustained always-on media strategy.",
        f"**{least[campaign_col]}** was the shortest flight at **{int(least['Active_Days'])} days** — this may indicate a burst campaign, an A/B test, or an early pause.",
        f"Campaigns averaged **{avg_days:.1f} active days**; **{above_avg} of {len(activity)} campaigns** exceeded this, indicating a portfolio skewed toward longer-running efforts.",
        f"A **{day_gap}-day spread** between the busiest and shortest campaigns signals a healthy mix of always-on and short-burst strategies in the portfolio.",
    ]


def generate_channel_insights(channels: pd.DataFrame) -> list[str]:
    if channels.empty:
        return ["No channel data available to analyse."]
    campaign_col = COLUMN_MAP["campaign_id"]
    brand_col    = COLUMN_MAP["brand"]
    multi        = int((channels["Unique_Channels"] > 1).sum())
    single       = int((channels["Unique_Channels"] == 1).sum())
    max_row      = channels.loc[channels["Unique_Channels"].idxmax()]
    brand_avg    = channels.groupby(brand_col)["Unique_Channels"].mean()
    top_brand    = brand_avg.idxmax()
    return [
        f"**{multi} campaign–brand pairs** span multiple channels, reflecting a cross-channel reach strategy.",
        f"**{single} pairs** are single-channel only — these are easier to attribute but may limit overall audience reach.",
        f"**{max_row[campaign_col]}** (Brand {max_row[brand_col]}) uses **{int(max_row['Unique_Channels'])} channels**, the widest spread in the dataset.",
        f"**Brand {top_brand}** averages the most channels per campaign, indicating the broadest multi-channel investment across the portfolio.",
    ]


def generate_kpi_insights(df: pd.DataFrame, kpi: str, kpi_summ: pd.DataFrame) -> list[str]:
    campaign_col = COLUMN_MAP["campaign_id"]
    series       = df[kpi].dropna()
    if series.empty:
        return [f"No data available for **{kpi}**."]

    mean_val = series.mean()
    std_val  = series.std()
    cv       = (std_val / mean_val * 100) if mean_val != 0 else 0
    null_pct = df[kpi].isna().mean() * 100

    variability = "high" if cv > 50 else "moderate" if cv > 20 else "low"
    variability_msg = (
        "performance varies significantly across campaigns and days — investigate what drives peak days"
        if cv > 50 else
        "there is some variation worth monitoring across campaigns"
        if cv > 20 else
        "performance is stable and predictable across the portfolio"
    )

    bullets = [
        f"Daily **{kpi}** ranges from **{series.min():.2f}** to **{series.max():.2f}** with a mean of **{mean_val:.2f}**.",
        f"A coefficient of variation of **{cv:.1f}%** indicates **{variability} variability** — {variability_msg}.",
    ]

    mean_col = f"{kpi}_mean"
    if mean_col in kpi_summ.columns and not kpi_summ[mean_col].isna().all():
        idx          = kpi_summ[mean_col].idxmax()
        top_campaign = kpi_summ.loc[idx, campaign_col]
        top_val      = kpi_summ.loc[idx, mean_col]
        bullets.append(
            f"**{top_campaign}** leads with the highest average **{kpi}** ({top_val:.2f}) — a useful performance benchmark for this metric."
        )

    is_video = kpi in ("Video_Views", "VTR")
    if null_pct > 0:
        null_msg = (
            f"**{null_pct:.1f}% missing values** — expected, as `{kpi}` is only populated for Video and OTT channels."
            if is_video else
            f"**{null_pct:.1f}% missing values** detected — these likely correspond to paused campaign days or zero-activity dates."
        )
    else:
        null_msg = f"**No missing values** in `{kpi}` — complete data coverage across all campaigns and dates."
    bullets.append(null_msg)
    return bullets


def generate_null_insights(nulls: pd.DataFrame, total_rows: int) -> list[str]:
    total_cols      = len(nulls)
    cols_with_nulls = nulls[nulls["Null_Count"] > 0]
    clean_cols      = total_cols - len(cols_with_nulls)

    bullets = [f"**{clean_cols} of {total_cols} columns** are fully complete with zero missing values."]

    if not cols_with_nulls.empty:
        worst     = nulls.iloc[0]
        worst_pct = worst["Null_Count"] / total_rows * 100
        is_video  = "Video" in str(worst["Column"]) or worst["Column"] == "VTR"
        bullets.append(
            f"**{worst['Column']}** has the most nulls (**{int(worst['Null_Count']):,}** rows, {worst_pct:.1f}%) — "
            + ("expected, since it is only populated for Video and OTT channels." if is_video
               else "worth investigating for upstream data collection or pipeline gaps.")
        )
        bullets.append(
            f"**{len(cols_with_nulls)} column(s)** contain some missing data; "
            "all KPI aggregations exclude nulls automatically, so computed results remain reliable."
        )

    bullets.append(
        "Null values in derived KPIs (CTR, CVR, CPM, CPC, CPA, VTR) arise when the denominator — "
        "Impressions, Clicks, or Conversions — is zero or absent on a given day."
    )
    return bullets
