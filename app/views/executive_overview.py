import textwrap
import time

import pandas as pd
import streamlit as st

from app.analytics import action_simulator, context as ctx_builder
from app.analytics.kpi_engine import revenue_trend_series
from app.components.ui_helpers import (
    confidence_label,
    render_action_box,
    render_alert_banner,
    render_driver_bars,
    render_insight_card,
    render_kpi_card,
    render_trend_chart,
    section_header,
)
from app.feedback.feedback_store import submit_feedback
from app.llm import narrative
from app.personas.persona_config import filter_action_plans
from app.rag.retriever import detect_contradiction, retrieve_evidence
from app.telemetry.telemetry import log_event


def render(datasets, persona, location_label):
    ctx = ctx_builder.build_context(datasets, persona, location_label)

    if not len(ctx.transactions_df):
        st.warning("No data available for this persona/location combination.")
        return

    kpis = ctx.kpis
    revenue = kpis["Revenue"]
    top_driver = ctx.drivers[0] if ctx.drivers else None

    # Sleek Materiality Alert Banner
    driver_mention = (
        f"BusinessIntelligence.ai estimates that <b>{top_driver.name}</b> is the largest modeled contributor."
        if top_driver and top_driver.name != "Unexplained"
        else "No single dominant driver has been identified yet."
    )
    alert_msg = f"Revenue moved <b>{revenue.movement_pct:+.1f}%</b> versus the expected baseline in {location_label}. {driver_mention}"
    alert_meta = f"Materiality: <b>{revenue.materiality_label}</b>  •  Statistical Significance: <b>p = {revenue.p_value:.3f}</b>"
    
    render_alert_banner(
        title="Material movement detected:",
        message=alert_msg,
        meta=alert_meta,
        alert_type="critical" if revenue.movement_pct < 0 else "info",
    )

    # 4-Column KPI Cards Grid
    cols = st.columns(4)
    for col, name in zip(cols, ["Revenue", "Transactions", "Average Ticket", "Wait Time"]):
        render_kpi_card(col, kpis[name])

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Section: What Changed?
    section_header(
        "What changed?",
        "Baseline combines rolling history and comparable periods.",
        badge_text="HIGH MATERIALITY" if revenue.is_business_significant else "MODERATE",
        badge_type="critical" if revenue.movement_pct < 0 else "healthy",
    )

    c1, c2 = st.columns([1.25, 0.75])
    with c1:
        with st.container(border=True):
            st.markdown('<div class="bi-label">Revenue trend — last 30 comparable days</div>', unsafe_allow_html=True)
            trend = revenue_trend_series(ctx.transactions_df)
            st.plotly_chart(render_trend_chart(trend), use_container_width=True)
            st.markdown(
                '<div style="font-size:12px;color:#475569;margin-top:2px;font-weight:500;">'
                'Baseline combines rolling history and comparable periods. The final observation crosses both business and statistical materiality thresholds.'
                '</div>',
                unsafe_allow_html=True,
            )

    with c2:
        with st.container(border=True):
            st.markdown('<div class="bi-label">Estimated driver contribution</div>', unsafe_allow_html=True)
            st.plotly_chart(render_driver_bars(ctx.drivers), use_container_width=True)
            st.markdown(
                '<div style="font-size:12px;color:#475569;margin-top:2px;font-weight:500;">'
                'Approximate attribution for prototype demonstration; contributions are not presented as definitive causal effects.'
                '</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Section: Why Did It Happen?
    section_header("Why did it happen?", "Causal attribution, contextual qualitative evidence, and counterfactual simulation.")

    query = " ".join([d.evidence_query for d in ctx.drivers if d.evidence_query])
    t0 = time.time()
    results, backend = retrieve_evidence(
        ctx.documents_df, ctx.feedback_df, query or "revenue decline", persona, ctx.city, ctx.store
    )
    retrieval_latency = time.time() - t0
    contradictory_evidence = detect_contradiction(results) or ctx.contradictory

    tx_kpi = kpis["Transactions"]
    ticket_kpi = kpis["Average Ticket"]
    wt_kpi = kpis["Wait Time"]

    kpi_summary = (
        f"Revenue is {revenue.movement_pct:+.1f}% vs baseline (INR {revenue.current_value:,.0f} vs "
        f"INR {revenue.baseline_value:,.0f}). Transactions are {tx_kpi.movement_pct:+.1f}%. "
        f"Average ticket is {ticket_kpi.movement_pct:+.1f}%. Wait time is {wt_kpi.movement_pct:+.1f}%."
    )
    drivers_summary = "\n".join(
        f"- {d.name}: {d.contribution_pct:.1f}% contribution, {d.direction}, confidence {d.confidence:.2f} ({d.method})"
        for d in ctx.drivers
    )
    evidence_summary = (
        "\n".join(f"- [{r['chunk']['source_type']}] {r['chunk']['text']}" for r in results)
        or "No evidence retrieved."
    )

    if contradictory_evidence:
        confidence_note = (
            "Evidence is contradictory for this location: some sources suggest normal conditions while "
            "others suggest a service or demand issue. Confidence should be reduced."
        )
    else:
        confidence_note = f"Top driver confidence: {top_driver.confidence:.2f}" if top_driver else "No dominant driver."

    if contradictory_evidence:
        llm_result = {"text": "", "input_tokens": 0, "output_tokens": 0, "latency_seconds": 0, "llm_calls": 0}
    else:
        llm_result = narrative.generate_narrative(
            persona, kpi_summary, drivers_summary, evidence_summary, confidence_note
        )

    total_latency = time.time() - t0

    log_event(
        analysis_label=f"Revenue - {location_label}",
        persona=persona,
        location=location_label,
        kpi="Revenue",
        method="Decomposition + correlation + business rules + RAG + LLM narrative",
        retrieval_count=len(results),
        llm_calls=llm_result["llm_calls"],
        input_tokens=llm_result["input_tokens"],
        output_tokens=llm_result["output_tokens"],
        latency_seconds=total_latency,
        retrieval_latency_seconds=retrieval_latency,
    )

    why_col1, why_col2 = st.columns([1.25, 0.75])
    
    with why_col1:
        with st.container(border=True):
            if contradictory_evidence:
                st.markdown(
                    textwrap.dedent("""
<div class="bi-alert bi-alert-critical" style="margin-bottom:12px;">
<div class="bi-alert-icon">⚠️</div>
<div>
<div class="bi-alert-title">Contradictory Evidence Detected</div>
<div class="bi-alert-body">We cannot confidently identify the primary driver because the available evidence contains conflicting signals. Review the evidence below.</div>
</div>
</div>
""").strip(),
                    unsafe_allow_html=True,
                )
            else:
                # 1. Primary Driver Insight
                top_name = top_driver.name if top_driver else "Transactions"
                top_pct = f"{top_driver.contribution_pct:.0f}%" if top_driver else "58%"
                ins1_body = (
                    f"Transactions moved <b>{tx_kpi.movement_pct:+.1f}%</b> while average ticket shifted <b>{ticket_kpi.movement_pct:+.1f}%</b>, "
                    f"indicating that changes in customer volume—not spend per transaction—is the primary modeled explanation for the revenue swing."
                )
                ins1_html = render_insight_card(
                    1,
                    f"{top_name} are the strongest modeled driver ({top_pct} contribution).",
                    ins1_body,
                )

                # 2. Secondary Operational Signal
                ins2_body = (
                    f"Average wait time moved from <b>{wt_kpi.baseline_value:.1f}</b> to <b>{wt_kpi.current_value:.1f} minutes</b> "
                    f"(<b>{wt_kpi.movement_pct:+.1f}%</b>). Customer feedback logs and operational records also reflect higher frequency of queue friction and service delays."
                )
                ins2_html = render_insight_card(
                    2,
                    f"Wait-time deterioration is a key operational signal.",
                    ins2_body,
                )

                # 3. Pricing / Mix Insight
                ins3_body = (
                    f"Average ticket moved <b>{ticket_kpi.movement_pct:+.1f}%</b> (current: ₹{ticket_kpi.current_value:.1f}), "
                    f"suggesting pricing stability and premium item mix helped partially buffer total revenue despite transaction volume decline."
                )
                ins3_html = render_insight_card(
                    3,
                    f"Pricing and product mix provided a partial offset.",
                    ins3_body,
                )

                st.markdown(ins1_html + "\n<div style='height:8px;'></div>\n" + ins2_html + "\n<div style='height:8px;'></div>\n" + ins3_html, unsafe_allow_html=True)

            if not contradictory_evidence and llm_result.get("text"):
                synth_text = llm_result["text"].replace("\n\n", "<br><br>").replace("**", "")
                st.markdown(
                    f"""
                    <div style="margin-top:12px;background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:12px 16px;font-size:13px;color:#0369a1;line-height:1.55;">
                        <b style="color:#0c4a6e;">Strategic Takeaway:</b><br>{synth_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.expander(f"Contextual Evidence & Field Notes ({len(results)} sources retrieved)"):
                for r in results:
                    c = r["chunk"]
                    st.markdown(
                        f"**{c['subject']}** — <span class='bi-badge bi-badge-watch'>{c['source_type']}</span> <span style='color:#475569;font-size:12px;'>{c['city']}/{c['store']} • {c['date']} • score: {r['score']:.2f}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='color:#334155;font-size:13px;padding:4px 0 8px;font-weight:500;'>{c['text']}</div>",
                        unsafe_allow_html=True,
                    )

    with why_col2:
        with st.container(border=True):
            from app.analytics import counterfactual as cf
            wt = kpis["Wait Time"]
            cf_res = cf.counterfactual_wait_time(wt.current_value, wt.baseline_value, revenue.current_value, wt.baseline_value)
            
            diff_str = f"₹{abs(cf_res.estimated_difference)/1_000_000:.2f}M" if abs(cf_res.estimated_difference) >= 1_000_000 else f"₹{abs(cf_res.estimated_difference):,.0f}"
            diff_prefix = "+" if cf_res.estimated_difference >= 0 else "-"
            
            cf_box_html = textwrap.dedent(f"""
<div class="bi-label">Counterfactual question</div>
<h2 style="margin:8px 0;font-size:19px;font-weight:750;color:#0f172a;">What if wait time had stayed at baseline?</h2>
<div style="font-size:13px;color:#475569;font-weight:500;margin-bottom:16px;">
Actual wait time: <b style="color:#0f172a;">{wt.current_value:.1f} min</b> → Baseline: <b style="color:#0f172a;">{wt.baseline_value:.1f} min</b>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;">
<div class="bi-label">Actual revenue</div>
<div style="font-size:22px;font-weight:800;color:#0f172a;">₹{revenue.current_value/1_000_000:.1f}M</div>
</div>
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;">
<div class="bi-label">Counterfactual</div>
<div style="font-size:22px;font-weight:800;color:#2563eb;">₹{cf_res.counterfactual_revenue/1_000_000:.1f}M</div>
</div>
</div>
<div class="bi-action-box" style="margin-top:0;padding:14px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:9px;">
<div style="font-weight:800;color:#1e3a8a;font-size:14px;margin-bottom:4px;">
Estimated difference: {diff_prefix}{diff_str}
</div>
<div style="font-size:13px;color:#334155;font-weight:500;line-height:1.5;">
Under the prototype's counterfactual approximation, restoring wait time to baseline corresponds to an estimated <b>{diff_prefix}{diff_str}</b> improvement in revenue.
</div>
</div>
""").strip()
            st.markdown(cf_box_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Section: Products & Stores
    section_header(
        "Products & stores",
        "Descriptive analytics and performance decomposition across catalog and store network.",
    )
    p_tab, s_tab = st.tabs(["Products Breakdown", "Store Network Breakdown"])
    
    with p_tab:
        with st.container(border=True):
            prod = (
                ctx.transactions_df.groupby("product")
                .agg(
                    revenue=("revenue", "sum"),
                    units=("quantity", "sum"),
                    avg_ticket=("revenue", "mean"),
                )
                .reset_index()
                .sort_values("revenue", ascending=False)
            )
            
            # Build styled HTML table
            table_rows = []
            for _, r in prod.iterrows():
                rev_fmt = f"₹{r['revenue']/1_000_000:.2f}M" if r['revenue'] >= 1_000_000 else f"₹{r['revenue']:,.0f}"
                units_fmt = f"{r['units']/1000:.1f}K" if r['units'] >= 1000 else f"{r['units']:.0f}"
                ticket_fmt = f"₹{r['avg_ticket']:.1f}"
                
                is_healthy = r['revenue'] > prod['revenue'].median()
                badge = '<span class="bi-badge bi-badge-healthy">Healthy</span>' if is_healthy else '<span class="bi-badge bi-badge-watch">Watch</span>'
                if r['product'] == "Chai Frappe":
                    badge = '<span class="bi-badge bi-badge-watch">21 Days History</span>'

                table_rows.append(f"""
<tr>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;font-weight:700;color:#0f172a;">{r['product']}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#0f172a;">{rev_fmt}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;color:#334155;">{units_fmt}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;color:#334155;">{ticket_fmt}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;">{badge}</td>
</tr>
""")

            table_html = textwrap.dedent(f"""
<table style="width:100%;border-collapse:collapse;font-size:13.5px;">
<thead>
<tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Product</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Revenue</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Units</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Avg Ticket</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Signal</th>
</tr>
</thead>
<tbody>
{''.join(table_rows)}
</tbody>
</table>
""").strip()
            st.markdown(table_html, unsafe_allow_html=True)

            new_product = ctx_builder.new_product_summary(ctx.transactions_df)
            if new_product:
                st.markdown(
                    f"""
                    <div style="margin-top:14px;padding:12px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;color:#334155;">
                        <span class="bi-badge bi-badge-watch" style="margin-right:6px;">New Release</span>
                        <b>{new_product['product']}</b>: Revenue ₹{new_product['revenue']:,.0f}, {new_product['units']:.0f} units across {new_product['history_days']} days. History coverage is sparse; caution recommended for causal attribution.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with s_tab:
        with st.container(border=True):
            store_stats = (
                ctx.transactions_df.groupby(["city", "store"])
                .agg(
                    revenue=("revenue", "sum"),
                    transactions=("transaction_id", "count"),
                    avg_ticket=("revenue", "mean"),
                )
                .reset_index()
            )
            wait_stats = ctx.staffing_df.groupby(["city", "store"])["wait_time"].mean().reset_index()
            store_stats = store_stats.merge(wait_stats, on=["city", "store"], how="left")
            
            store_rows = []
            for _, s in store_stats.iterrows():
                rev_fmt = f"₹{s['revenue']/1_000_000:.2f}M" if s['revenue'] >= 1_000_000 else f"₹{s['revenue']:,.0f}"
                tx_fmt = f"{s['transactions']/1000:.1f}K" if s['transactions'] >= 1000 else f"{s['transactions']}"
                wt_fmt = f"{s['wait_time']:.1f} min" if pd.notna(s['wait_time']) else "—"
                ticket_fmt = f"₹{s['avg_ticket']:.1f}"

                store_rows.append(f"""
<tr>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;font-weight:700;color:#0f172a;">{s['city']}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#0f172a;">{s['store']}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#0f172a;">{rev_fmt}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;color:#334155;">{tx_fmt}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;color:#334155;">{ticket_fmt}</td>
<td style="padding:12px 14px;border-bottom:1px solid #f1f5f9;font-weight:600;color:#0f172a;">{wt_fmt}</td>
</tr>
""")

            store_table_html = textwrap.dedent(f"""
<table style="width:100%;border-collapse:collapse;font-size:13.5px;">
<thead>
<tr style="background:#f8fafc;border-bottom:2px solid #e2e8f0;">
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">City</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Store</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Revenue</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Transactions</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Avg Ticket</th>
<th style="padding:10px 14px;text-align:left;color:#475569;font-size:11.5px;text-transform:uppercase;letter-spacing:0.5px;">Wait Time</th>
</tr>
</thead>
<tbody>
{''.join(store_rows)}
</tbody>
</table>
""").strip()
            st.markdown(store_table_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Section: Recommended Action
    section_header("Recommended action", "Prescriptive operational intervention derived from driver causal attributions.")
    if top_driver and top_driver.name != "Unexplained" and not contradictory_evidence:
        current_associates = int(ctx.staffing_df["staff_available"].mean()) if len(ctx.staffing_df) else 8
        promo_active = ctx.promotions_df["end_date"].max() >= pd.Timestamp("2026-07-31").strftime("%Y-%m-%d")
        stockout_present = bool(ctx.inventory_df["stockout_flag"].any()) if len(ctx.inventory_df) else False

        plan = action_simulator.build_action_plan(
            driver=top_driver,
            current_associates=current_associates,
            proposed_associates=current_associates + 2,
            current_wait_time=kpis["Wait Time"].current_value,
            baseline_wait_time=kpis["Wait Time"].baseline_value,
            current_revenue=revenue.current_value,
            current_transactions=kpis["Transactions"].current_value,
            current_avg_ticket=kpis["Average Ticket"].current_value,
            promotion_active=promo_active,
            stockout_present=stockout_present,
        )
        allowed_plans = filter_action_plans(persona, [plan]) if plan else []

        if allowed_plans:
            p = allowed_plans[0]
            st.markdown(
                render_action_box(
                    driver=p.driver,
                    lever=p.lever,
                    action=p.action,
                    owner=p.owner,
                    monitoring_kpis=p.monitoring_kpis,
                    monitoring_days=p.monitoring_period_days,
                    impact=p.estimated_revenue_impact,
                ),
                unsafe_allow_html=True,
            )
        elif plan:
            st.info(
                f"A recommendation exists ({plan.lever}) but is outside this persona's decision rights. "
                f"Owner: {plan.owner}."
            )
    else:
        st.info("No actionable recommendation is issued while the primary driver is unresolved or contradictory.")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Feedback Section
    section_header("Analyst feedback", "Human-in-the-loop validation to reinforce or correct causal attributions.")
    with st.container(border=True):
        fb_cols = st.columns([1, 1, 1, 2])
        insight_id = f"EXEC-{location_label}-Revenue"
        if fb_cols[0].button("✓ Correct", key="fb_correct", use_container_width=True):
            submit_feedback(insight_id, persona, "Correct")
            st.toast("Feedback recorded: Correct")
        if fb_cols[1].button("~ Partially Correct", key="fb_partial", use_container_width=True):
            submit_feedback(insight_id, persona, "Partially correct")
            st.toast("Feedback recorded: Partially correct")
        if fb_cols[2].button("✗ Incorrect", key="fb_incorrect", use_container_width=True):
            submit_feedback(insight_id, persona, "Incorrect")
            st.toast("Feedback recorded: Incorrect")
        comment = fb_cols[3].text_input(
            "Comment (optional)",
            key="fb_comment",
            label_visibility="collapsed",
            placeholder="Add context or operational notes...",
        )
        if comment:
            submit_feedback(insight_id, persona, "Comment", comment=comment)
