# Media Performance Anomaly Detector — Claude Code Instructions

## Project Overview

A **Streamlit web application** for detecting statistical anomalies in media campaign performance data. The tool ingests two CSVs (campaign-level time series + campaign registry), performs EDA, correlation analysis, and anomaly detection, and outputs AI-generated insights and recommendations.

---

## Tech Stack

- **Framework:** Streamlit
- **Language:** Python 3.10+
- **Core Libraries:** `pandas`, `numpy`, `plotly`, `streamlit` *(scipy is NOT required — Z-scores use pure NumPy)*
- **Run the app (recommended — double-click or run from any terminal):**
  ```
  start_app.bat
  ```
- **Run the app (manual):**
  ```bash
  "C:\Users\L108410\OneDrive - Eli Lilly and Company\Desktop\MMM Insights Generator\.venv\Scripts\streamlit.exe" run app.py --server.port 8502
  ```

> **Important:** The correct command is `streamlit run app.py` — NOT `run streamlit app.py`.  
> Use `start_app.bat` for a persistent server that survives terminal restarts.

---

## Application Structure

```
project/
├── app.py                    # Single-page Streamlit entry point — routing, sidebar, session state
├── config.py                 # Column maps, KPI lists, thresholds
├── start_app.bat             # Windows launcher — double-click to start server
├── requirements.txt          # pandas, numpy, plotly, streamlit (no scipy)
├── assets/images/logo.png    # Sidebar logo
├── knowledge/                # ★ Single source of truth for KPI definitions & formulas
│   ├── kpi_definitions.py    #   DERIVED_KPI_COLUMNS, compute_derived_kpis(), get_kpi_label/description()
│   └── column_definitions.md #   Full column + KPI reference with API docs → READ THIS for KPI details
├── views/                    # Streamlit UI layer — rendering only, no business logic
│   ├── eda.py                #   Basic EDA view
│   ├── correlation.py        #   Correlation Analysis view
│   └── anomaly.py            #   Anomaly Detection view
├── skills/                   # Core analytical logic — pure Python, no Streamlit
│   ├── data/
│   │   ├── data_skill.py     #   Ingest, validate, merge campaign + registry data
│   │   └── data_skill.md     #   → Schema, upload flow, validation spec
│   ├── eda/
│   │   ├── eda_skill.py      #   EDA computation functions
│   │   └── eda_skill.md      #   → EDA feature specification
│   ├── correlation/
│   │   ├── correlation_skill.py  # Pearson correlation (pure NumPy)
│   │   └── correlation_skill.md  # → Correlation feature specification
│   ├── anomaly/
│   │   ├── anomaly_skill.py  #   Z-Score / IQR / Time Series detection orchestration
│   │   └── anomaly_skill.md  #   → Anomaly feature spec + statistical method formulas
│   └── insights/
│       ├── insights_skill.py #   Insights & recommendations interface
│       └── insights_skill.md #   → Insights generation spec
└── utils/                    # Low-level helpers
    ├── data_loader.py        #   CSV reader/cleaner — returns (df, error_msg) tuple
    ├── stats.py              #   zscore_anomalies, iqr_anomalies, timeseries_anomalies
    └── ai_insights.py        #   generate_insights / generate_recommendations text logic
```

### Layer responsibilities

| Layer        | Contains           | Imports from         | Rule                                             |
|--------------|--------------------|----------------------|--------------------------------------------------|
| `knowledge/` | Definitions & math | stdlib, numpy, pandas| No Streamlit, no config imports                  |
| `config.py`  | Column maps, lists | `knowledge/`         | Import DERIVED_KPI_COLUMNS from knowledge        |
| `views/`     | Streamlit UI       | `skills/`            | No direct stats/business logic; never `pages/`   |
| `skills/`    | Analytical logic   | `utils/`, `config`   | No Streamlit imports                             |
| `utils/`     | Low-level helpers  | `config`, `knowledge/`| Pure functions only                             |

> **Never rename `views/` to `pages/`** — Streamlit auto-generates sidebar nav entries for every `.py` in a folder named exactly `pages/`, duplicating the main-area buttons.

---

## Single-Page App Architecture

`app.py` is the **only** Streamlit entry point. No multi-page routing.

### Layout

```
┌─────────────────────┬──────────────────────────────────────────────────────┐
│  SIDEBAR (left)     │  MAIN CONTENT AREA                                   │
│                     │                                                      │
│  [logo]             │  🏠 Home  ›  [active section breadcrumb]             │
│  ─────────────────  │  Media Performance Anomaly Detector                  │
│  Data Management    │  ─────────────────────────────────────────────────   │
│                     │  [📊 Basic EDA] [🔗 Correlation] [⚠️ Anomaly]        │
│  📊 Campaign Data   │  ─────────────────────────────────────────────────   │
│  [file browser]     │                                                      │
│  [⬆️ Upload button] │  Welcome card   — when no data is loaded             │
│  [status message]   │  Ready card     — when data loaded, no view active   │
│                     │  EDA / Correlation / Anomaly content                 │
│  📋 Campaign Reg.   │    — rendered when a button is clicked               │
│  [file browser]     │                                                      │
│  [⬆️ Upload button] │                                                      │
│  [status message]   │                                                      │
│  ─────────────────  │                                                      │
│  Loaded Files       │                                                      │
│  [Reset button]     │                                                      │
└─────────────────────┴──────────────────────────────────────────────────────┘
```

### Session state keys

| Key                     | Type                                          | Purpose                                |
|-------------------------|-----------------------------------------------|----------------------------------------|
| `active_view`           | `None \| "eda" \| "correlation" \| "anomaly"` | Which view is rendered                 |
| `campaign_df`           | `DataFrame \| None`                           | Loaded campaign performance data       |
| `registry_df`           | `DataFrame \| None`                           | Loaded campaign registry               |
| `uploaded_files`        | `dict`                                        | `{"campaign": name, "registry": name}` |
| `campaign_upload_status`| `None \| "success" \| "failed"`               | Upload result for campaign file        |
| `registry_upload_status`| `None \| "success" \| "failed"`               | Upload result for registry file        |
| `corr_done`             | `bool`                                        | Whether correlation has been submitted |
| `anomaly_results`       | `dict \| None`                                | Cached anomaly detection output        |
| `anomaly_method_used`   | `str \| None`                                 | Method label used for current results  |

---

## Navigation Buttons

Three horizontally-placed buttons in the main content area:

| Button                 | Action                            |
|------------------------|-----------------------------------|
| `📊 Basic EDA`         | Sets `active_view = "eda"`        |
| `🔗 Correlation Analysis` | Sets `active_view = "correlation"` |
| `⚠️ Anomaly Detection` | Sets `active_view = "anomaly"`    |

- Disabled until campaign data is uploaded.
- Active button: `type="primary"` (blue). Inactive: `type="secondary"`.
- Breadcrumb above title updates: `🏠 Home › 📊 Basic EDA`.

---

## Developer Configuration Notes

- All column name references must use `config.COLUMN_MAP` — never hardcode column names.
- `KPI_COLUMNS` in `config.py` drives which columns appear in EDA, correlation, and anomaly tabs.
- Adding a new derived KPI requires only updating `knowledge/kpi_definitions.py`.
- Per-skill feature specs are in `skills/<name>/<name>_skill.md`.
- KPI definitions and formulas reference: `knowledge/column_definitions.md`.

---

## UI / UX Guidelines

- `st.set_page_config(layout="wide")` — always wide layout.
- `st.columns` for horizontal button placement.
- `st.sidebar` for data upload only.
- `st.expander` for Insights and Recommendations sections.
- `st.spinner` during analysis.
- Plotly only — no Matplotlib.
- Anomaly charts: normal points **blue**, anomalies **red open circles**.
- Correlation heatmap: `color_continuous_scale="RdBu_r"`.

---

## Assets

Logo: `assets/images/logo.png` — displayed in sidebar above Data Management.  
Recommended dimensions: 400 × 120 px (wide banner) or 200 × 200 px (square icon).
