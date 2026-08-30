import textwrap
import pandas as pd
import streamlit as st

from app.components.ui_helpers import section_header
from app.llm.ollama_client import is_available
from app.telemetry.telemetry import get_events


def render(datasets, persona, location_label):
    section_header("Inference Server Status", "Health check for local Ollama LLM / embedding engine.")
    available = is_available()
    if available:
        st.markdown(
            textwrap.dedent("""
<div class="bi-alert bi-alert-info">
<div class="bi-alert-icon">⚡</div>
<div>
<div class="bi-alert-title">Ollama Server Online</div>
<div class="bi-alert-body">Local LLM & embedding endpoints are active and responding.</div>
</div>
</div>
""").strip(),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            textwrap.dedent("""
<div class="bi-alert bi-alert-critical">
<div class="bi-alert-icon">ℹ️</div>
<div>
<div class="bi-alert-title">Ollama Server Offline (Fallback Active)</div>
<div class="bi-alert-body">Narrative synthesis is using high-performance local deterministic template fallback. See README for Ollama setup.</div>
</div>
</div>
""").strip(),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header(
        "Runtime Execution Telemetry",
        "Every analytical query, vector retrieval, and LLM call in this session logs telemetry here.",
    )
    events = get_events()
    if not events:
        with st.container(border=True):
            st.markdown(
                '<div style="color:#475569;font-size:13px;">'
                'No analysis events recorded yet in this session — navigate to the Executive Overview or Driver Analysis pages to trigger runs.'
                '</div>',
                unsafe_allow_html=True,
            )
        return

    df = pd.DataFrame(events)

    # 4-Column Metric Summary Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        c1_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Total LLM Calls</div>
<div class="bi-value">{int(df['llm_calls'].sum())}</div>
<div style="font-size:11.5px;color:#475569;">Inference invocations</div>
</div>
""").strip()
        st.markdown(c1_html, unsafe_allow_html=True)

    with c2:
        c2_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Total Tokens</div>
<div class="bi-value">{int(df['input_tokens'].sum() + df['output_tokens'].sum()):,}</div>
<div style="font-size:11.5px;color:#475569;">Prompt + Completion</div>
</div>
""").strip()
        st.markdown(c2_html, unsafe_allow_html=True)

    with c3:
        c3_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Simulated Cost</div>
<div class="bi-value" style="color:#16a34a;">${df['estimated_cost_usd'].sum():.4f}</div>
<div style="font-size:11.5px;color:#475569;">Nominal cloud equivalent</div>
</div>
""").strip()
        st.markdown(c3_html, unsafe_allow_html=True)

    with c4:
        c4_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Avg Latency</div>
<div class="bi-value">{df['total_latency_seconds'].mean():.2f}s</div>
<div style="font-size:11.5px;color:#475569;">End-to-end execution</div>
</div>
""").strip()
        st.markdown(c4_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown(
        '<div style="font-size:12px;color:#64748b;margin-top:10px;">'
        'Estimated cost is a nominal figure for demonstrating operational cost governance — actual local Ollama inference has zero marginal API cost.'
        '</div>',
        unsafe_allow_html=True,
    )
