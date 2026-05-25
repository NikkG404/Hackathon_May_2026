import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="Media Performance Anomaly Detector",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Nav buttons */
div[data-testid="column"] > div > div > div > button {
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    padding: 0.65rem 0;
}
/* Welcome / ready cards */
.welcome-card {
    background: #f8f9fb;
    border: 1px solid #e3e6ea;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-top: 0.5rem;
}
.ready-card {
    background: #eef6ee;
    border: 1px solid #b2d8b2;
    border-radius: 12px;
    padding: 1.25rem 2rem;
    margin-top: 0.5rem;
}
/* Section breadcrumb */
.section-label {
    font-size: 0.85rem;
    color: #6b7280;
    margin-bottom: 0.25rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
_defaults = {
    "active_view":            None,
    "campaign_df":            None,
    "registry_df":            None,
    "uploaded_files":         {},
    # Upload status per file: None | "success" | "failed"
    "campaign_upload_status": None,
    "registry_upload_status": None,
    "corr_done":              False,
    "anomaly_results":        None,
    "anomaly_method_used":    None,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "images", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.markdown("---")

    st.markdown("## Data Management")

    # ── Campaign Performance Data ─────────────────────────────────────────────
    st.markdown("#### 📊 Campaign Performance Data")
    st.caption("Fact file — daily KPI metrics per campaign")

    campaign_file = st.file_uploader(
        "campaign_perf",
        type=["csv"],
        key="upload_campaign",
        label_visibility="collapsed",
        accept_multiple_files=False,
    )

    if campaign_file is not None:
        # Show Upload button only when a file is browsed
        if st.button("⬆️  Upload Campaign Data", key="btn_upload_campaign",
                     type="primary", use_container_width=True):
            with st.spinner("Validating and loading…"):
                from utils.data_loader import load_campaign_data
                _df, _err = load_campaign_data(campaign_file, silent=True)
            if _df is not None:
                st.session_state["campaign_df"]            = _df
                st.session_state["uploaded_files"]["campaign"] = campaign_file.name
                st.session_state["campaign_upload_status"] = "success"
                # Reset view so the ready-card shows
                st.session_state["active_view"] = None
            else:
                st.session_state["campaign_upload_status"] = "failed"

    # Status message (persists across reruns)
    _cs = st.session_state.get("campaign_upload_status")
    if _cs == "success":
        st.success("✅ Uploaded Successfully")
    elif _cs == "failed":
        st.error("❌ Upload failed. Schema mismatched or some data issue is there.")

    # Reset status when user clears/changes the file
    if campaign_file is None and _cs is not None:
        st.session_state["campaign_upload_status"] = None

    st.markdown("")

    # ── Campaign Registry ─────────────────────────────────────────────────────
    st.markdown("#### 📋 Campaign Registry")
    st.caption("Dimension file — campaign metadata (Brand, Channel, Objective, Budget, Dates)")

    registry_file = st.file_uploader(
        "campaign_registry",
        type=["csv"],
        key="upload_registry",
        label_visibility="collapsed",
        accept_multiple_files=False,
    )

    if registry_file is not None:
        if st.button("⬆️  Upload Campaign Registry", key="btn_upload_registry",
                     type="primary", use_container_width=True):
            with st.spinner("Validating and loading…"):
                from utils.data_loader import load_registry_data
                _rdf, _rerr = load_registry_data(registry_file, silent=True)
            if _rdf is not None:
                st.session_state["registry_df"]              = _rdf
                st.session_state["uploaded_files"]["registry"] = registry_file.name
                st.session_state["registry_upload_status"]   = "success"
            else:
                st.session_state["registry_upload_status"] = "failed"

    _rs = st.session_state.get("registry_upload_status")
    if _rs == "success":
        st.success("✅ Uploaded Successfully")
    elif _rs == "failed":
        st.error("❌ Upload failed. Schema mismatched or some data issue is there.")

    if registry_file is None and _rs is not None:
        st.session_state["registry_upload_status"] = None

    # ── Loaded files list ─────────────────────────────────────────────────────
    if st.session_state["uploaded_files"]:
        st.markdown("---")
        st.markdown("**Loaded Files**")
        _icons = {"campaign": "📊", "registry": "📋"}
        for _ftype, _fname in st.session_state["uploaded_files"].items():
            st.markdown(f"{_icons.get(_ftype, '📄')} `{_fname}`")

    # ── Reset ─────────────────────────────────────────────────────────────────
    if st.session_state["campaign_df"] is not None:
        st.markdown("---")
        if st.button("🔄 Reset / Load New Data", use_container_width=True):
            for _k in ("campaign_df", "registry_df", "active_view",
                       "corr_done", "anomaly_results", "anomaly_method_used",
                       "campaign_upload_status", "registry_upload_status"):
                st.session_state[_k] = None
            st.session_state["uploaded_files"] = {}
            st.rerun()

# ── Main area — header ────────────────────────────────────────────────────────
active = st.session_state.get("active_view")
df     = st.session_state["campaign_df"]

# Breadcrumb / section label
_section_labels = {
    "eda":         "🏠 Home  ›  📊 Basic EDA",
    "correlation": "🏠 Home  ›  🔗 Correlation Analysis",
    "anomaly":     "🏠 Home  ›  ⚠️ Anomaly Detection",
}
_section = _section_labels.get(active, "🏠 Home")
st.markdown(f"<div class='section-label'>{_section}</div>", unsafe_allow_html=True)
st.markdown(
    "<h2 style='margin:0 0 2px 0;'>Media Performance Anomaly Detector</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#6b7280; margin:0 0 14px 0;'>"
    "Detect statistical anomalies across campaigns, channels, and KPIs.</p>",
    unsafe_allow_html=True,
)

# ── Three navigation buttons ──────────────────────────────────────────────────
col_eda, col_corr, col_anom = st.columns(3)

with col_eda:
    if st.button("📊  Basic EDA", use_container_width=True,
                 type="primary" if active == "eda" else "secondary",
                 disabled=(df is None)):
        st.session_state["active_view"] = "eda"
        st.rerun()

with col_corr:
    if st.button(
        "🔗  Correlation Analysis",
        use_container_width=True,
        type="primary" if active == "correlation" else "secondary",
        help="Performs correlation analysis between any 2 selected numerical columns.",
        disabled=(df is None),
    ):
        st.session_state["active_view"] = "correlation"
        st.session_state["corr_done"] = False
        st.rerun()

with col_anom:
    if st.button("⚠️  Anomaly Detection", use_container_width=True,
                 type="primary" if active == "anomaly" else "secondary",
                 disabled=(df is None)):
        st.session_state["active_view"] = "anomaly"
        st.rerun()

st.markdown("---")

# ── Content ───────────────────────────────────────────────────────────────────
if df is None:
    st.markdown("""
<div class="welcome-card">
<h3 style="margin-top:0;">👋 Welcome</h3>
<p>
This tool analyzes your media campaign performance data to automatically surface statistical
anomalies across channels, brands, and KPIs.
To get started, <strong>upload your data files using the sidebar on the left</strong>.
</p>
<p><strong>What you'll need:</strong></p>
<ul>
  <li>📊 <strong>Campaign Performance Data</strong> (required) — Daily KPI metrics at the
      campaign level: Impressions, Clicks, Spend, Conversions, Video Views, Reach, and Frequency.</li>
  <li>📋 <strong>Campaign Registry</strong> (optional but recommended) — Static campaign metadata:
      Channel, Brand, Objective, Budget, Start &amp; End dates.</li>
</ul>
<p><strong>What you'll get:</strong></p>
<ul>
  <li>🔍 <strong>Basic EDA</strong> — Time-period overview, KPI breakdowns, activity analysis, null diagnostics</li>
  <li>📈 <strong>Correlation Analysis</strong> — Pearson correlation heatmaps and pairwise scatter plots between KPIs</li>
  <li>⚠️ <strong>Anomaly Detection</strong> — Z-Score, IQR, or Time Series detection with AI-generated
      insights and strategic recommendations for every flagged anomaly</li>
</ul>
</div>
""", unsafe_allow_html=True)

elif active is None:
    import config as _cfg
    _date_col  = _cfg.COLUMN_MAP["date"]
    _camp_col  = _cfg.COLUMN_MAP["campaign_id"]
    _brand_col = _cfg.COLUMN_MAP["brand"]
    st.markdown(f"""
<div class="ready-card">
<strong>✅ Data loaded and ready.</strong>&nbsp;&nbsp;
{len(df):,} rows &nbsp;·&nbsp;
{df[_camp_col].nunique()} campaigns &nbsp;·&nbsp;
{df[_brand_col].nunique()} brands &nbsp;·&nbsp;
{df[_date_col].min().date()} → {df[_date_col].max().date()}
<br/><br/>
Select an analysis above: <strong>Basic EDA</strong>, <strong>Correlation Analysis</strong>,
or <strong>Anomaly Detection</strong>.
</div>
""", unsafe_allow_html=True)

elif active == "eda":
    from views.eda import render as _render_eda
    _render_eda(df)

elif active == "correlation":
    from views.correlation import render as _render_corr
    _render_corr(df)

elif active == "anomaly":
    from views.anomaly import render as _render_anom
    _render_anom(df)
