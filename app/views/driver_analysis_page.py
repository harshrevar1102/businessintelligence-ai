import textwrap
import time

import streamlit as st

from app.analytics import context as ctx_builder
from app.components.ui_helpers import render_driver_bars, section_header
from app.rag.retriever import detect_contradiction, retrieve_evidence
from app.telemetry.telemetry import log_event


def render(datasets, persona, location_label):
    ctx = ctx_builder.build_context(datasets, persona, location_label)
    if not len(ctx.transactions_df):
        st.warning("No data available for this persona/location combination.")
        return

    section_header(
        "Ranked Drivers",
        f"Modeled attribution decomposition for Revenue in {location_label}.",
        badge_text="STATISTICAL ATTRIBUTION",
        badge_type="healthy",
    )

    with st.container(border=True):
        st.plotly_chart(render_driver_bars(ctx.drivers), use_container_width=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header("Driver Deep-Dive & Linked Evidence", "Explore individual driver mechanics, method lineage, and qualitative corroboration.")

    for i, driver in enumerate(ctx.drivers, start=1):
        with st.expander(f"{i}. {driver.name} — {driver.contribution_pct:.1f}% contribution (Confidence: {driver.confidence:.2f})"):
            info_html = textwrap.dedent(f"""
<div style="font-size:14px;color:#1e293b;margin-bottom:10px;line-height:1.5;font-weight:500;">
{driver.explanation}
</div>
<div style="display:flex;gap:16px;margin-bottom:12px;font-size:12px;color:#475569;">
<div>Method: <b style="color:#0f172a;">{driver.method}</b></div>
<div>Controllable: <b style="color:#0f172a;">{driver.controllable}</b></div>
<div>Direction: <b style="color:{'#dc2626' if driver.direction == 'negative' else '#16a34a'};">{driver.direction.upper()}</b></div>
</div>
""").strip()
            st.markdown(info_html, unsafe_allow_html=True)

            if driver.evidence_query:
                if len(ctx.transactions_df) < 12000:
                    st.markdown(
                        f"""
                        <div style="margin-top:12px;background:#fff1f2;border:1px solid #fecdd3;border-radius:8px;padding:12px 16px;font-size:13px;color:#9f1239;line-height:1.55;">
                            <b style="color:#881337;">Insufficient Data:</b><br>Not enough data to pull reliable citations and evidence. Available data contains {len(ctx.transactions_df):,} transactions, whereas a minimum of 12,000 transactions is required for causal analysis.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    t0 = time.time()
                    results, backend = retrieve_evidence(
                        ctx.documents_df,
                        ctx.feedback_df,
                        driver.evidence_query,
                        persona,
                        ctx.city,
                        ctx.store,
                    )
                    latency = time.time() - t0
                    contradictory = detect_contradiction(results)

                    log_event(
                        analysis_label=f"Driver evidence - {driver.name}",
                        persona=persona,
                        location=location_label,
                        kpi="Revenue",
                        method=driver.method,
                        retrieval_count=len(results),
                        latency_seconds=latency,
                        retrieval_latency_seconds=latency,
                    )

                    if contradictory:
                        st.markdown(
                            textwrap.dedent("""
    <div class="bi-alert bi-alert-critical" style="margin: 8px 0;">
    <div class="bi-alert-icon">⚠️</div>
    <div class="bi-alert-body">Contradictory evidence found for this driver — treat attribution as provisional.</div>
    </div>
    """).strip(),
                            unsafe_allow_html=True,
                        )

                    st.markdown("<div style='font-size:12.5px;font-weight:700;color:#0f172a;margin-top:6px;'>Corroborating Evidence:</div>", unsafe_allow_html=True)
                    for r in results:
                        c = r["chunk"]
                        ev_html = textwrap.dedent(f"""
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px 12px;margin:6px 0;">
    <div style="font-weight:700;font-size:13px;color:#0f172a;">{c['subject']} <span class="bi-badge bi-badge-watch">{c['source_type']}</span></div>
    <div style="font-size:12px;color:#475569;margin:2px 0 4px;">{c['city']}/{c['store']} • {c['date']} • Score: {r['score']:.2f}</div>
    <div style="font-size:13px;color:#334155;font-weight:500;">{c['text']}</div>
    </div>
    """).strip()
                        st.markdown(ev_html, unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size:12px;color:#475569;'>No linked evidence query for this driver.</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header("Alternative Hypotheses & Residuals")
    
    with st.container(border=True):
        if len(ctx.drivers) > 1:
            for d in ctx.drivers[1:3]:
                hyp_html = textwrap.dedent(f"""
<div style="padding:8px 0;border-bottom:1px solid #f1f5f9;font-size:13.5px;color:#1e293b;">
• <b>{d.name}</b> could also explain part of the variance (<b>{d.contribution_pct:.1f}%</b> modeled contribution).
</div>
""").strip()
                st.markdown(hyp_html, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#475569;font-size:13px;'>No strong alternative hypotheses identified for this scope.</div>", unsafe_allow_html=True)

        unexplained = next((d for d in ctx.drivers if d.name == "Unexplained"), None)
        if unexplained:
            unexp_html = textwrap.dedent(f"""
<div style="margin-top:10px;padding:10px 12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;font-size:13px;color:#475569;">
<b>Unexplained Component:</b> {unexplained.contribution_pct:.1f}% of movement is not captured by current deterministic/correlational drivers.
</div>
""").strip()
            st.markdown(unexp_html, unsafe_allow_html=True)
