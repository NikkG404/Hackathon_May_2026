"""
Correlation skill: compute Pearson correlation matrices and pairwise statistics.
Pure Python — no Streamlit imports. All rendering is handled in pages/correlation.py.
"""
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import KPI_COLUMNS


def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Return KPI columns that are present and numeric in the DataFrame."""
    return [c for c in KPI_COLUMNS if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]


def compute_correlation_matrix(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Return Pearson correlation matrix for the specified columns."""
    return df[columns].corr(method="pearson")


def _pearsonr_numpy(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    """Pearson r and two-tailed p-value using pure NumPy (no scipy)."""
    n  = len(x)
    xm = x - x.mean()
    ym = y - y.mean()
    r  = float(np.dot(xm, ym) / (np.sqrt(np.dot(xm, xm)) * np.sqrt(np.dot(ym, ym)) + 1e-12))
    r  = max(-1.0, min(1.0, r))
    if abs(r) == 1.0 or n <= 2:
        p = 0.0
    else:
        # t-distribution approximation for two-tailed p-value (no scipy needed)
        t    = r * np.sqrt((n - 2) / max(1 - r ** 2, 1e-12))
        # regularised incomplete beta: p ≈ I(df/(df+t²), df/2, 0.5)
        df   = n - 2
        x_b  = df / (df + t ** 2)
        # NumPy-only beta CDF approximation via continued fraction (accurate to ~4 sig figs)
        p = float(_betai(df / 2, 0.5, x_b))
    return r, p


def _betai(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a,b) via NumPy — no scipy."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    # Use continued-fraction expansion (Lentz method) for stability
    lbeta = _log_beta(a, b)
    front = np.exp(np.log(x) * a + np.log(1.0 - x) * b - lbeta) / a
    return float(front * _betacf(a, b, x))


def _log_beta(a: float, b: float) -> float:
    return float(np.sum(np.log(np.arange(1, int(a))) if a > 1 else [0])
                 + np.sum(np.log(np.arange(1, int(b))) if b > 1 else [0])
                 - np.sum(np.log(np.arange(1, int(a + b)))) if a + b > 1 else 0)


def _log_beta(a: float, b: float) -> float:
    """ln B(a,b) via log-gamma approximation (Stirling for large values)."""
    return float(_lgamma(a) + _lgamma(b) - _lgamma(a + b))


def _lgamma(x: float) -> float:
    """Log-gamma via Lanczos approximation."""
    g = 7
    c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028,
         771.32342877765313, -176.61502916214059, 12.507343278686905,
         -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7]
    if x < 0.5:
        return float(np.log(np.pi) - np.log(abs(np.sin(np.pi * x))) - _lgamma(1.0 - x))
    x -= 1
    a = c[0] + sum(c[i + 1] / (x + i + 1) for i in range(g))
    t = x + g + 0.5
    return float(0.5 * np.log(2 * np.pi) + (x + 0.5) * np.log(t) - t + np.log(a))


def _betacf(a: float, b: float, x: float) -> float:
    """Continued-fraction evaluation for incomplete beta (modified Lentz)."""
    max_iter, eps = 200, 3e-7
    fpmin = 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d, h = 1.0 / d, 1.0 / d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d, delta = 1.0 / d, d / c
        h *= delta
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d, delta = 1.0 / d, d / c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return float(h)


def compute_pairwise_stats(df: pd.DataFrame, col1: str, col2: str) -> dict:
    """
    Return Pearson r, two-tailed p-value, and sample size for two columns.
    NaN rows are dropped before computation.
    """
    clean = df[[col1, col2]].dropna()
    if len(clean) < 3:
        return {"r": None, "p_value": None, "n": len(clean)}
    r, p = _pearsonr_numpy(clean[col1], clean[col2])
    return {"r": round(r, 4), "p_value": round(p, 4) if not np.isnan(p) else "N/A", "n": len(clean)}


# ── Insight generators ────────────────────────────────────────────────────────

def generate_pairwise_insights(pair_stats: dict, col1: str, col2: str) -> list[str]:
    r = pair_stats["r"]
    p = pair_stats["p_value"]
    n = pair_stats["n"]

    if r is None:
        return ["Insufficient data to compute a reliable correlation — at least 3 non-null paired rows are required."]

    abs_r     = abs(r)
    strength  = "strong" if abs_r >= 0.7 else "moderate" if abs_r >= 0.5 else "weak" if abs_r >= 0.3 else "negligible"
    direction = "positive" if r > 0 else "negative"

    try:
        p_float = float(p)
        if p_float < 0.001:
            sig_text = "highly statistically significant (p < 0.001)"
        elif p_float < 0.01:
            sig_text = "very significant (p < 0.01)"
        elif p_float < 0.05:
            sig_text = "statistically significant (p < 0.05)"
        else:
            sig_text = "not statistically significant (p ≥ 0.05) — treat this relationship with caution"
    except (ValueError, TypeError):
        sig_text = "statistical significance could not be determined"

    bullets = [
        f"Pearson r = **{r}** indicates a **{strength} {direction} linear relationship** between **{col1}** and **{col2}**.",
        f"This result is **{sig_text}**, computed on **{n:,} paired observations**.",
    ]

    if direction == "positive" and abs_r >= 0.5:
        bullets.append(
            f"Campaigns that score high on **{col1}** tend to also score high on **{col2}** — "
            "these metrics move together and likely share the same underlying campaign driver."
        )
    elif direction == "negative" and abs_r >= 0.5:
        bullets.append(
            f"As **{col1}** rises, **{col2}** tends to fall — this inverse relationship may point to "
            "an efficiency trade-off worth exploring in budget allocation or bidding strategy."
        )
    elif abs_r < 0.3:
        bullets.append(
            f"The negligible correlation means **{col1}** and **{col2}** largely move independently — "
            "improving one is unlikely to directly impact the other."
        )
    else:
        bullets.append(
            f"The {strength} relationship suggests some co-movement, but both metrics also respond to separate influences."
        )

    if n < 30:
        bullets.append(
            f"**Note:** Only **{n} data points** were available — with small samples, correlation estimates are less reliable; interpret results with caution."
        )

    return bullets


def generate_heatmap_insights(corr_matrix: pd.DataFrame) -> list[str]:
    cols  = corr_matrix.columns.tolist()
    pairs = [
        (cols[i], cols[j], corr_matrix.iloc[i, j])
        for i in range(len(cols))
        for j in range(i + 1, len(cols))
        if not np.isnan(corr_matrix.iloc[i, j])
    ]

    if not pairs:
        return ["Not enough numeric data to build a full correlation matrix."]

    by_abs       = sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    top          = by_abs[0]
    strong_pairs = [p for p in pairs if abs(p[2]) >= 0.7]
    neg_pairs    = sorted([p for p in pairs if p[2] < -0.3], key=lambda x: x[2])

    corr_no_diag = corr_matrix.where(~np.eye(len(corr_matrix), dtype=bool))
    most_indep = corr_no_diag.abs().mean().idxmin()

    bullets = [
        f"**{top[0]} ↔ {top[1]}** is the strongest pair in the matrix (r = **{top[2]:.2f}**) — "
        "these metrics are closely linked and likely driven by the same campaign-level factors.",
    ]

    if len(strong_pairs) > 1:
        bullets.append(
            f"**{len(strong_pairs)} metric pairs** show strong correlations (|r| ≥ 0.70), suggesting significant "
            "co-movement — these KPIs may partially capture the same signal and should be interpreted together."
        )
    else:
        bullets.append(
            "Most metric pairs show moderate-to-weak correlations, meaning the KPIs capture distinct aspects "
            "of campaign performance rather than duplicating the same signal."
        )

    if neg_pairs:
        nb = neg_pairs[0]
        bullets.append(
            f"**{nb[0]} ↔ {nb[1]}** (r = {nb[2]:.2f}) is the sharpest negative relationship — "
            "when one improves, the other tends to worsen, pointing to a potential efficiency trade-off."
        )
    else:
        bullets.append(
            "No meaningful negative correlations were found — all significant relationships in this dataset trend in the same direction."
        )

    bullets.append(
        f"**{most_indep}** has the lowest average correlation with other KPIs, meaning it captures a unique "
        "dimension of performance that the other metrics don't fully explain."
    )
    return bullets
