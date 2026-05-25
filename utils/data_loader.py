import pandas as pd
import numpy as np
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import COLUMN_MAP, REGISTRY_COLUMN_MAP, CURRENCY_COLUMNS, REGISTRY_CURRENCY_COLUMNS, RAW_KPI_COLUMNS
from knowledge.kpi_definitions import compute_derived_kpis


def _clean_currency(series: pd.Series) -> pd.Series:
    """Strip leading $ and commas, convert to float."""
    return (
        series.astype(str)
        .str.replace(r"[$,]", "", regex=True)
        .str.strip()
        .replace("nan", np.nan)
        .pipe(pd.to_numeric, errors="coerce")
    )


def load_campaign_data(file, silent: bool = False) -> tuple[pd.DataFrame | None, str]:
    """
    Load and clean a campaign performance CSV (fact file).
    Returns (DataFrame, error_message). DataFrame is None on failure.
    When silent=True, does not call st.error — caller handles messaging.
    """
    try:
        df = pd.read_csv(file)
    except Exception as e:
        msg = f"Could not read file: {e}"
        if not silent:
            st.error(msg)
        return None, msg

    # Validate required columns
    required = list(COLUMN_MAP.values())
    missing = [c for c in required if c not in df.columns]
    if missing:
        msg = f"Missing expected columns: {missing}"
        if not silent:
            st.error(msg)
        return None, msg

    # Validate date column has parseable values
    date_col = COLUMN_MAP["date"]
    parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
    if parsed_dates.isna().all():
        msg = f"Column '{date_col}' contains no valid dates."
        if not silent:
            st.error(msg)
        return None, msg

    # Clean currency columns
    for col in CURRENCY_COLUMNS:
        if col in df.columns:
            df[col] = _clean_currency(df[col])

    df[date_col] = parsed_dates

    # Coerce raw KPI columns to numeric
    for col in RAW_KPI_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Compute derived KPIs (CTR, CVR, CPM, CPC, CPA, VTR)
    df = compute_derived_kpis(df)

    return df, ""


def load_registry_data(file, silent: bool = False) -> tuple[pd.DataFrame | None, str]:
    """
    Load and clean a campaign registry CSV (dimension file).
    Returns (DataFrame, error_message). DataFrame is None on failure.
    Handles the embedded Pause Schedule section automatically.
    """
    try:
        df = pd.read_csv(file)
    except Exception as e:
        msg = f"Could not read file: {e}"
        if not silent:
            st.error(msg)
        return None, msg

    cid_col = REGISTRY_COLUMN_MAP["campaign_id"]
    if cid_col not in df.columns:
        msg = f"Missing expected column: '{cid_col}'"
        if not silent:
            st.error(msg)
        return None, msg

    # Drop pause-schedule rows and blank separators
    df = df[
        df[cid_col].notna()
        & (df[cid_col].astype(str).str.strip() != "")
        & (~df[cid_col].astype(str).str.startswith("---"))
    ].copy()

    if df.empty:
        msg = "Registry file contains no valid campaign rows."
        if not silent:
            st.error(msg)
        return None, msg

    # Clean currency columns
    for col in REGISTRY_CURRENCY_COLUMNS:
        if col in df.columns:
            df[col] = _clean_currency(df[col])

    # Parse date columns
    for key in ("start_date", "end_date"):
        col = REGISTRY_COLUMN_MAP[key]
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df, ""
