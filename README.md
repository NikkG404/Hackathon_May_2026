# Media Performance Anomaly Detector

A Streamlit-based web application that ingests media campaign performance data, performs exploratory analysis and correlation studies, and automatically surfaces statistical anomalies across campaigns, channels, brands, and KPIs — with plain-English insights and strategic recommendations for every flagged data point.

---

## Table of Contents

1. [Project Background](#1-project-background)
2. [Thought Process & Design Philosophy](#2-thought-process--design-philosophy)
3. [Tech Stack](#3-tech-stack)
4. [How to Run](#4-how-to-run)
5. [Input Data](#5-input-data)
6. [Application Walkthrough](#6-application-walkthrough)
7. [Statistical Methods](#7-statistical-methods)
8. [KPI Reference](#8-kpi-reference)
9. [Project Architecture](#9-project-architecture)

---

## 1. Project Background

Media campaigns generate large volumes of daily performance data — impressions, clicks, spend, conversions, video views, and more. Manually reviewing this data across dozens of campaigns, multiple brands, and several channels to find anomalies is time-consuming, inconsistent, and prone to oversight.

This tool automates that process. It gives media analysts and campaign managers a single interface to:

- **Understand their data** — what time periods, campaigns, and channels are covered, where KPIs stand, what is missing.
- **Discover relationships** — how KPIs correlate with each other and whether those correlations are statistically meaningful.
- **Detect anomalies** — flag days where a KPI behaved unusually relative to its own history, with context on *why* it is anomalous and *what to do* about it.

The tool is designed to be self-serve: no SQL, no Python, no dashboarding skills required. Upload two CSV files, click a button, read the output.

---

## 2. Thought Process & Design Philosophy

### Why a single-page app?
Most analytical tools force users through a rigid linear flow. Here, all three analyses (EDA, Correlation, Anomaly Detection) are available simultaneously as horizontal nav buttons — so an analyst can move freely between context-gathering and investigation without losing state.

### Why two input files?
Campaign performance data (daily metrics) and campaign metadata (channel, brand, objective, budget) serve different analytical purposes. Keeping them separate mirrors real-world data warehouse conventions (fact table + dimension table) and lets the app load quickly on small registry updates without reloading the full time-series.

### Why plain-English bullet points everywhere?
Charts and tables communicate *what happened*. The bullet-point insight blocks communicate *what it means*. A coefficient of variation of 73% is a number; "performance varies significantly across campaigns — investigate what drives peak days" is an action. Both are needed.

### Why no cloud LLM for insights?
All insights and recommendations are generated locally using deterministic rule-based logic driven by the actual computed statistics. This keeps the tool fast, offline-capable, privacy-safe, and completely reproducible — the same data always produces the same insight.

### Why pure NumPy for statistics?
The deployment environment has no scipy or statsmodels. Z-scores, Pearson r, p-values, and the IQR fences are all implemented from first principles using NumPy — making the tool dependency-light and portable.

---

## 3. Tech Stack

| Component | Library | Version |
|---|---|---|
| Web framework | Streamlit | ≥ 1.28 |
| Data manipulation | pandas | ≥ 1.5 |
| Numerical computation | NumPy | ≥ 1.23 |
| Visualisation | Plotly | ≥ 5.0 |
| Python | CPython | 3.10+ |

**No scipy. No statsmodels. No cloud API calls. No database.**

---

## 4. How to Run

### Option A — Double-click (recommended)
```
Double-click  start_app.bat
```
Opens a persistent server on **http://localhost:8502** that survives terminal restarts and browser refreshes.

### Option B — Manual
```bash
"<path-to-venv>/Scripts/streamlit.exe" run app.py --server.port 8502
```

> **Important:** Use `streamlit run app.py` — not `run streamlit app.py` or `python app.py`.

---

## 5. Input Data

The tool expects two CSV files, uploaded via the sidebar.

### File 1 — Campaign Performance Data *(required)*
**What it is:** The fact file. One row = one campaign on one date.

| Column | Type | Description |
|---|---|---|
| `Date` | date | Reporting date (YYYY-MM-DD) |
| `Campaign_ID` | string | Unique campaign identifier (e.g. `A_DIS_01`) |
| `Brand` | string | Brand (A, B, C, D, …) |
| `Channel` | string | Media channel: Display, Video, OTT, Search, Paid Social |
| `Objective` | string | Campaign goal: Awareness, Consideration, Conversion, Retargeting, etc. |
| `Impressions` | integer | Daily ad impressions served |
| `Clicks` | integer | Daily clicks |
| `Spend_USD` | currency | Daily media spend — accepts `"$1,368.59"` format; cleaned on load |
| `Conversions` | decimal | Daily goal completions (30-day click attribution) |
| `Video_Views` | integer | Video completions ≥ 30 s — **blank for non-video channels** |
| `Reach` | integer | Estimated unique users exposed |
| `Frequency` | decimal | Avg exposures per unique user |

> **Note:** A missing row for a date means the campaign was paused that day — not a data error.

### File 2 — Campaign Registry *(optional but recommended)*
**What it is:** The dimension file. One row = one campaign.

| Column | Type | Description |
|---|---|---|
| `Campaign_ID` | string | Primary key — joins to the performance data |
| `Brand` | string | Brand identifier |
| `Channel` | string | Media channel |
| `Objective` | string | Campaign objective |
| `Start_Date` | date | Flight start |
| `End_Date` | date | Flight end |
| `Budget_USD` | currency | Total campaign budget — accepts `"$120,000"` format |

> **Note:** The registry CSV may contain an embedded "Pause Schedule" section at the bottom, separated by a blank row and a `--- Pause Schedule ---` header. The app strips this automatically.

### Upload flow
1. Click the file browser in the sidebar and select your CSV.
2. An **⬆️ Upload** button appears.
3. Click it. The app validates the schema and date columns.
4. A green **✅ Uploaded Successfully** confirmation appears, or a red **❌ Upload failed** with the reason.
5. Upload status persists across reruns; clearing the file widget resets it.

---

## 6. Application Walkthrough

Once campaign data is uploaded, three analysis buttons become active in the main area.

### 📊 Basic EDA

Answers: *"What does my data look like?"*

| Section | What you see | What the insights explain |
|---|---|---|
| **Overview** | 5 metric cards — date range, campaign count, brand count, total rows | How dense the dataset is; avg records per campaign |
| **Campaign Activity** | Tables of most/least active campaigns + bar chart | Which campaigns ran the longest vs shortest; portfolio mix |
| **Channels per Campaign** | Table of unique channels per campaign × brand | Which brands run multi-channel vs single-channel strategies |
| **KPI Summary** | Per-KPI tab with min/max/mean/median table + daily trend line | Variability, benchmark campaign, data completeness per metric |
| **Null Count** | Table of missing values per column | Which columns have gaps and why (e.g. Video_Views is sparse by design) |

---

### 🔗 Correlation Analysis

Answers: *"Do these two KPIs move together?"*

1. Select any two numeric KPI columns from the dropdowns (or tick "Show full matrix" for all 13).
2. Click **Submit**.

| Section | What you see | What the insights explain |
|---|---|---|
| **Pairwise Stats** | Pearson r, p-value, sample size | Strength and direction of the relationship; statistical significance |
| **Scatter Plot** | Data points + OLS trendline (NumPy-computed) | Visual confirmation of the trend; cluster vs spread |
| **Heatmap** | Full Pearson correlation matrix (RdBu_r colour scale) | Strongest pairs, negative trade-offs, most independent KPI |

**Interpreting r:**

| r value | Interpretation |
|---|---|
| ≥ 0.70 | Strong — metrics move closely together |
| 0.50 – 0.69 | Moderate — meaningful co-movement |
| 0.30 – 0.49 | Weak — some relationship, but other factors dominate |
| < 0.30 | Negligible — largely independent |

---

### ⚠️ Anomaly Detection

Answers: *"Which data points are statistically unusual — and what should I do about them?"*

1. Select a detection method (description card appears explaining the method).
2. Click **Execute Anomaly Detection**.
3. Results appear in one tab per KPI (13 tabs total — 7 raw + 6 derived).

**Per-KPI tab output:**

| Element | Description |
|---|---|
| **Time series chart** | All data in blue; anomalous points as red open circles |
| **Anomaly count badge** | Warning (orange) if anomalies found; green if clean |
| **Anomaly table** | Date, Campaign_ID, Brand, Channel, KPI value, anomaly score |
| **Insights expander** | Plain-English description of what was detected |
| **Recommendations expander** | Actionable suggestions for what to investigate or fix |

---

## 7. Statistical Methods

### Z-Score (Standard Score)

**Concept:** Measures how far a value sits from the population mean in units of standard deviation.

**Formula:**
```
z = (value − mean) / std
```
A point is anomalous if **|z| > 3.0** — meaning it lies in the extreme 0.3% tail of a normal distribution.

**When to use:** Best for metrics that are roughly normally distributed and stable over time — Impressions, Reach, Spend on steady campaigns.

**Limitation:** Sensitive to existing outliers (an extreme value inflates the mean and std, potentially masking other anomalies).

---

### IQR (Interquartile Range)

**Concept:** A robust, distribution-free method. Instead of using the mean and std (which are pulled by outliers), it uses the middle 50% of the data to define what is "normal."

**Formula:**
```
IQR   = Q3 − Q1
Lower = Q1 − 1.5 × IQR
Upper = Q3 + 1.5 × IQR
```
Any value outside [Lower, Upper] is flagged.

**When to use:** Best for skewed or heavy-tailed metrics — Conversions, CPA, CPC — where a few extreme values would distort the Z-Score benchmark.

**Advantage:** Not affected by existing outliers in the data.

---

### Time Series Statistical Method

**Concept:** Evaluates each day's value against its *local recent context* rather than the global mean. This captures the fact that what is "normal" for a campaign can shift over time — ramp-up periods, flights, seasonality.

**Formula:**
```
rolling_mean[t] = mean of values in the 7-day window ending at t
rolling_std[t]  = std  of values in the 7-day window ending at t

Anomaly if value > rolling_mean + 2 × rolling_std
          or value < rolling_mean − 2 × rolling_std
```

**When to use:** Best for trending or seasonally-varying metrics — CTR, VTR, Frequency — where a globally-derived threshold would be too loose or too tight.

**Advantage:** Adapts to the campaign lifecycle; catches sudden local spikes that a global method would miss.

---

## 8. KPI Reference

Six derived KPIs are computed automatically on data load. They are treated identically to raw KPIs in all analyses.

| KPI | Full Name | Formula | Unit | Notes |
|---|---|---|---|---|
| `CTR` | Click-Through Rate | Clicks / Impressions × 100 | % | Core engagement metric |
| `CVR` | Conversion Rate | Conversions / Clicks × 100 | % | Reflects landing page / funnel quality |
| `CPM` | Cost per Mille | Spend / Impressions × 1,000 | USD | Efficiency of reach buying |
| `CPC` | Cost per Click | Spend / Clicks | USD | Efficiency of traffic acquisition |
| `CPA` | Cost per Acquisition | Spend / Conversions | USD | Primary metric for performance campaigns |
| `VTR` | View-Through Rate | Video_Views / Impressions × 100 | % | Video/OTT only — NaN for all other channels |

All formulas produce `NaN` (not an error) when the denominator is zero or missing.

---

## 9. Project Architecture

```
project/
├── app.py                    # Single-page Streamlit entry point
├── config.py                 # Column maps, KPI lists, detection thresholds
├── start_app.bat             # Windows persistent launcher
├── requirements.txt
├── assets/images/logo.png
│
├── knowledge/                # Single source of truth for all KPI definitions
│   ├── kpi_definitions.py    # Formulas, compute_derived_kpis(), get_kpi_label/description()
│   └── column_definitions.md # Human-readable reference + API docs
│
├── views/                    # Streamlit rendering layer (UI only, no business logic)
│   ├── eda.py
│   ├── correlation.py
│   └── anomaly.py
│
├── skills/                   # Analytical logic layer (pure Python, no Streamlit)
│   ├── data/                 # Ingest, validate, merge
│   ├── eda/                  # EDA computations + insight generators
│   ├── correlation/          # Pearson r, heatmap + insight generators
│   ├── anomaly/              # Z-Score / IQR / Time Series detection
│   └── insights/             # Descriptive & prescriptive text generation
│
└── utils/                    # Low-level helpers
    ├── data_loader.py        # CSV reader — returns (df, error_msg) tuple
    ├── stats.py              # Core statistical functions (pure NumPy)
    └── ai_insights.py        # Text generation using KPI label/description lookups
```

### Layer rules

```
knowledge/ ← config.py ← utils/ ← skills/ ← views/ ← app.py
```

- Each layer only imports from layers to its left.
- `views/` contains no statistical logic — only Streamlit rendering calls.
- `skills/` contains no Streamlit imports — only pure Python.
- All KPI formulas live exclusively in `knowledge/kpi_definitions.py` — changing a formula there propagates everywhere automatically.
- The folder is named `views/` (not `pages/`) intentionally — Streamlit auto-generates sidebar nav for any `.py` file inside a folder literally named `pages/`.

---

*Built for internal media analytics — Eli Lilly Hackathon 2025.*
