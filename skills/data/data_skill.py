"""
Data ingestion & validation skill.
Provides a clean interface for loading, validating, and merging the two CSV inputs.
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.data_loader import load_campaign_data, load_registry_data
from config import COLUMN_MAP, REGISTRY_COLUMN_MAP


def ingest_campaign_data(uploaded_file) -> pd.DataFrame | None:
    """Load, clean, and return the campaign performance DataFrame (fact file)."""
    return load_campaign_data(uploaded_file)


def ingest_registry_data(uploaded_file) -> pd.DataFrame | None:
    """Load, clean, and return the campaign registry DataFrame (dimension file)."""
    return load_registry_data(uploaded_file)


def merge_campaign_with_registry(
    campaign_df: pd.DataFrame,
    registry_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Left-join campaign performance data with registry metadata on Campaign_ID.
    Registry columns added: Start_Date, End_Date, Budget_USD.
    """
    cid_campaign = COLUMN_MAP["campaign_id"]
    cid_registry = REGISTRY_COLUMN_MAP["campaign_id"]

    registry_extra_cols = [
        REGISTRY_COLUMN_MAP["start_date"],
        REGISTRY_COLUMN_MAP["end_date"],
        REGISTRY_COLUMN_MAP["budget"],
    ]
    keep_cols = [cid_registry] + [c for c in registry_extra_cols if c in registry_df.columns]

    merged = campaign_df.merge(
        registry_df[keep_cols],
        left_on=cid_campaign,
        right_on=cid_registry,
        how="left",
    )
    # Drop duplicate join key column when names differ
    if cid_registry != cid_campaign and cid_registry in merged.columns:
        merged = merged.drop(columns=[cid_registry])

    return merged


def validate_columns(df: pd.DataFrame, required_cols: list[str]) -> tuple[bool, list[str]]:
    """Return (is_valid, missing_columns)."""
    missing = [c for c in required_cols if c not in df.columns]
    return len(missing) == 0, missing
