"""
Single source of truth for all column definitions and derived KPI formulas.

Rules:
- All skills, utils, and pages MUST import KPI formulas from this module.
- Never hardcode a KPI formula anywhere else in the codebase.
- To add or change a KPI, edit ONLY this file.
"""

import numpy as np
import pandas as pd


# ── Raw column definitions ────────────────────────────────────────────────────

COLUMN_DEFINITIONS: dict[str, dict] = {
    "Date": {
        "type": "Date",
        "definition": (
            "Calendar date of the reporting day (YYYY-MM-DD). "
            "Multiple campaigns can share the same date, reflecting simultaneous campaign activity."
        ),
    },
    "Campaign_ID": {
        "type": "Text",
        "definition": (
            "Unique identifier for each ad campaign. "
            "Format: <Brand>_<Channel_Code>_<Index> (e.g., A_DIS_01 = Brand A, Display, Campaign 1). "
            "Multiple Campaign_IDs can be active on the same date within the same Brand and Channel."
        ),
    },
    "Brand": {
        "type": "Text (Categorical)",
        "definition": (
            "Brand identifier: A, B, C, or D. "
            "Each brand manages its own set of campaigns independently."
        ),
    },
    "Channel": {
        "type": "Text (Categorical)",
        "definition": (
            "Media channel: Display, Video, OTT, Search, or Paid Social. "
            "Each channel may have 2–3 concurrent campaigns per brand."
        ),
    },
    "Objective": {
        "type": "Text (Categorical)",
        "definition": (
            "Campaign marketing objective: Awareness (broad reach), Consideration (engagement), "
            "Conversion (action-driving), Retargeting (re-engaging past visitors), "
            "Branded Search, or Non-Branded Search."
        ),
    },
    "Impressions": {
        "type": "Integer",
        "definition": (
            "Total number of times this campaign's ads were served to users on this day. "
            "If a campaign was paused, no row is recorded for that day (absence = paused/inactive)."
        ),
    },
    "Clicks": {
        "type": "Integer",
        "definition": "Total number of user clicks on this campaign's ads for the day.",
    },
    "Spend_USD": {
        "type": "Decimal (USD)",
        "definition": "Total media spend in US Dollars for this campaign on this day.",
    },
    "Conversions": {
        "type": "Decimal",
        "definition": (
            "Number of completed goal actions (e.g., sign-up, purchase, form fill) attributed "
            "to this campaign on this day. Uses a 30-day click attribution window."
        ),
    },
    "Video_Views": {
        "type": "Integer (nullable)",
        "definition": (
            "Number of video ad views (at least 30 seconds or completion). "
            "Populated for Video and OTT channels only; blank for Display, Search, and Paid Social."
        ),
    },
    "Reach": {
        "type": "Integer",
        "definition": "Estimated number of unique users exposed to this campaign's ads on this day.",
    },
    "Frequency": {
        "type": "Decimal",
        "definition": (
            "Average number of times a unique user was shown this campaign's ads on this day "
            "(Impressions ÷ Reach)."
        ),
    },
}


# ── Derived KPI definitions ───────────────────────────────────────────────────
# Each entry is the authoritative formula specification.
# compute_derived_kpis() below implements these — always keep the two in sync.

DERIVED_KPI_DEFINITIONS: dict[str, dict] = {
    "CTR": {
        "name": "Click-Through Rate",
        "formula_str": "Clicks / Impressions × 100",
        "unit": "%",
        "channels": "all",
        "definition": (
            "Ad engagement rate. Higher CTR suggests stronger creative or "
            "better audience targeting."
        ),
    },
    "CVR": {
        "name": "Conversion Rate",
        "formula_str": "Conversions / Clicks × 100",
        "unit": "%",
        "channels": "all",
        "definition": (
            "Share of clicks leading to a conversion. "
            "Reflects landing page quality and offer relevance."
        ),
    },
    "CPM": {
        "name": "Cost per Mille",
        "formula_str": "Spend_USD / Impressions × 1,000",
        "unit": "USD",
        "channels": "all",
        "definition": (
            "Cost to deliver 1,000 impressions. "
            "Core efficiency metric for awareness-objective campaigns."
        ),
    },
    "CPC": {
        "name": "Cost per Click",
        "formula_str": "Spend_USD / Clicks",
        "unit": "USD",
        "channels": "all",
        "definition": (
            "Average cost of each click. "
            "Lower CPC = more cost-efficient traffic acquisition."
        ),
    },
    "CPA": {
        "name": "Cost per Acquisition",
        "formula_str": "Spend_USD / Conversions",
        "unit": "USD",
        "channels": "all",
        "definition": (
            "Average cost per conversion. "
            "Primary efficiency KPI for performance-oriented campaigns."
        ),
    },
    "VTR": {
        "name": "View-Through Rate",
        "formula_str": "Video_Views / Impressions × 100",
        "unit": "%",
        "channels": ["Video", "OTT"],
        "definition": (
            "Proportion of impressions that resulted in a video view. "
            "Applicable to Video and OTT channels only."
        ),
    },
    # ROAS requires Avg. Order Value which is not in the dataset.
    # Formula reference only — not computed automatically.
    # "ROAS": {
    #     "name": "Return on Ad Spend",
    #     "formula_str": "(Conversions × Avg_Order_Value) / Spend_USD",
    #     "unit": "x",
    #     "channels": "all",
    #     "definition": "Revenue generated per dollar spent. Requires external AOV data.",
    # },
}

DERIVED_KPI_COLUMNS: list[str] = list(DERIVED_KPI_DEFINITIONS.keys())


# ── Compute function ──────────────────────────────────────────────────────────

def compute_derived_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all derived KPI columns to a campaign DataFrame.

    Formulas are defined exclusively in DERIVED_KPI_DEFINITIONS above.
    Division by zero or missing inputs produce NaN (safe, no errors raised).
    Returns a copy — original DataFrame is not modified.
    """
    df = df.copy()

    imp = df.get("Impressions")
    clk = df.get("Clicks")
    spd = df.get("Spend_USD")
    con = df.get("Conversions")
    vvw = df.get("Video_Views")

    # CTR = Clicks / Impressions × 100
    if imp is not None and clk is not None:
        df["CTR"] = np.where(imp > 0, clk / imp * 100, np.nan)

    # CVR = Conversions / Clicks × 100
    if clk is not None and con is not None:
        df["CVR"] = np.where(clk > 0, con / clk * 100, np.nan)

    # CPM = Spend_USD / Impressions × 1000
    if spd is not None and imp is not None:
        df["CPM"] = np.where(imp > 0, spd / imp * 1000, np.nan)

    # CPC = Spend_USD / Clicks
    if spd is not None and clk is not None:
        df["CPC"] = np.where(clk > 0, spd / clk, np.nan)

    # CPA = Spend_USD / Conversions
    if spd is not None and con is not None:
        df["CPA"] = np.where(con > 0, spd / con, np.nan)

    # VTR = Video_Views / Impressions × 100  (Video & OTT only — NaN elsewhere)
    if vvw is not None and imp is not None:
        df["VTR"] = np.where(imp > 0, vvw / imp * 100, np.nan)

    return df


def get_kpi_label(col: str) -> str:
    """Return 'Name (unit)' display label for a KPI column, falling back to the column name."""
    if col in DERIVED_KPI_DEFINITIONS:
        d = DERIVED_KPI_DEFINITIONS[col]
        return f"{d['name']} ({d['unit']})"
    return col


def get_kpi_description(col: str) -> str:
    """Return the definition string for a raw or derived KPI column."""
    if col in DERIVED_KPI_DEFINITIONS:
        return DERIVED_KPI_DEFINITIONS[col]["definition"]
    if col in COLUMN_DEFINITIONS:
        return COLUMN_DEFINITIONS[col]["definition"]
    return ""
