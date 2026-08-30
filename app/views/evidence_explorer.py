import textwrap
import time

import streamlit as st

from app.analytics import context as ctx_builder
from app.components.ui_helpers import section_header
from app.rag.retriever import detect_contradiction, retrieve_evidence
from app.telemetry.telemetry import log_event


def render(datasets, persona, location_label):
    ctx = ctx_builder.build_context(datasets, persona, location_label)

    with st.container(border=True):
        c_inp, c_k = st.columns([3, 1])
        with c_inp:
            query = st.text_input("Search Qualitative Evidence & Feedback", value="staffing wait time revenue decline")
        with c_k:
            top_k = st.slider("Max Results", 2, 10, 5)

    if not query:
        return

    t0 = time.time()
    results, backend = retrieve_evidence(
        ctx.documents_df, ctx.feedback_df, query, persona, ctx.city, ctx.store, top_k=top_k
    )
    latency = time.time() - t0

    log_event(
        analysis_label="Evidence Explorer search",
        persona=persona,
        location=location_label,
        kpi="n/a",
        method="RAG semantic retrieval",
        retrieval_count=len(results),
        latency_seconds=latency,
        retrieval_latency_seconds=latency,
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header(
        f"{len(results)} Evidence Results Retrieved",
        f"Semantic search executed in {latency*1000:.1f}ms using {backend} embeddings.",
        badge_text=f"{backend.upper()} BACKEND",
        badge_type="healthy",
    )

    if detect_contradiction(results):
        contra_html = textwrap.dedent("""
<div class="bi-alert bi-alert-critical">
<div class="bi-alert-icon">⚠️</div>
<div>
<div class="bi-alert-title">Conflicting Signals Detected</div>
<div class="bi-alert-body">These results contain conflicting narratives (e.g. staff shortage complaints alongside reports of normal traffic).</div>
</div>
</div>
""").strip()
        st.markdown(contra_html, unsafe_allow_html=True)

    for r in results:
        c = r["chunk"]
        chunk_html = textwrap.dedent(f"""
<div class="bi-card" style="margin-bottom:12px;padding:16px 20px;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
<div style="font-size:15px;font-weight:750;color:#0f172a;">{c['subject']}</div>
<span class="bi-badge bi-badge-watch">{c['source_type']}</span>
</div>
<div style="font-size:12px;color:#475569;margin-bottom:8px;font-weight:500;">
Location: <b style="color:#0f172a;">{c['city']}/{c['store']}</b> • Date: <b style="color:#0f172a;">{c['date']}</b> • Relevance Score: <b style="color:#2563eb;">{r['score']:.2f}</b>
</div>
<div style="font-size:13.5px;color:#1e293b;line-height:1.55;font-weight:500;">
{c['text']}
</div>
<div style="font-size:11.5px;color:#64748b;margin-top:8px;border-top:1px solid #f1f5f9;padding-top:6px;">
Sensitivity: <b>{c['sensitivity']}</b> • Chunk ID: <code>{c['chunk_id']}</code>
</div>
</div>
""").strip()
        st.markdown(chunk_html, unsafe_allow_html=True)
