"""
Anomaly detection skill: run Z-Score, IQR, or Time Series detection across KPI columns.
Pure Python — no Streamlit imports. All rendering is handled in pages/anomaly.py.
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import KPI_COLUMNS
from utils.stats import zscore_anomalies, iqr_anomalies, timeseries_anomalies

# Maps UI label → internal method key
METHODS: dict[str, str] = {
    "Z-Score (Standard Score) Method": "zscore",
    "IQR (Interquartile Range) Method": "iqr",
    "Time Series Statistical Method":   "timeseries",
}

METHOD_LABELS = list(METHODS.keys())


def detect_anomalies(
    df: pd.DataFrame,
    kpi_col: str,
    method_label: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Run anomaly detection on a single KPI column.

    Returns:
        anomaly_df  — subset of df where anomalies were detected, with '_anomaly_score' column added.
        score_series — full-length score Series aligned to df.index.
    """
    method = METHODS.get(method_label, "zscore")
    series = df[kpi_col]

    if method == "zscore":
        mask, scores = zscore_anomalies(series)
    elif method == "iqr":
        mask, scores = iqr_anomalies(series)
    else:
        mask, scores = timeseries_anomalies(series)

    anomaly_df = df[mask].copy()
    anomaly_df["_anomaly_score"] = scores[mask].round(4)
    return anomaly_df, scores


def detect_all_kpis(
    df: pd.DataFrame,
    method_label: str,
) -> dict[str, tuple[pd.DataFrame, pd.Series]]:
    """
    Run anomaly detection for every available KPI column.

    Returns a dict keyed by KPI column name:
        { "Impressions": (anomaly_df, score_series), ... }
    """
    available = [c for c in KPI_COLUMNS if c in df.columns]
    return {kpi: detect_anomalies(df, kpi, method_label) for kpi in available}
