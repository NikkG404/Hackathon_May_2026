import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    ANOMALY_Z_THRESHOLD,
    ANOMALY_IQR_MULTIPLIER,
    ANOMALY_ROLLING_WINDOW,
    ANOMALY_ROLLING_STD_MULTIPLIER,
)


def zscore_anomalies(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Z-Score method. Returns (bool mask, z-score series).
    Anomaly threshold: ANOMALY_Z_THRESHOLD standard deviations from mean.
    Pure NumPy — no scipy dependency.
    """
    clean = series.dropna()
    mean  = clean.mean()
    std   = clean.std(ddof=0)

    z_vals = np.abs((clean - mean) / std) if std > 0 else pd.Series(0.0, index=clean.index)

    full_z = pd.Series(np.nan, index=series.index)
    full_z.loc[clean.index] = z_vals

    mask = full_z > ANOMALY_Z_THRESHOLD
    return mask.fillna(False), full_z


def iqr_anomalies(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    IQR method. Returns (bool mask, distance-from-fence score series).
    Fences: Q1 - 1.5*IQR  /  Q3 + 1.5*IQR
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - ANOMALY_IQR_MULTIPLIER * IQR
    upper = Q3 + ANOMALY_IQR_MULTIPLIER * IQR

    mask = (series < lower) | (series > upper)

    score = pd.Series(0.0, index=series.index)
    below = series < lower
    above = series > upper
    if IQR > 0:
        score[below] = (lower - series[below]) / IQR
        score[above] = (series[above] - upper) / IQR

    return mask.fillna(False), score


def timeseries_anomalies(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Rolling mean ± rolling std method.
    Window: ANOMALY_ROLLING_WINDOW days.
    Threshold: ANOMALY_ROLLING_STD_MULTIPLIER standard deviations.
    """
    rolling_mean = series.rolling(window=ANOMALY_ROLLING_WINDOW, min_periods=1).mean()
    rolling_std = series.rolling(window=ANOMALY_ROLLING_WINDOW, min_periods=1).std().fillna(0)

    upper = rolling_mean + ANOMALY_ROLLING_STD_MULTIPLIER * rolling_std
    lower = rolling_mean - ANOMALY_ROLLING_STD_MULTIPLIER * rolling_std

    mask = (series > upper) | (series < lower)

    # Score: number of std deviations from rolling mean
    denom = rolling_std.replace(0, np.nan)
    score = (series - rolling_mean).abs() / denom
    score = score.fillna(0)

    return mask.fillna(False), score
