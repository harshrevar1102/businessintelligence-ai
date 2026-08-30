import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.config.settings import APP_SUBTITLE, APP_TITLE, PERSONAS
from app.data.loader import get_datasets
from app.entitlement.entitlement import allowed_locations, enforce_default_location
from app.views import (
    action_simulator_page, counterfactuals_page, data_sources_page, driver_analysis_page,
    evidence_explorer, executive_overview, feedback_page, kpi_contract_page, kpi_explorer, telemetry_page,
)

st.set_page_config(
    page_title=f"{APP_TITLE} — Executive Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Contrast, Dark-Sidebar Executive Styling System
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background-color: #f6f7f9 !important;
    color: #0f172a !important;
}

/* Headings & High Contrast Text */
h1, h2, h3, h4, h5, h6 {
    color: #0f172a !important;
    font-weight: 750 !important;
    letter-spacing: -0.02em !important;
}

p, span, label, li, td, th {
    color: #1e293b;
    font-weight: 500;
}

/* Fix washed-out captions */
[data-testid="stCaptionContainer"], .stCaption, small {
    color: #334155 !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    opacity: 1 !important;
}

/* Dark Modern Executive Sidebar */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid #1e293b !important;
    color: #e2e8f0 !important;
}

[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 1.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* Sidebar Brand Logo */
.sidebar-brand {
    font-size: 20px;
    font-weight: 800;
    color: #ffffff !important;
    letter-spacing: -0.03em;
    margin-bottom: 2px;
}

.sidebar-brand span {
    color: #38bdf8 !important;
}

.sidebar-tagline {
    font-size: 11px;
    color: #94a3b8 !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 24px;
}

.sidebar-group-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8 !important;
    margin: 18px 4px 8px;
}

/* Sidebar Navigation Buttons */
[data-testid="stSidebar"] div.stButton > button {
    background-color: transparent !important;
    color: #cbd5e1 !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    padding: 9px 12px !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    text-align: left !important;
    display: flex !important;
    justify-content: flex-start !important;
    transition: all 0.15s ease-in-out !important;
    box-shadow: none !important;
    margin-bottom: 2px !important;
}

[data-testid="stSidebar"] div.stButton > button:hover {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border-color: #334155 !important;
}

[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border-left: 3px solid #38bdf8 !important;
    border-top: 1px solid #334155 !important;
    border-right: 1px solid #334155 !important;
    border-bottom: 1px solid #334155 !important;
}

[data-testid="stSidebar"] div.stButton > button[kind="primary"] * {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Main Container Layout */
.main .block-container {
    max-width: 1360px;
    padding: 2rem 2.5rem 3rem !important;
}

/* Topbar Header */
.topbar-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 18px;
}

.topbar-title {
    font-size: 26px;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
    letter-spacing: -0.03em;
}

.topbar-subtitle {
    font-size: 13.5px;
    color: #475569;
    font-weight: 600;
    margin-top: 4px;
}

/* Custom UI Cards */
.bi-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    height: 100%;
}

.bi-label {
    color: #475569;
    font-size: 11.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
}

.bi-value {
    font-size: 26px;
    font-weight: 800;
    color: #0f172a;
    margin: 6px 0;
    letter-spacing: -0.02em;
}

.bi-delta {
    font-size: 13px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 4px;
}

.bi-delta.up {
    color: #16a34a;
}

.bi-delta.down {
    color: #dc2626;
}

.bi-meta {
    font-size: 12px;
    color: #475569;
    font-weight: 500;
    margin-top: 8px;
    border-top: 1px solid #f1f5f9;
    padding-top: 6px;
}

/* High-Contrast Alert Banners (NO orange) */
.bi-alert {
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 22px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

.bi-alert-critical {
    background: #fff1f2;
    border: 1px solid #fecdd3;
    border-left: 5px solid #dc2626;
}

.bi-alert-critical .bi-alert-title {
    color: #991b1b;
    font-weight: 800;
    font-size: 14.5px;
    margin-bottom: 3px;
}

.bi-alert-info {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 5px solid #2563eb;
}

.bi-alert-info .bi-alert-title {
    color: #1e3a8a;
    font-weight: 800;
    font-size: 14.5px;
    margin-bottom: 3px;
}

.bi-alert-body {
    color: #1e293b;
    font-size: 13.5px;
    font-weight: 500;
    line-height: 1.5;
}

.bi-alert-meta {
    color: #475569;
    font-size: 12px;
    font-weight: 600;
    margin-top: 6px;
}

.bi-alert-icon {
    font-size: 20px;
    line-height: 1;
}

/* Badges */
.bi-badge {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 99px;
    font-size: 11px;
    font-weight: 750;
    letter-spacing: 0.4px;
}

.bi-badge-critical {
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fca5a5;
}

.bi-badge-watch {
    background: #e0e7ff;
    color: #3730a3;
    border: 1px solid #c7d2fe;
}

.bi-badge-healthy {
    background: #dcfce7;
    color: #166534;
    border: 1px solid #86efac;
}

/* Section Headers */
.bi-section-header {
    margin-top: 24px;
    margin-bottom: 12px;
}

.bi-section-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}

.bi-section-title {
    font-size: 18px;
    font-weight: 750;
    color: #0f172a;
    margin: 0;
}

.bi-section-sub {
    font-size: 13px;
    color: #475569;
    font-weight: 500;
    margin-top: 4px;
}

/* Insight Cards */
.bi-insight-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 9px;
    padding: 14px 16px;
    margin-bottom: 10px;
    line-height: 1.5;
}

.bi-insight-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
}

.bi-insight-num {
    background: #2563eb;
    color: #ffffff;
    border-radius: 99px;
    width: 20px;
    height: 20px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11.5px;
    font-weight: 800;
}

.bi-insight-title {
    font-weight: 750;
    color: #0f172a;
    font-size: 14px;
}

.bi-insight-body {
    color: #334155;
    font-size: 13.5px;
    font-weight: 500;
}

/* Action Recommendation Box */
.bi-action-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 18px 20px;
    margin-top: 8px;
}

.bi-action-flow {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}

.bi-action-step {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 7px 12px;
    display: inline-flex;
    flex-direction: column;
    gap: 2px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}

.step-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #64748b;
    font-weight: 700;
}

.step-val {
    font-size: 13px;
    font-weight: 700;
    color: #0f172a;
}

.bi-action-arrow {
    color: #2563eb;
    font-weight: 800;
    font-size: 16px;
}

.bi-action-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 13px;
    color: #1e293b;
    border-top: 1px solid #dbeafe;
    padding-top: 10px;
    margin-top: 6px;
    font-weight: 500;
}

.bi-action-impact {
    color: #15803d;
    font-weight: 750;
    font-size: 13.5px;
}

/* Streamlit Native Form Elements Overrides */
div[data-testid="stSelectbox"] label, div[data-testid="stSlider"] label, div[data-testid="stTextInput"] label {
    color: #0f172a !important;
    font-size: 12.5px !important;
    font-weight: 700 !important;
}

div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border-color: #cbd5e1 !important;
    border-radius: 8px !important;
    color: #0f172a !important;
    font-weight: 600 !important;
}

div[data-testid="stExpander"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
}

div[data-testid="stExpander"] summary {
    font-weight: 700 !important;
    color: #0f172a !important;
}

/* Streamlit Tabs */
button[data-baseweb="tab"] {
    font-weight: 700 !important;
    color: #475569 !important;
    font-size: 14px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #2563eb !important;
    border-bottom-color: #2563eb !important;
}

/* Native Metrics Styling */
[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 16px 18px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
}

[data-testid="stMetricLabel"] {
    color: #475569 !important;
    font-size: 12px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

[data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 24px !important;
    font-weight: 800 !important;
}

/* Dataframe styling */
[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* Dividers */
hr {
    border-color: #e2e8f0 !important;
    margin: 1.5rem 0 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

PAGES = {
    "Workspace": {
        "Executive Overview": executive_overview,
        "KPI Explorer": kpi_explorer,
        "Driver Analysis": driver_analysis_page,
        "Counterfactuals": counterfactuals_page,
        "Action Simulator": action_simulator_page,
    },
    "Data": {
        "Evidence": evidence_explorer,
        "Data Sources": data_sources_page,
        "KPI Contract": kpi_contract_page,
    },
    "System": {
        "Feedback": feedback_page,
        "Telemetry": telemetry_page,
    },
}

with st.sidebar:
    st.markdown(
        textwrap.dedent("""
<div class="sidebar-brand">BusinessIntelligence<span>.ai</span></div>
<div class="sidebar-tagline">Causal KPI-to-Action Engine</div>
""").strip(),
        unsafe_allow_html=True,
    )

    if "active_page" not in st.session_state:
        st.session_state.active_page = "Executive Overview"

    for group_name, pages in PAGES.items():
        st.markdown(f'<div class="sidebar-group-title">{group_name}</div>', unsafe_allow_html=True)
        for page_name in pages:
            is_active = st.session_state.active_page == page_name
            if st.button(
                page_name,
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.active_page = page_name

if "persona" not in st.session_state:
    st.session_state.persona = "CEO / Executive"

# Topbar with title, subtitle, and selectors
top_left, top_r1, top_r2 = st.columns([2.5, 1.2, 1.2])
with top_left:
    top_html = textwrap.dedent(f"""
<div class="topbar-title">Business Performance Overview</div>
<div class="topbar-subtitle">{APP_SUBTITLE}</div>
""").strip()
    st.markdown(top_html, unsafe_allow_html=True)

with top_r1:
    persona = st.selectbox("Active Persona", PERSONAS, key="persona")

with top_r2:
    location_options = allowed_locations(persona)
    default_location = enforce_default_location(persona, st.session_state.get("location", location_options[0]))
    location_label = st.selectbox(
        "Location / Branch",
        location_options,
        index=location_options.index(default_location),
        key="location",
    )

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

datasets = get_datasets()
active_group = next(g for g in PAGES if st.session_state.active_page in PAGES[g])
active_module = PAGES[active_group][st.session_state.active_page]

active_module.render(datasets, persona, location_label)

st.divider()
footer_html = textwrap.dedent("""
<div style="color: #475569; font-size: 12px; font-weight: 500; line-height: 1.5; margin-top: 10px;">
<b>Prototype UI • Synthetic CaféCo data</b><br>
Numeric attribution is generated by deterministic statistical logic; RAG provides contextual evidence;
LLMs are limited to evidence extraction and narrative generation.
</div>
""").strip()
st.markdown(footer_html, unsafe_allow_html=True)
