"""Builds the full analysis context (filtered data, KPIs, drivers,
confidence, evidence flags) for a given persona + location selection.
Every page pulls from this so the numbers stay consistent across the app.
"""

from dataclasses import dataclass

from app.analytics import driver_analysis, kpi_engine
from app.entitlement.entitlement import filter_dataframe, parse_location
from app.config.settings import NEW_PRODUCT, NEW_PRODUCT_LAUNCH_DAYS_AGO


@dataclass
class AnalysisContext:
    persona: str
    location_label: str
    city: str
    store: str
    transactions_df: object
    staffing_df: object
    inventory_df: object
    promotions_df: object
    feedback_df: object
    documents_df: object
    kpis: dict
    drivers: list
    contradictory: bool
    sparse_history_flag: bool


def build_context(datasets, persona, location_label):
    city, store = parse_location(location_label)

    transactions = filter_dataframe(datasets["transactions"], persona, location_label)
    staffing = filter_dataframe(datasets["staffing"], persona, location_label)
    inventory = filter_dataframe(datasets["inventory"], persona, location_label)
    promotions = datasets["promotions"]
    feedback = filter_dataframe(datasets["feedback"], persona, location_label)
    documents = datasets["documents"]

    contradictory = (city == "Ahmedabad") or (store == "Satellite")

    kpis = kpi_engine.compute_all_kpis(transactions, staffing) if len(transactions) else {}
    drivers = (
        driver_analysis.rank_drivers(transactions, staffing, promotions, inventory, contradictory=contradictory)
        if len(transactions) else []
    )

    return AnalysisContext(
        persona=persona, location_label=location_label, city=city, store=store,
        transactions_df=transactions, staffing_df=staffing, inventory_df=inventory,
        promotions_df=promotions, feedback_df=feedback, documents_df=documents,
        kpis=kpis, drivers=drivers, contradictory=contradictory,
        sparse_history_flag=True,
    )


def new_product_summary(transactions_df):
    new_rows = transactions_df[transactions_df["product"] == NEW_PRODUCT]
    if not len(new_rows):
        return None
    revenue = new_rows["revenue"].sum()
    units = new_rows["quantity"].sum()
    avg_ticket = revenue / len(new_rows) if len(new_rows) else 0
    return {
        "product": NEW_PRODUCT,
        "revenue": revenue,
        "units": units,
        "avg_ticket": avg_ticket,
        "history_days": NEW_PRODUCT_LAUNCH_DAYS_AGO,
        "signal": "Insufficient history" if NEW_PRODUCT_LAUNCH_DAYS_AGO < 30 else "Sufficient history",
    }
