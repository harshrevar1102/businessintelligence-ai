import textwrap
import plotly.graph_objects as go
import streamlit as st

from app.analytics import context as ctx_builder
from app.analytics.kpi_engine import revenue_trend_series
from app.components.ui_helpers import render_driver_bars, render_kpi_card, render_trend_chart, section_header
from app.config.kpi_contract import KPI_CONTRACT
from app.data.loader import get_source_metadata


def render(datasets, persona, location_label):
    ctx = ctx_builder.build_context(datasets, persona, location_label)
    if not len(ctx.transactions_df):
        st.warning("No data available for this persona/location combination.")
        return

    col_sel, _ = st.columns([1.5, 2.5])
    with col_sel:
        kpi_name = st.selectbox("Select KPI to Inspect", list(ctx.kpis.keys()))
    kpi = ctx.kpis[kpi_name]

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Top KPI metric card
    c_card, c_thresh = st.columns([1.2, 2.8])
    with c_card:
        render_kpi_card(c_card, kpi)
    
    with c_thresh:
        stat_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Statistical & Materiality Evaluation</div>
<div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:12px;margin-top:10px;">
<div>
<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Current Value</div>
<div style="font-size:18px;font-weight:800;color:#0f172a;">{kpi.current_value:,.2f}</div>
</div>
<div>
<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Baseline Value</div>
<div style="font-size:18px;font-weight:800;color:#0f172a;">{kpi.baseline_value:,.2f}</div>
</div>
<div>
<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Materiality Status</div>
<div style="font-size:14px;font-weight:800;color:{'#991b1b' if kpi.materiality_label == 'Material' else '#166534'};margin-top:2px;">
{kpi.materiality_label} (p={kpi.p_value:.3f})
</div>
</div>
</div>
</div>
""").strip()
        st.markdown(stat_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Trend Chart
    section_header(f"{kpi_name} Trend Analysis", "Historical rolling trend versus baseline trajectory.")
    with st.container(border=True):
        if kpi_name in ("Revenue", "Transactions", "Average Ticket"):
            trend = revenue_trend_series(ctx.transactions_df)
            st.plotly_chart(render_trend_chart(trend), use_container_width=True)
        else:
            wt = ctx.staffing_df.copy()
            daily = wt.groupby("date")["wait_time"].mean().reset_index()
            fig_wt = go.Figure()
            fig_wt.add_trace(go.Scatter(
                x=daily["date"], y=daily["wait_time"],
                name="Wait Time (min)", mode="lines+markers",
                line=dict(color="#2563eb", width=2.5),
                marker=dict(size=4, color="#1d4ed8")
            ))
            fig_wt.update_layout(
                height=260, margin=dict(l=10, r=20, t=20, b=10),
                plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
                font=dict(family="Inter, sans-serif", size=12, color="#0f172a"),
                yaxis=dict(title="Wait Time (minutes)", gridcolor="#f1f5f9", linecolor="#cbd5e1"),
                xaxis=dict(showgrid=False, linecolor="#cbd5e1")
            )
            st.plotly_chart(fig_wt, use_container_width=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Driver Decomposition
    section_header("Driver Decomposition", f"Modeled contributors explaining {kpi_name} variance.")
    with st.container(border=True):
        st.plotly_chart(render_driver_bars(ctx.drivers), use_container_width=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # KPI Semantic Contract & Data Freshness
    c_contract, c_fresh = st.columns([1.5, 1])
    with c_contract:
        section_header("KPI Semantic Contract", "Authoritative definition and business formula.")
        contract = KPI_CONTRACT.get(kpi_name)
        if contract:
            contract_html = textwrap.dedent(f"""
<div class="bi-card">
<div style="font-size:14px;font-weight:750;color:#0f172a;margin-bottom:8px;">{kpi_name}</div>
<div style="color:#334155;font-size:13.5px;line-height:1.5;margin-bottom:10px;">
<b>Definition:</b> {contract['definition']}
</div>
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;font-family:monospace;font-size:12.5px;color:#1e293b;margin-bottom:10px;">
Formula: {contract['formula']}
</div>
<div style="font-size:12.5px;color:#475569;display:grid;grid-template-columns:1fr 1fr;gap:6px;">
<div>Owner: <b style="color:#0f172a;">{contract['owner']}</b></div>
<div>Cadence: <b style="color:#0f172a;">{contract['refresh_cadence']}</b></div>
<div>Grain: <b style="color:#0f172a;">{contract['grain']}</b></div>
<div>Source: <b style="color:#0f172a;">{contract['source'].split(' (')[0]}</b></div>
</div>
</div>
""").strip()
            st.markdown(contract_html, unsafe_allow_html=True)

    with c_fresh:
        section_header("Data Freshness & Lineage", "Pipeline telemetry for this KPI.")
        source_name = contract["source"].split(" (")[0] if contract else None
        meta = next((m for m in get_source_metadata() if m["source_name"] == source_name), None)
        if meta:
            fresh_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Data Pipeline Health</div>
<div style="margin:10px 0;">
<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Last Refresh</div>
<div style="font-size:16px;font-weight:800;color:#0f172a;">{meta['last_refresh']}</div>
</div>
<div style="margin:10px 0;">
<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Data Quality</div>
<div style="font-size:14px;font-weight:800;color:#166534;"><span class="bi-badge bi-badge-healthy">{meta['data_quality']}</span></div>
</div>
<div style="margin:10px 0;">
<div style="font-size:11px;color:#64748b;text-transform:uppercase;font-weight:700;">Historical Coverage</div>
<div style="font-size:14px;font-weight:700;color:#0f172a;">{meta['historical_coverage']}</div>
</div>
</div>
""").strip()
            st.markdown(fresh_html, unsafe_allow_html=True)
