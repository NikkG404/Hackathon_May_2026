# Anomaly Detection Skill — Statistical Anomaly Detection

## Files
- `skills/anomaly/anomaly_skill.py` — orchestration (calls utils/stats.py)
- `utils/stats.py` — low-level detection functions (pure NumPy)
- `views/anomaly.py` — Streamlit rendering (calls anomaly_skill + insights_skill)

---

## Feature Specification

Triggered when user clicks **⚠️ Anomaly Detection** in the main nav.

---

## UI Flow

1. Radio buttons (horizontal) — **Select Detection Method**:
   - `Z-Score (Standard Score) Method`
   - `IQR (Interquartile Range) Method`
   - `Time Series Statistical Method`
2. **Execute Anomaly Detection** button (primary).
3. On click, `detect_all_kpis(df, method)` runs inside `st.spinner`.
4. Results cached in `st.session_state["anomaly_results"]` and `["anomaly_method_used"]`.
5. Re-clicking Execute replaces cached results.

---

## Output — Per-KPI Tabs

One `st.tab` per KPI in `KPI_COLUMNS` (13 tabs total — 7 raw + 6 derived).

Each tab contains:

### Time Series Chart
- `go.Scatter` with two traces:
  - **Normal** — blue line + small markers (`color="steelblue"`, `size=4`)
  - **Anomaly** — red open circles (`symbol="circle-open"`, `size=10`, `line.width=2.5`)
- X-axis: `Date`, Y-axis: KPI value.

### Anomaly Count Badge
- `st.warning(f"{n} anomalies detected …")` if `n > 0`
- `st.success("No anomalies detected …")` if `n == 0`

### Anomaly Table
- Columns: `Date`, `Campaign_ID`, `Brand`, `Channel`, `{kpi}`, `_anomaly_score`
- Sorted by `Date` ascending.

### Insights (Expandable)
- `st.expander("Insights (Descriptive Analytics)")` → `get_insights(anomaly_df, kpi, method)`

### Recommendations (Expandable)
- `st.expander("Recommendations (Prescriptive Analytics)")` → `get_recommendations(anomaly_df, kpi, method)`

---

## Statistical Methods (`utils/stats.py`)

### Z-Score — pure NumPy (no scipy)
```python
clean  = series.dropna()
mean   = clean.mean()
std    = clean.std(ddof=0)
z_vals = np.abs((clean - mean) / std)   # if std == 0, all zeros
mask   = z_vals > ANOMALY_Z_THRESHOLD   # default 3.0
# score column: z_vals (absolute z-score)
```

### IQR
```python
Q1, Q3  = series.quantile(0.25), series.quantile(0.75)
IQR     = Q3 - Q1
lower   = Q1 - ANOMALY_IQR_MULTIPLIER * IQR   # default 1.5
upper   = Q3 + ANOMALY_IQR_MULTIPLIER * IQR
mask    = (series < lower) | (series > upper)
# score column: distance beyond fence (in IQR units)
```

### Time Series Statistical
```python
rolling_mean = series.rolling(window=ANOMALY_ROLLING_WINDOW, min_periods=1).mean()
rolling_std  = series.rolling(window=ANOMALY_ROLLING_WINDOW, min_periods=1).std().fillna(0)
upper        = rolling_mean + ANOMALY_ROLLING_STD_MULTIPLIER * rolling_std
lower        = rolling_mean - ANOMALY_ROLLING_STD_MULTIPLIER * rolling_std
mask         = (series > upper) | (series < lower)
# score column: (value - rolling_mean) / rolling_std
```

**Config thresholds** (`config.py`):
```python
ANOMALY_Z_THRESHOLD            = 3.0
ANOMALY_IQR_MULTIPLIER         = 1.5
ANOMALY_ROLLING_WINDOW         = 7
ANOMALY_ROLLING_STD_MULTIPLIER = 2.0
```

---

## `skills/anomaly/anomaly_skill.py` API

```python
METHOD_LABELS: list[str]   # ordered list of UI radio-button labels
METHODS: dict[str, str]    # label → internal key ("zscore" | "iqr" | "timeseries")

def detect_anomalies(df, kpi_col, method_label) -> tuple[pd.DataFrame, pd.Series]
    # Returns (anomaly_df_with_score_col, full_score_series)
def detect_all_kpis(df, method_label) -> dict[str, tuple[pd.DataFrame, pd.Series]]
    # {"Impressions": (anomaly_df, scores), "Clicks": ..., ...} for all KPI_COLUMNS
```

## Method Explanation Cards (`views/anomaly.py`)

A `_METHOD_INFO` dict in `views/anomaly.py` holds three keys — one per `METHOD_LABELS` entry — each containing:
- `"what"` — conceptual description of the method
- `"how"` — how it flags anomalies (formula in plain English)
- `"best_for"` — which KPI types / campaign patterns it suits best

Rendered as `st.expander(f"About: {method}", expanded=True)` between the radio buttons and Execute button. Updates live as the user switches methods.
