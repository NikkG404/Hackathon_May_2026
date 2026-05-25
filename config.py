# config.py
# Edit column name mappings here if your CSV headers differ.
# KPI formulas and derived KPI definitions live exclusively in knowledge/kpi_definitions.py.

from knowledge.kpi_definitions import DERIVED_KPI_COLUMNS  # noqa: E402

# --- Campaign Performance Data (fact file) column mappings ---
# Keys are internal identifiers; values are the exact CSV column headers.
COLUMN_MAP = {
    "date":          "Date",
    "campaign_id":   "Campaign_ID",
    "brand":         "Brand",
    "channel":       "Channel",
    "objective":     "Objective",
    "impressions":   "Impressions",
    "clicks":        "Clicks",
    "spend":         "Spend_USD",
    "conversions":   "Conversions",
    "video_views":   "Video_Views",
    "reach":         "Reach",
    "frequency":     "Frequency",
}

# --- Campaign Registry (dimension file) column mappings ---
REGISTRY_COLUMN_MAP = {
    "campaign_id":  "Campaign_ID",
    "brand":        "Brand",
    "channel":      "Channel",
    "objective":    "Objective",
    "start_date":   "Start_Date",
    "end_date":     "End_Date",
    "budget":       "Budget_USD",
}

# Raw KPI columns (directly from CSV).
RAW_KPI_COLUMNS = [
    "Impressions",
    "Clicks",
    "Spend_USD",
    "Conversions",
    "Video_Views",
    "Reach",
    "Frequency",
]

# Full KPI list = raw + derived (CTR, CVR, CPM, CPC, CPA, VTR).
# Derived columns are computed on load by knowledge.kpi_definitions.compute_derived_kpis().
# All EDA summaries, correlation dropdowns, and anomaly detection tabs use this list.
KPI_COLUMNS = RAW_KPI_COLUMNS + DERIVED_KPI_COLUMNS

# Columns whose values are formatted as "$X,XXX.XX" — stripped of "$" and "," on load.
CURRENCY_COLUMNS = ["Spend_USD"]
REGISTRY_CURRENCY_COLUMNS = ["Budget_USD"]

# --- Anomaly detection thresholds ---
ANOMALY_Z_THRESHOLD            = 3.0
ANOMALY_IQR_MULTIPLIER         = 1.5
ANOMALY_ROLLING_WINDOW         = 7
ANOMALY_ROLLING_STD_MULTIPLIER = 2.0
