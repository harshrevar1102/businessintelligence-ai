import textwrap
import pandas as pd
import streamlit as st

from app.analytics import action_simulator, context as ctx_builder
from app.components.ui_helpers import render_action_box, section_header
from app.personas.persona_config import can_act_on


def render(datasets, persona, location_label):
    ctx = ctx_builder.build_context(datasets, persona, location_label)
    if not len(ctx.transactions_df):
        st.warning("No data available for this persona/location combination.")
        return

    kpis = ctx.kpis
    driver_names = [d.name for d in ctx.drivers if d.name in action_simulator.LEVER_LIBRARY]
    if not driver_names:
        st.info("No controllable driver identified for this scope yet.")
        return

    col_sel, _ = st.columns([1.5, 2.5])
    with col_sel:
        driver_choice = st.selectbox("Select Controllable Driver", driver_names)
    
    driver = next(d for d in ctx.drivers if d.name == driver_choice)
    config = action_simulator.LEVER_LIBRARY[driver_choice]

    with st.container(border=True):
        # Staffing controls
        current_associates = int(ctx.staffing_df["staff_available"].mean()) if len(ctx.staffing_df) else 8
        proposed_associates = (
            st.slider("Proposed peak-hour associates per store", 3, 15, current_associates + 2)
            if config["lever"] == "Peak-hour staffing"
            else current_associates
        )

        # Pricing controls
        proposed_price_change = (
            st.slider("Proposed price adjustment (%)", -10.0, 10.0, -2.0, 0.5,
                     help="Negative values = discount, Positive values = price increase")
            if config["lever"] == "Promotional pricing"
            else -2.0
        )

        # Promotion controls
        promo_active = ctx.promotions_df["end_date"].max() >= pd.Timestamp("2026-07-31").strftime("%Y-%m-%d")
        proposed_promo_reactivate = (
            st.checkbox("Reactivate promotional campaign", value=True,
                       help="Simulate reactivating or extending the promotional campaign")
            if config["lever"] == "Campaign reactivation"
            else True
        )

        # Inventory controls
        stockout_present = bool(ctx.inventory_df["stockout_flag"].any()) if len(ctx.inventory_df) else False
        if config["lever"] == "Supplier expediting":
            st.markdown(
                f"<div style='font-size:14px;color:#1e293b;margin-bottom:8px;'>Current stockout present: <b>{stockout_present}</b></div>",
                unsafe_allow_html=True,
            )
        proposed_stockout_resolve = (
            st.checkbox("Expedite supplier delivery to resolve stockout", value=True,
                       help="Simulate expediting delivery to resolve the stockout")
            if config["lever"] == "Supplier expediting"
            else True
        )

    plan = action_simulator.build_action_plan(
        driver=driver,
        current_associates=current_associates,
        proposed_associates=proposed_associates,
        current_wait_time=kpis["Wait Time"].current_value,
        baseline_wait_time=kpis["Wait Time"].baseline_value,
        current_revenue=kpis["Revenue"].current_value,
        current_transactions=kpis["Transactions"].current_value,
        current_avg_ticket=kpis["Average Ticket"].current_value,
        promotion_active=promo_active,
        stockout_present=stockout_present,
        proposed_price_change=proposed_price_change,
        proposed_promo_reactivate=proposed_promo_reactivate,
        proposed_stockout_resolve=proposed_stockout_resolve,
    )

    if plan is None:
        st.info("No action plan available for this driver.")
        return

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    section_header("Prescriptive Action Specification", "Detailed operational execution plan and entitlement ownership.")

    st.markdown(
        render_action_box(
            driver=plan.driver,
            lever=plan.lever,
            action=plan.action,
            owner=plan.owner,
            monitoring_kpis=plan.monitoring_kpis,
            monitoring_days=plan.monitoring_period_days,
            impact=plan.estimated_revenue_impact,
        ),
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Entitlement Status Box
    if not can_act_on(persona, plan.lever):
        ent_html = textwrap.dedent(f"""
<div class="bi-alert bi-alert-info">
<div class="bi-alert-icon">🔒</div>
<div>
<div class="bi-alert-title">Decision Rights Boundary</div>
<div class="bi-alert-body">This lever is outside <b>{persona}</b>'s decision authority in this governance model. Assigned owner: <b>{plan.owner}</b>.</div>
</div>
</div>
""").strip()
        st.markdown(ent_html, unsafe_allow_html=True)
