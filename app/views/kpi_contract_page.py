import textwrap
import streamlit as st

from app.components.ui_helpers import section_header
from app.config.kpi_contract import KPI_CONTRACT


def render(datasets, persona, location_label):
    section_header("KPI Semantic Contract Catalog", "Authoritative business definitions, formulas, lineage, and governance rules.")
    
    col_sel, _ = st.columns([1.5, 2.5])
    with col_sel:
        kpi_name = st.selectbox("Select KPI Contract", list(KPI_CONTRACT.keys()))
    
    contract = KPI_CONTRACT[kpi_name]

    with st.container(border=True):
        st.markdown(f"<div class='bi-label'>Semantic Specification</div><h3 style='margin:4px 0 12px;color:#0f172a;'>{kpi_name}</h3>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Definition:** <span style='color:#334155;'>{contract['definition']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Formula:** <code style='color:#1e293b;background:#f1f5f9;padding:2px 6px;border-radius:4px;'>{contract['formula']}</code>", unsafe_allow_html=True)
            st.markdown(f"**Unit of Measure:** <b style='color:#0f172a;'>{contract['unit']}</b>", unsafe_allow_html=True)
            st.markdown(f"**Upstream Source:** <span style='color:#334155;'>{contract['source']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Aggregation Grain:** <span style='color:#334155;'>{contract['grain']}</span>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**Refresh Cadence:** <span style='color:#334155;'>{contract['refresh_cadence']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Historical Coverage:** <span style='color:#334155;'>{contract['historical_coverage']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Baseline Method:** <span style='color:#334155;'>{contract['baseline_method']}</span>", unsafe_allow_html=True)
            st.markdown(f"**Materiality Threshold:** <b style='color:#991b1b;'>{contract['materiality_threshold']}</b>", unsafe_allow_html=True)
            st.markdown(f"**Business Owner:** <b style='color:#0f172a;'>{contract['owner']}</b>", unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;border-top:1px solid #f1f5f9;margin-top:12px;'></div>", unsafe_allow_html=True)
        st.markdown(f"**Modeled Drivers:** <span style='color:#2563eb;font-weight:600;'>{', '.join(contract['drivers'])}</span>", unsafe_allow_html=True)
        st.markdown(f"**Data Lineage:** <span style='color:#475569;'>{contract['lineage']}</span>", unsafe_allow_html=True)
        st.markdown(f"**Access Restriction:** <span class='bi-badge bi-badge-watch'>{contract['access_restriction']}</span>", unsafe_allow_html=True)
