# Correlation Skill — Pearson Correlation Analysis

## Files
- `skills/correlation/correlation_skill.py` — pure-Python / NumPy correlation math
- `views/correlation.py` — Streamlit rendering (calls correlation_skill, no business logic)

---

## Feature Specification

Triggered when user clicks **🔗 Correlation Analysis** in the main nav.  
Tooltip on the nav button: `"Performs correlation analysis between any 2 selected numerical columns."`

---

## UI Flow

1. An expander **"Select Columns"** is shown expanded by default.
2. Two `st.selectbox` dropdowns — **First KPI** and **Second KPI** — populated with numeric KPI columns only (via `get_numeric_columns(df)`).
3. A checkbox: **"Show full correlation matrix (all numeric KPIs)"** — `value=False` by default.
4. A **Submit** button (primary). Sets `st.session_state["corr_done"] = True`.
5. Nothing renders until Submit is clicked.

---

## Output Sections

### Pairwise Stats (always for the two selected columns)
Three `st.metric` cards:
- **Pearson r** — rounded to 4 decimal places
- **p-value** — rounded to 4 decimal places, or `"N/A"` if NaN
- **Sample Size** — count of non-NaN rows

### Scatter Plot
- `px.scatter` with `trendline="ols"`, `opacity=0.55`, `color_discrete_sequence=["steelblue"]`.
- Title format: `"{col1} vs {col2}  (r = {r})"`.

### Correlation Heatmap
- `px.imshow` of the Pearson correlation matrix.
- `color_continuous_scale="RdBu_r"`, `zmin=-1`, `zmax=1`, `text_auto=".2f"`.
- Columns used: full `numeric_cols` if checkbox is checked, else just `[col1, col2]`.
- Chart height: `max(350, 80 * len(cols_to_use))`.

---

## Implementation Notes

### Pearson r (pure NumPy — no scipy required)
```python
xm = x - x.mean(); ym = y - y.mean()
r  = dot(xm, ym) / (sqrt(dot(xm,xm)) * sqrt(dot(ym,ym)) + 1e-12)
r  = clamp(r, -1.0, 1.0)
```

### p-value
Approximated via `scipy.special.betainc` if scipy is available; otherwise returns `float("nan")`.  
The t-statistic: `t = r * sqrt((n-2) / (1-r²))`, then beta-function two-tailed p.

---

## `skills/correlation/correlation_skill.py` API

```python
def get_numeric_columns(df)                          -> list[str]
    # Returns KPI_COLUMNS present in df that are numeric dtype
def compute_correlation_matrix(df, columns)          -> pd.DataFrame
    # Pearson correlation matrix via df[columns].corr(method="pearson")
def compute_pairwise_stats(df, col1, col2)           -> dict
    # {"r": float, "p_value": float|"N/A", "n": int}
    # Drops NaN rows before computation; returns None r/p if n < 3

# Insight generators — return list[str] of bullet-point strings
def generate_pairwise_insights(pair_stats, col1, col2)  -> list[str]
    # Labels r as strong/moderate/weak/negligible; interprets p-value significance
    # Adds caution note if n < 30
def generate_heatmap_insights(corr_matrix)               -> list[str]
    # Finds strongest pair, counts strong pairs (|r|≥0.7), flags negative correlations
    # Identifies most independent KPI via lowest mean |r| (diagonal excluded with .where())
```

## Notes
- `trendline="ols"` (Plotly) was replaced with pure `np.polyfit` in `views/correlation.py` — statsmodels not available.
- Diagonal exclusion uses `corr_matrix.where(~np.eye(..., dtype=bool))` — avoids read-only numpy array error from `np.fill_diagonal(.values, ...)`.
- p-value computed via Lanczos log-gamma + Lentz continued-fraction beta CDF — no scipy.
