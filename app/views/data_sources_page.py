import textwrap
import pandas as pd
import streamlit as st

from app.components.ui_helpers import section_header
from app.data.loader import get_source_metadata, using_committed_dataset


def render(datasets, persona, location_label):
    section_header(
        "Data Sources & Pipeline Lineage",
        "Structured transactional tables and unstructured narrative sources feeding this prototype.",
        badge_text="COMMITTED DATASET" if using_committed_dataset() else "IN-MEMORY SYNTHETIC",
        badge_type="healthy" if using_committed_dataset() else "watch",
    )

    with st.container(border=True):
        sources = get_source_metadata()
        table_rows = []
        for s in sources:
            table_rows.append(f"""
<tr>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;font-weight:700;color:#0f172a;">{s['source_name']}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;color:#334155;"><span class="bi-badge bi-badge-watch">{s.get('source_type', 'Structured')}</span></td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;color:#334155;">{s.get('grain', '—')}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;color:#334155;">{s.get('refresh_cadence', '—')}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#0f172a;">{s.get('last_refresh', '—')}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;"><span class="bi-badge bi-badge-healthy">{s.get('data_quality', 'Fresh')}</span></td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;color:#334155;">{s.get('historical_coverage', '—')}</td>
</tr>
""")

        table_html = textwrap.dedent(f"""
<table style="width:100%;border-collapse:collapse;font-size:13px;">
<thead>
<tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Source</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Type</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Grain</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Cadence</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Last Refresh</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Quality</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Coverage</th>
</tr>
</thead>
<tbody>
{''.join(table_rows)}
</tbody>
</table>
""").strip()
        st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header("Grain & Cadence Reconciliation")
    
    with st.container(border=True):
        st.markdown(
            '<div style="font-size:13.5px;color:#1e293b;line-height:1.6;font-weight:500;">'
            'Sales transactions refresh daily at store/day grain, staffing refreshes hourly at '
            'store/hour grain, and customer feedback arrives near real-time at the individual '
            'message grain. The deterministic KPI engine aligns temporal windows and entity hierarchies '
            'before analytical estimation runs.'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header("Current Session Dataset Volume")
    
    counts = {name: len(df_) for name, df_ in datasets.items()}
    c_cols = st.columns(len(counts))
    for col, (name, count) in zip(c_cols, counts.items()):
        with col:
            cnt_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">{name.replace('_', ' ')}</div>
<div class="bi-value" style="font-size:22px;">{count:,}</div>
<div style="font-size:11.5px;color:#475569;">Records loaded</div>
</div>
""").strip()
            st.markdown(cnt_html, unsafe_allow_html=True)