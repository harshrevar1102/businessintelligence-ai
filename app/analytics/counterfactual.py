"""Counterfactual ("what if") scenario engine.

These are assumption-based simulations, not causal ground truth - each
function documents the business assumption it relies on. They are kept
deterministic on purpose so the LLM never invents the numbers, only
narrates them.
"""

from dataclasses import dataclass

# Business assumptions used purely for simulation purposes in this prototype.
WAIT_TIME_REVENUE_ELASTICITY = 0.025      # % revenue change per 1 minute of wait-time change
STAFFING_MINUTES_PER_ASSOCIATE = 0.6      # wait-time minutes saved per added peak-hour associate
PRICE_DEMAND_ELASTICITY = -0.6            # % transaction change per 1% price change
PROMOTION_REACTIVATION_LIFT = 0.06        # transaction lift if a lapsed promotion is restored
STOCKOUT_RESOLUTION_LIFT = 0.03           # transaction lift at the affected store/product if resolved


@dataclass
class CounterfactualResult:
    lever: str
    actual_value: float
    baseline_value: float
    proposed_value: float
    actual_revenue: float
    counterfactual_revenue: float
    estimated_difference: float
    confidence: str
    assumption: str


def counterfactual_wait_time(current_wait_time, proposed_wait_time, current_revenue, baseline_wait_time):
    delta = current_wait_time - proposed_wait_time
    revenue_change_pct = delta * WAIT_TIME_REVENUE_ELASTICITY
    counterfactual_revenue = current_revenue * (1 + revenue_change_pct)

    return CounterfactualResult(
        lever="Wait Time",
        actual_value=current_wait_time,
        baseline_value=baseline_wait_time,
        proposed_value=proposed_wait_time,
        actual_revenue=current_revenue,
        counterfactual_revenue=counterfactual_revenue,
        estimated_difference=counterfactual_revenue - current_revenue,
        confidence="Medium",
        assumption=f"Assumes a {WAIT_TIME_REVENUE_ELASTICITY*100:.1f}% revenue change per 1 minute of wait-time change.",
    )


def counterfactual_staffing(current_associates, proposed_associates, current_wait_time, current_revenue, baseline_wait_time):
    delta_associates = proposed_associates - current_associates
    implied_wait_time = max(2.0, current_wait_time - delta_associates * STAFFING_MINUTES_PER_ASSOCIATE)
    wt_result = counterfactual_wait_time(current_wait_time, implied_wait_time, current_revenue, baseline_wait_time)

    return CounterfactualResult(
        lever="Peak-hour Staffing",
        actual_value=current_associates,
        baseline_value=current_associates,
        proposed_value=proposed_associates,
        actual_revenue=current_revenue,
        counterfactual_revenue=wt_result.counterfactual_revenue,
        estimated_difference=wt_result.estimated_difference,
        confidence="Medium",
        assumption=(
            f"Assumes each added peak-hour associate reduces wait time by "
            f"~{STAFFING_MINUTES_PER_ASSOCIATE} minutes, then applies the wait-time elasticity."
        ),
    )


def counterfactual_pricing(current_price_change_pct, proposed_price_change_pct, current_transactions, current_avg_ticket):
    delta_price_pct = proposed_price_change_pct - current_price_change_pct
    txn_change_pct = delta_price_pct * PRICE_DEMAND_ELASTICITY
    new_transactions = current_transactions * (1 + txn_change_pct / 100)
    new_avg_ticket = current_avg_ticket * (1 + proposed_price_change_pct / 100)

    current_revenue = current_transactions * current_avg_ticket
    counterfactual_revenue = new_transactions * new_avg_ticket

    return CounterfactualResult(
        lever="Pricing",
        actual_value=current_price_change_pct,
        baseline_value=0.0,
        proposed_value=proposed_price_change_pct,
        actual_revenue=current_revenue,
        counterfactual_revenue=counterfactual_revenue,
        estimated_difference=counterfactual_revenue - current_revenue,
        confidence="Low",
        assumption=f"Assumes a price-demand elasticity of {PRICE_DEMAND_ELASTICITY} (transaction volume falls as price rises).",
    )


def counterfactual_promotion(current_revenue, current_transactions, current_avg_ticket, promotion_active):
    if promotion_active:
        return CounterfactualResult(
            lever="Promotion", actual_value=1, baseline_value=1, proposed_value=1,
            actual_revenue=current_revenue, counterfactual_revenue=current_revenue,
            estimated_difference=0.0, confidence="High", assumption="Promotion is already active.",
        )

    new_transactions = current_transactions * (1 + PROMOTION_REACTIVATION_LIFT)
    counterfactual_revenue = new_transactions * current_avg_ticket

    return CounterfactualResult(
        lever="Promotion",
        actual_value=0, baseline_value=1, proposed_value=1,
        actual_revenue=current_revenue, counterfactual_revenue=counterfactual_revenue,
        estimated_difference=counterfactual_revenue - current_revenue,
        confidence="Low",
        assumption=f"Assumes reactivating the promotion lifts transactions by {PROMOTION_REACTIVATION_LIFT*100:.0f}%.",
    )


def counterfactual_inventory(current_revenue, current_transactions, current_avg_ticket, stockout_present):
    if not stockout_present:
        return CounterfactualResult(
            lever="Inventory", actual_value=1, baseline_value=1, proposed_value=1,
            actual_revenue=current_revenue, counterfactual_revenue=current_revenue,
            estimated_difference=0.0, confidence="High", assumption="No active stockout in this scope.",
        )

    new_transactions = current_transactions * (1 + STOCKOUT_RESOLUTION_LIFT)
    counterfactual_revenue = new_transactions * current_avg_ticket

    return CounterfactualResult(
        lever="Inventory",
        actual_value=0, baseline_value=1, proposed_value=1,
        actual_revenue=current_revenue, counterfactual_revenue=counterfactual_revenue,
        estimated_difference=counterfactual_revenue - current_revenue,
        confidence="Low",
        assumption=f"Assumes resolving the stockout lifts affected-store transactions by {STOCKOUT_RESOLUTION_LIFT*100:.0f}%.",
    )
