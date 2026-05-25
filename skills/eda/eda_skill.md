# EDA Skill — Exploratory Data Analysis

## Files
- `skills/eda/eda_skill.py` — pure-Python computation functions
- `views/eda.py` — Streamlit rendering (calls eda_skill, no business logic)

---

## Feature Specification

Triggered when user clicks **📊 Basic EDA** in the main nav.  
All computations run once inside a `st.spinner`, then results are rendered.

---

## Sections Rendered

### 1. Overview (5 metric cards)
| Metric           | Source                                   |
|------------------|------------------------------------------|
| Start Date       | `min(Date)`                              |
| End Date         | `max(Date)`                              |
| Unique Campaigns | `nunique(Campaign_ID)`                   |
| Unique Brands    | `nunique(Brand)`                         |
| Total Rows       | `len(df)`                                |

### 2. Campaign Activity — Active Days
- Table of all campaigns sorted by `Active_Days` descending.
- **Most Active (top 10)** and **Least Active (bottom 10)** displayed side-by-side.
- Plotly bar chart — top 25 campaigns by active days, `color_continuous_scale="Blues"`.

### 3. Channels per Campaign × Brand
- `groupby([Campaign_ID, Brand])[Channel].nunique()` → column: `Unique_Channels`
- Rendered as `st.dataframe`, sorted by `[Brand, Campaign_ID]`.

### 4. KPI Summary — per Campaign
- Stats: `min`, `max`, `mean`, `median` for every KPI in `KPI_COLUMNS`.
- One tab per KPI (raw + derived, 13 total).
- Each tab: stat table + Plotly line chart of daily total (sum across all campaigns) for that KPI.
- Line chart color: `"steelblue"`.

### 5. Null Count per Column
- `df.isnull().sum()` → table sorted descending.

---

## `skills/eda/eda_skill.py` API

```python
def compute_overview(df)             -> dict
def compute_campaign_activity(df)    -> pd.DataFrame   # all campaigns, ranked by Active_Days desc
def compute_channels_per_campaign(df)-> pd.DataFrame   # campaign × brand with Unique_Channels
def compute_kpi_summary(df)          -> pd.DataFrame   # per-campaign min/max/mean/median per KPI
def compute_null_counts(df)          -> pd.DataFrame   # column → Null_Count, sorted desc
def compute_kpi_over_time(df, kpi)   -> pd.DataFrame   # daily sum of kpi: [Date, kpi]

# Insight generators — return list[str] of bullet-point strings
def generate_overview_insights(overview: dict)                      -> list[str]
def generate_activity_insights(activity: pd.DataFrame)              -> list[str]
def generate_channel_insights(channels: pd.DataFrame)               -> list[str]
def generate_kpi_insights(df, kpi, kpi_summ)                        -> list[str]
    # Uses CV (coefficient of variation) to classify variability as low/moderate/high
    # Identifies benchmark campaign (highest mean for the KPI)
    # Flags null % with context (video-only metrics expected to be sparse)
def generate_null_insights(nulls: pd.DataFrame, total_rows: int)    -> list[str]
```
