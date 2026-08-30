"""Maps a driver to a controllable lever, a concrete action, an owner and a
monitoring plan. Reuses the counterfactual engine to estimate impact so the
numbers shown here stay consistent with the Counterfactuals page.
"""

from dataclasses import dataclass

from app.analytics import counterfactual as cf


@dataclass
class ActionPlan:
    driver: str
    lever: str
    action: str
    expected_impact: str
    owner: str
    confidence: str
    monitoring_kpis: list
    monitoring_period_days: int
    estimated_revenue_impact: float


LEVER_LIBRARY = {
    "Wait Time / Staffing": {
        "lever": "Peak-hour staffing",
        "owner": "Store Operations",
        "monitoring_kpis": ["Wait Time", "Transactions / hour", "Revenue"],
        "monitoring_period_days": 14,
    },
    "Transaction Volume": {
        "lever": "Peak-hour staffing",
        "owner": "Store Operations",
        "monitoring_kpis": ["Transactions", "Wait Time", "Revenue"],
        "monitoring_period_days": 14,
    },
    "Pricing / Product Mix": {
        "lever": "Promotional pricing",
        "owner": "Marketing",
        "monitoring_kpis": ["Average Ticket", "Transactions", "Revenue"],
        "monitoring_period_days": 21,
    },
    "Promotion Ended": {
        "lever": "Campaign reactivation",
        "owner": "Marketing",
        "monitoring_kpis": ["Transactions", "Promotion Usage", "Revenue"],
        "monitoring_period_days": 21,
    },
    "Inventory Stockout": {
        "lever": "Supplier expediting",
        "owner": "Supply Chain",
        "monitoring_kpis": ["Closing Stock", "Product Revenue", "Stockout Flag"],
        "monitoring_period_days": 10,
    },
}


def build_action_plan(driver, current_associates, proposed_associates, current_wait_time,
                       baseline_wait_time, current_revenue, current_transactions, current_avg_ticket,
                       promotion_active, stockout_present):
    config = LEVER_LIBRARY.get(driver.name)
    if config is None:
        return None

    if driver.name in ("Wait Time / Staffing", "Transaction Volume"):
        result = cf.counterfactual_staffing(
            current_associates, proposed_associates, current_wait_time, current_revenue, baseline_wait_time,
        )
        action = f"Increase peak-hour staffing from {current_associates} to {proposed_associates} associates."
        impact_estimate = result.estimated_difference
    elif driver.name == "Pricing / Product Mix":
        result = cf.counterfactual_pricing(0, -2, current_transactions, current_avg_ticket)
        action = "Introduce a small targeted discount to rebuild transaction volume."
        impact_estimate = result.estimated_difference
    elif driver.name == "Promotion Ended":
        result = cf.counterfactual_promotion(current_revenue, current_transactions, current_avg_ticket, promotion_active)
        action = "Reactivate or extend the recently ended promotional campaign."
        impact_estimate = result.estimated_difference
    elif driver.name == "Inventory Stockout":
        result = cf.counterfactual_inventory(current_revenue, current_transactions, current_avg_ticket, stockout_present)
        action = "Expedite supplier delivery to resolve the stockout."
        impact_estimate = result.estimated_difference
    else:
        return None

    confidence = driver.confidence
    confidence_label = "High" if confidence >= 0.75 else "Medium" if confidence >= 0.5 else "Low"

    return ActionPlan(
        driver=driver.name,
        lever=config["lever"],
        action=action,
        expected_impact=f"Estimated revenue impact: INR {impact_estimate:,.0f}",
        owner=config["owner"],
        confidence=confidence_label,
        monitoring_kpis=config["monitoring_kpis"],
        monitoring_period_days=config["monitoring_period_days"],
        estimated_revenue_impact=impact_estimate,
    )
