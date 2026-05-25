# Media Campaign Performance Dataset — Column & KPI Reference

This is the authoritative reference for all column definitions and KPI formulas used in this project.
**All skills and utility modules import formulas exclusively from `knowledge/kpi_definitions.py`.**
Do not define or recompute KPIs elsewhere.

---

## Raw Columns (from `Campaign_Data_Sample.csv`)

| Column | Type | Definition |
|---|---|---|
| `Date` | Date | Calendar date of the reporting day (YYYY-MM-DD). Multiple campaigns can share the same date, reflecting simultaneous campaign activity. |
| `Campaign_ID` | Text | Unique campaign identifier. Format: `<Brand>_<Channel_Code>_<Index>` (e.g., `A_DIS_01` = Brand A, Display, Campaign 1). Multiple IDs can be active on the same date within the same Brand and Channel. |
| `Brand` | Categorical | Brand identifier: A, B, C, or D. Each brand manages its campaigns independently. |
| `Channel` | Categorical | Media channel: Display, Video, OTT, Search, or Paid Social. Each channel may have 2–3 concurrent campaigns per brand. |
| `Objective` | Categorical | Campaign objective: Awareness, Consideration, Conversion, Retargeting, Branded Search, or Non-Branded Search. |
| `Impressions` | Integer | Total ad impressions served on this day. **Absence of a row = campaign was paused that day.** |
| `Clicks` | Integer | Total user clicks on ads for the day. |
| `Spend_USD` | Decimal (USD) | Total media spend in USD for this campaign on this day. Stored as `"$1,368.59"` in CSV; stripped on load. |
| `Conversions` | Decimal | Goal actions attributed to this campaign. Uses a **30-day click attribution window**. |
| `Video_Views` | Integer (nullable) | Video views ≥ 30 s or completion. **Video and OTT channels only — blank for all other channels.** |
| `Reach` | Integer | Estimated unique users exposed to the campaign's ads. |
| `Frequency` | Decimal | Average exposures per unique user (Impressions ÷ Reach). |

---

## Derived KPIs (computed on load via `knowledge/kpi_definitions.py`)

These columns are added to every loaded DataFrame automatically. **Do not recalculate inline — always use `compute_derived_kpis()`.**

| KPI | Full Name | Formula | Unit | Channels | Interpretation |
|---|---|---|---|---|---|
| `CTR` | Click-Through Rate | `Clicks / Impressions × 100` | % | All | Ad engagement rate. Higher = stronger creative or targeting. |
| `CVR` | Conversion Rate | `Conversions / Clicks × 100` | % | All | Share of clicks leading to a conversion. Reflects landing page quality. |
| `CPM` | Cost per Mille | `Spend_USD / Impressions × 1,000` | USD | All | Cost per 1,000 impressions. Core efficiency metric for awareness. |
| `CPC` | Cost per Click | `Spend_USD / Clicks` | USD | All | Average cost per click. Lower = more efficient traffic. |
| `CPA` | Cost per Acquisition | `Spend_USD / Conversions` | USD | All | Cost per conversion. Primary KPI for performance campaigns. |
| `VTR` | View-Through Rate | `Video_Views / Impressions × 100` | % | Video, OTT | Proportion of impressions resulting in a video view. NaN for non-video channels. |

> **ROAS** (Return on Ad Spend = `Conversions × Avg_Order_Value / Spend_USD`) is not computed automatically because Average Order Value is not present in the dataset.

---

## Notes on Data Behaviour

- **Paused campaigns:** No row is written for paused days. Gaps in a Campaign_ID's date sequence indicate paused periods. Cross-reference `Campaign_Registry.csv` for the pause schedule.
- **Division by zero:** All derived KPI formulas produce `NaN` (not an error) when the denominator is zero or null.
- **VTR sparsity:** `VTR` will be `NaN` for Display, Search, and Paid Social rows because `Video_Views` is blank for those channels. This is expected and not a data quality issue.
- **Frequency identity:** `Frequency` in the raw data should equal `Impressions / Reach`. Any deviation may indicate data quality issues worth investigating.

---

## Adding a New KPI

1. Add an entry to `DERIVED_KPI_DEFINITIONS` in `knowledge/kpi_definitions.py`
2. Add the computation to `compute_derived_kpis()` in the same file
3. Update the table above in this document
4. No other files need to change — `config.py` imports `DERIVED_KPI_COLUMNS` automatically

---

## `knowledge/kpi_definitions.py` — Public API

| Export | Type | Purpose |
|---|---|---|
| `COLUMN_DEFINITIONS` | `dict` | Definition string for every raw CSV column |
| `DERIVED_KPI_DEFINITIONS` | `dict` | Name, formula, unit, channel scope, and description for each derived KPI |
| `DERIVED_KPI_COLUMNS` | `list` | `["CTR", "CVR", "CPM", "CPC", "CPA", "VTR"]` |
| `compute_derived_kpis(df)` | `function` | Adds all derived KPI columns to a DataFrame copy; returns the copy |
| `get_kpi_label(col)` | `function` | Returns `"Name (unit)"` for display, e.g. `"Click-Through Rate (%)"` |
| `get_kpi_description(col)` | `function` | Returns the definition string for any raw or derived column |

### Workflow
1. `utils/data_loader.load_campaign_data()` calls `compute_derived_kpis()` on every loaded DataFrame.
2. `config.py` imports `DERIVED_KPI_COLUMNS` → `KPI_COLUMNS = RAW_KPI_COLUMNS + DERIVED_KPI_COLUMNS` (13 total).
3. All skills and views read `KPI_COLUMNS` from `config` — derived KPIs are treated identically to raw KPIs.
4. `utils/ai_insights.py` uses `get_kpi_label()` and `get_kpi_description()` to enrich insight text.

> **Rule:** Never recompute a KPI formula outside `knowledge/kpi_definitions.py`.  
> If a formula changes, update it once there — everything else picks it up automatically.
