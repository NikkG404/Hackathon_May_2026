"""
Insights skill: generate descriptive and prescriptive text from anomaly results.
Thin wrapper over utils/ai_insights.py — provides the callable interface for pages.
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.ai_insights import generate_insights, generate_recommendations


def get_insights(df_anomalies: pd.DataFrame, kpi_col: str, method: str) -> str:
    """
    Return a plain-English descriptive explanation of detected anomalies.
    Pass an empty DataFrame to get a 'no anomalies' message.
    """
    return generate_insights(df_anomalies, kpi_col, method)


def get_recommendations(df_anomalies: pd.DataFrame, kpi_col: str, method: str) -> str:
    """
    Return prescriptive strategic recommendations based on detected anomalies.
    Pass an empty DataFrame to get a 'no action required' message.
    """
    return generate_recommendations(df_anomalies, kpi_col, method)
