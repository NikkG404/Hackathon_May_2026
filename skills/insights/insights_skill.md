# Insights Skill — Descriptive & Prescriptive Text Generation

## Files
- `skills/insights/insights_skill.py` — thin callable interface for views
- `utils/ai_insights.py` — text generation logic; uses `knowledge/kpi_definitions.py`

---

## Purpose

Generates plain-English text from anomaly detection results:
- **Descriptive Insights** — explain *what* was detected (counts, dates, magnitude).
- **Prescriptive Recommendations** — suggest *what to do* about the anomalies.

Text is enriched with KPI full names and definitions via:
- `get_kpi_label(col)` → e.g. `"Click-Through Rate (%)"`
- `get_kpi_description(col)` → definition sentence from `knowledge/kpi_definitions.py`

---

## Behavior

| Condition             | Insights output                               | Recommendations output           |
|-----------------------|-----------------------------------------------|----------------------------------|
| `anomaly_df` is empty | "No anomalies detected for {KPI label}."      | "No action required."            |
| Anomalies present     | Summary of count, date range, severity, method | Actionable strategic suggestions |

---

## `skills/insights/insights_skill.py` API

```python
def get_insights(df_anomalies: pd.DataFrame, kpi_col: str, method: str) -> str
    # Returns markdown-formatted descriptive text.
    # Pass empty DataFrame for "no anomalies" message.

def get_recommendations(df_anomalies: pd.DataFrame, kpi_col: str, method: str) -> str
    # Returns markdown-formatted prescriptive text.
    # Pass empty DataFrame for "no action required" message.
```

Both functions delegate to `utils/ai_insights.py`:
```python
generate_insights(df_anomalies, kpi_col, method)       -> str
generate_recommendations(df_anomalies, kpi_col, method) -> str
```

---

## Adding New Insight Logic

1. Edit `utils/ai_insights.py` — add/update `generate_insights` or `generate_recommendations`.
2. Use `get_kpi_label(col)` and `get_kpi_description(col)` from `knowledge/kpi_definitions.py` for consistent KPI naming.
3. Do **not** add Streamlit calls here — rendering stays in `views/anomaly.py`.
