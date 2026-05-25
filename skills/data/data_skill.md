# Data Skill — Schema, Loading & Validation

## Files
- `skills/data/data_skill.py` — ingest, validate, and merge campaign + registry DataFrames
- `utils/data_loader.py` — low-level CSV reader/cleaner; called by data_skill

---

## Data Schema

### 1. Campaign Performance Data — Fact File (`Campaign_Data_Sample.csv`)

**Role:** Daily time-series KPI data at campaign level. One row = one campaign on one date.  
**Upload label in UI:** "Campaign Performance Data"

| CSV Column    | Type    | Notes                                                                 |
|---------------|---------|-----------------------------------------------------------------------|
| `Date`        | date    | YYYY-MM-DD                                                            |
| `Campaign_ID` | string  | Unique campaign key, matches Campaign Registry                        |
| `Brand`       | string  | Brand identifier (A, B, C, D, …)                                     |
| `Channel`     | string  | Media channel (Display, Video, OTT, Search, Paid Social)              |
| `Objective`   | string  | Campaign objective (Awareness, Retargeting, Branded, …)               |
| `Impressions` | integer | Daily impression count                                                |
| `Clicks`      | integer | Daily click count                                                     |
| `Spend_USD`   | float   | Daily spend — stored as `"$1,368.59"` in CSV; cleaned on load         |
| `Conversions` | float   | Daily conversions (fractional attribution)                            |
| `Video_Views` | float   | Daily video views — **sparse** (empty for non-video channels)         |
| `Reach`       | integer | Daily unique reach                                                    |
| `Frequency`   | float   | Avg exposures per unique user                                         |

```python
COLUMN_MAP = {
    "date":        "Date",
    "campaign_id": "Campaign_ID",
    "brand":       "Brand",
    "channel":     "Channel",
    "objective":   "Objective",
    "impressions": "Impressions",
    "clicks":      "Clicks",
    "spend":       "Spend_USD",
    "conversions": "Conversions",
    "video_views": "Video_Views",
    "reach":       "Reach",
    "frequency":   "Frequency",
}
RAW_KPI_COLUMNS  = ["Impressions", "Clicks", "Spend_USD", "Conversions", "Video_Views", "Reach", "Frequency"]
CURRENCY_COLUMNS = ["Spend_USD"]  # Stripped of "$" and "," on load
```

---

### 2. Campaign Registry — Dimension File (`Campaign_Registry.csv`)

**Role:** Static campaign metadata. One row = one campaign.  
**Upload label in UI:** "Campaign Registry"

> The registry CSV contains an embedded **Pause Schedule** section below the main campaign table
> (separated by a blank row and a `--- Pause Schedule ---` header).
> The data loader automatically ignores this section.

| CSV Column    | Type   | Notes                                                          |
|---------------|--------|----------------------------------------------------------------|
| `Campaign_ID` | string | Primary key — joins to Campaign Performance Data               |
| `Brand`       | string | Brand identifier                                               |
| `Channel`     | string | Media channel                                                  |
| `Objective`   | string | Campaign objective                                             |
| `Start_Date`  | date   | Campaign flight start (YYYY-MM-DD)                             |
| `End_Date`    | date   | Campaign flight end (YYYY-MM-DD)                               |
| `Budget_USD`  | float  | Total campaign budget — stored as `"$120,000"` in CSV; cleaned |

```python
REGISTRY_COLUMN_MAP = {
    "campaign_id": "Campaign_ID",
    "brand":       "Brand",
    "channel":     "Channel",
    "objective":   "Objective",
    "start_date":  "Start_Date",
    "end_date":    "End_Date",
    "budget":      "Budget_USD",
}
REGISTRY_CURRENCY_COLUMNS = ["Budget_USD"]
```

---

## Upload Flow (Sidebar)

Each uploader follows the same pattern — **browse first, then explicitly upload**:

1. User selects a CSV file in the `st.file_uploader` widget (file is not yet processed).
2. An **"⬆️ Upload"** button appears.
3. On click, `load_campaign_data(file, silent=True)` or `load_registry_data(file, silent=True)` is called.
4. Result:
   - **Pass** → `"✅ Uploaded Successfully"` — DataFrame stored in session state.
   - **Fail** → `"❌ Upload failed. Schema mismatched or some data issue is there."` — nothing stored.
5. Status message clears automatically if the user removes the file from the uploader.

### Validation checks — campaign data
- File must be readable as CSV.
- All columns in `COLUMN_MAP.values()` must be present.
- `Date` column must contain at least one parseable date.

### Validation checks — registry
- File must be readable as CSV.
- `Campaign_ID` column must be present.
- At least one valid (non-blank, non-`---`) row must exist after Pause Schedule stripping.

---

## `utils/data_loader.py` API

```python
def load_campaign_data(file, silent: bool = False) -> tuple[pd.DataFrame | None, str]:
    # Returns (df, error_message). df is None on failure.
    # When silent=True, suppresses st.error() — caller handles messaging.

def load_registry_data(file, silent: bool = False) -> tuple[pd.DataFrame | None, str]:
    # Same pattern. Strips Pause Schedule section automatically.
```

Always call with `silent=True` from the upload button block and handle messaging in `app.py`.

---

## `skills/data/data_skill.py` API

```python
def ingest_campaign_data(uploaded_file) -> pd.DataFrame | None
def ingest_registry_data(uploaded_file) -> pd.DataFrame | None
def merge_campaign_with_registry(campaign_df, registry_df) -> pd.DataFrame
    # Left-joins on Campaign_ID; adds Start_Date, End_Date, Budget_USD
def validate_columns(df, required_cols) -> tuple[bool, list[str]]
    # Returns (is_valid, missing_columns)
```
