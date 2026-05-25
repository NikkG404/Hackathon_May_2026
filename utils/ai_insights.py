import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COLUMN_MAP
from knowledge.kpi_definitions import get_kpi_label, get_kpi_description


def generate_insights(df_anomalies: pd.DataFrame, kpi_col: str, method: str) -> str:
    """Descriptive plain-English summary of detected anomalies for a given KPI."""
    kpi_label = get_kpi_label(kpi_col)
    kpi_desc  = get_kpi_description(kpi_col)

    if df_anomalies.empty:
        return (
            f"No anomalies detected in **{kpi_label}** using the **{method}**. "
            "The metric is performing within expected statistical bounds across all campaigns and dates."
        )

    date_col     = COLUMN_MAP["date"]
    campaign_col = COLUMN_MAP["campaign_id"]
    brand_col    = COLUMN_MAP["brand"]
    channel_col  = COLUMN_MAP["channel"]

    n            = len(df_anomalies)
    dates        = sorted(pd.to_datetime(df_anomalies[date_col]).dt.strftime("%Y-%m-%d").unique().tolist())
    date_summary = ", ".join(dates[:6]) + (" …" if len(dates) > 6 else "")

    campaigns = df_anomalies[campaign_col].unique().tolist() if campaign_col in df_anomalies.columns else []
    brands    = df_anomalies[brand_col].unique().tolist()    if brand_col    in df_anomalies.columns else []
    channels  = df_anomalies[channel_col].unique().tolist()  if channel_col  in df_anomalies.columns else []

    avg_val = df_anomalies[kpi_col].mean()
    max_val = df_anomalies[kpi_col].max()
    min_val = df_anomalies[kpi_col].min()

    camp_str  = ", ".join(str(c) for c in campaigns[:6]) + (" …" if len(campaigns) > 6 else "")
    brand_str = ", ".join(str(b) for b in brands)
    chan_str  = ", ".join(str(c) for c in channels)

    lines = [
        f"**{n} anomalous data point(s)** detected in **{kpi_label}** using the **{method}**.",
    ]
    if kpi_desc:
        lines += ["", f"*{kpi_desc}*"]
    lines += [
        "",
        f"- **Affected dates:** {date_summary}",
        f"- **Affected campaigns:** {camp_str}",
        f"- **Affected brands:** {brand_str}",
        f"- **Affected channels:** {chan_str}",
        f"- **Anomalous value range:** {min_val:,.2f} – {max_val:,.2f}  *(avg of anomalous points: {avg_val:,.2f})*",
        "",
        (
            "These data points deviate significantly from the expected distribution. "
            "Review the dates and campaigns listed above for unusual activity such as "
            "budget pacing changes, creative rotations, audience shifts, or external market events "
            "that may explain the deviation."
        ),
    ]
    return "\n".join(lines)


def generate_recommendations(df_anomalies: pd.DataFrame, kpi_col: str, method: str) -> str:
    """Prescriptive strategic recommendations based on detected anomalies."""
    kpi_label = get_kpi_label(kpi_col)

    if df_anomalies.empty:
        return (
            f"No action required. **{kpi_label}** is performing within normal statistical bounds. "
            "Continue monitoring and re-run detection as new data becomes available."
        )

    campaign_col = COLUMN_MAP["campaign_id"]
    n        = len(df_anomalies)
    campaigns = df_anomalies[campaign_col].unique().tolist() if campaign_col in df_anomalies.columns else []
    camp_str  = ", ".join(str(c) for c in campaigns[:4]) + (" …" if len(campaigns) > 4 else "")

    lines = [
        f"**Strategic Recommendations for {kpi_label} Anomalies ({n} flagged points):**",
        "",
        f"1. **Investigate Campaign Configuration** — Review budget pacing, bidding strategy, and targeting "
        f"settings for the affected campaigns ({camp_str}). Unexpected spikes often stem from automated bid "
        f"changes, budget cap removals, or audience expansion settings.",
        "",
        f"2. **Validate Data Quality** — Confirm that tracking pixels and conversion tags are firing "
        f"correctly on the anomalous dates. Duplicate event tracking is a common cause of inflated "
        f"conversion or click counts.",
        "",
        f"3. **Cross-Reference External Events** — Check for public holidays, competitor activity, "
        f"or market disruptions on the flagged dates. External factors can legitimately drive deviations "
        f"in {kpi_label} that are not actionable.",
        "",
        f"4. **Review Audience & Creative Changes** — If a new audience segment or creative asset "
        f"was launched around the anomaly dates, assess its direct impact on {kpi_label} performance.",
        "",
        f"5. **Set Automated Alerts** — Configure platform-level budget alerts and anomaly notifications "
        f"to catch similar deviations in real time going forward, reducing the lag between detection and response.",
    ]
    return "\n".join(lines)
