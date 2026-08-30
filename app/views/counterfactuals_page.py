import textwrap
import streamlit as st

from app.analytics import context as ctx_builder, counterfactual as cf
from app.components.ui_helpers import section_header


def render(datasets, persona, location_label):
    ctx = ctx_builder.build_context(datasets, persona, location_label)
    if not len(ctx.transactions_df):
        st.warning("No data available for this persona/location combination.")
        return

    kpis = ctx.kpis
    
    col_sel, _ = st.columns([1.5, 2.5])
    with col_sel:
        lever = st.selectbox("Select Business Lever", ["Wait Time", "Staffing", "Pricing", "Promotion", "Inventory"])

    section_header(f"Counterfactual Simulation: {lever}", "Simulate alternative policy scenarios and estimate causal revenue response.")

    with st.container(border=True):
        if lever == "Wait Time":
            current = kpis["Wait Time"].current_value
            baseline = kpis["Wait Time"].baseline_value
            proposed = st.slider("Proposed wait time (minutes)", 2.0, 12.0, float(round(baseline, 1)), 0.1)
            result = cf.counterfactual_wait_time(current, proposed, kpis["Revenue"].current_value, baseline)

        elif lever == "Staffing":
            current_associates = int(ctx.staffing_df["staff_available"].mean()) if len(ctx.staffing_df) else 8
            proposed_associates = st.slider("Proposed peak-hour associates per store", 3, 15, current_associates + 2)
            result = cf.counterfactual_staffing(
                current_associates,
                proposed_associates,
                kpis["Wait Time"].current_value,
                kpis["Revenue"].current_value,
                kpis["Wait Time"].baseline_value,
            )

        elif lever == "Pricing":
            proposed_change = st.slider("Proposed price adjustment (%)", -10.0, 10.0, 0.0, 0.5)
            result = cf.counterfactual_pricing(
                0,
                proposed_change,
                kpis["Transactions"].current_value,
                kpis["Average Ticket"].current_value,
            )

        elif lever == "Promotion":
            promo_active = st.toggle("Promotion active in simulation window", value=False)
            result = cf.counterfactual_promotion(
                kpis["Revenue"].current_value,
                kpis["Transactions"].current_value,
                kpis["Average Ticket"].current_value,
                promo_active,
            )

        else:
            stockout_present = bool(ctx.inventory_df["stockout_flag"].any()) if len(ctx.inventory_df) else False
            st.markdown(
                f"<div style='font-size:14px;color:#1e293b;margin-bottom:12px;'>Current stockout present in scope: <b>{stockout_present}</b></div>",
                unsafe_allow_html=True,
            )
            result = cf.counterfactual_inventory(
                kpis["Revenue"].current_value,
                kpis["Transactions"].current_value,
                kpis["Average Ticket"].current_value,
                stockout_present,
            )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 3 Comparison Metric Cards
    c1, c2, c3 = st.columns(3)
    diff_val = result.estimated_difference
    diff_prefix = "+" if diff_val >= 0 else "-"
    diff_str = f"₹{abs(diff_val)/1_000_000:.2f}M" if abs(diff_val) >= 1_000_000 else f"₹{abs(diff_val):,.0f}"

    with c1:
        c1_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Observed Actual Revenue</div>
<div class="bi-value">₹{result.actual_revenue/1_000_000:.2f}M</div>
<div style="font-size:12px;color:#475569;">Observed in analysis window</div>
</div>
""").strip()
        st.markdown(c1_html, unsafe_allow_html=True)

    with c2:
        c2_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Counterfactual Revenue</div>
<div class="bi-value" style="color:#2563eb;">₹{result.counterfactual_revenue/1_000_000:.2f}M</div>
<div style="font-size:12px;color:#475569;">Modeled response</div>
</div>
""").strip()
        st.markdown(c2_html, unsafe_allow_html=True)

    with c3:
        c3_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">Estimated Difference</div>
<div class="bi-value" style="color:{'#16a34a' if diff_val >= 0 else '#dc2626'};">{diff_prefix}{diff_str}</div>
<div style="font-size:12px;color:#475569;">Confidence: <b>{result.confidence}</b></div>
</div>
""").strip()
        st.markdown(c3_html, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    assump_html = textwrap.dedent(f"""
<div class="bi-action-box">
<div style="font-size:13.5px;font-weight:700;color:#1e3a8a;margin-bottom:4px;">Underlying Model Assumption:</div>
<div style="font-size:13px;color:#334155;line-height:1.5;">{result.assumption}</div>
</div>
""").strip()
    st.markdown(assump_html, unsafe_allow_html=True)
