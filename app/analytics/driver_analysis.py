"""Multi-factor driver analysis.

Combines a deterministic revenue decomposition (transactions x average
ticket), a correlation signal between wait time and transaction volume,
and a handful of business rules (promotion end dates, stockouts) into a
ranked list of candidate drivers. This is the analytical backbone that
the LLM later narrates - the ranking and contribution numbers themselves
are not produced by the LLM.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from app.analytics.kpi_engine import _split_periods
from app.config import settings


@dataclass
class Driver:
    name: str
    contribution_pct: float
    direction: str          # "negative" or "positive" contribution to the KPI movement
    confidence: float
    method: str
    controllable: bool
    evidence_query: str
    explanation: str


def decompose_revenue_drivers(transactions_df):
    """Splits the revenue movement into a transaction-volume effect and a
    pricing/mix effect using a standard volume x price decomposition."""
    current_mask, baseline_mask = _split_periods(transactions_df)
    d = transactions_df.copy()
    d["date"] = pd.to_datetime(d["date"])

    cur = d[current_mask]
    base = d[baseline_mask]

    cur_txn = len(cur)
    base_txn = len(base) / max(settings.BASELINE_LOOKBACK_PERIODS, 1)
    cur_rev = cur["revenue"].sum()
    base_rev = base["revenue"].sum() / max(settings.BASELINE_LOOKBACK_PERIODS, 1)

    cur_ticket = cur_rev / cur_txn if cur_txn else 0
    base_ticket = base_rev / base_txn if base_txn else 0

    delta_txn = cur_txn - base_txn
    delta_ticket = cur_ticket - base_ticket

    volume_effect = delta_txn * base_ticket
    price_mix_effect = delta_ticket * base_txn
    interaction = delta_txn * delta_ticket
    total_delta = cur_rev - base_rev

    if total_delta == 0:
        return {"volume_effect": 0, "price_mix_effect": 0, "interaction": 0, "total_delta": 0}

    return {
        "volume_effect": volume_effect,
        "price_mix_effect": price_mix_effect,
        "interaction": interaction,
        "total_delta": total_delta,
    }


def wait_time_correlation(staffing_df, transactions_df):
    """Correlation between daily wait time and daily transaction count, as a
    rough statistical signal that service speed is linked to volume."""
    s = staffing_df.copy()
    s["date"] = pd.to_datetime(s["date"])
    daily_wait = s.groupby("date")["wait_time"].mean()

    t = transactions_df.copy()
    t["date"] = pd.to_datetime(t["date"])
    daily_txn = t.groupby("date")["transaction_id"].count()

    joined = pd.concat([daily_wait, daily_txn], axis=1, keys=["wait_time", "transactions"]).dropna()
    if len(joined) < 5:
        return 0.0
    return float(joined["wait_time"].corr(joined["transactions"]))


def check_promotion_ended(promotions_df, transactions_df):
    d = transactions_df.copy()
    d["date"] = pd.to_datetime(d["date"])
    current_mask, _ = _split_periods(transactions_df)
    current_start = d[current_mask]["date"].min()

    for _, promo in promotions_df.iterrows():
        end = pd.to_datetime(promo["end_date"])
        if pd.notna(current_start) and end < current_start and (current_start - end).days < 20:
            return True, promo["promotion_id"]
    return False, None


def check_stockout(inventory_df):
    current_mask, _ = _split_periods(inventory_df.rename(columns={"date": "date"}))
    d = inventory_df.copy()
    d["date"] = pd.to_datetime(d["date"])
    recent = d[current_mask]
    stocked_out = recent[recent["stockout_flag"] == True]
    if len(stocked_out):
        products = stocked_out["product"].unique().tolist()
        stores = stocked_out["store"].unique().tolist()
        return True, products, stores
    return False, [], []


def rank_drivers(transactions_df, staffing_df, promotions_df, inventory_df, contradictory=False):
    decomposition = decompose_revenue_drivers(transactions_df)
    total_delta = decomposition["total_delta"]

    drivers = []

    if total_delta != 0:
        vol_pct = abs(decomposition["volume_effect"]) / abs(total_delta) * 100
        drivers.append(Driver(
            name="Transaction Volume",
            contribution_pct=min(vol_pct, 100),
            direction="negative" if decomposition["volume_effect"] < 0 else "positive",
            confidence=0.85 if not contradictory else 0.35,
            method="Volume x price decomposition (deterministic)",
            controllable=True,
            evidence_query="transactions decline staffing wait time footfall",
            explanation=(
                "Change in transaction count, holding average ticket at its baseline value, "
                "explains this share of the revenue movement."
            ),
        ))

        price_pct = abs(decomposition["price_mix_effect"]) / abs(total_delta) * 100
        drivers.append(Driver(
            name="Pricing / Product Mix",
            contribution_pct=min(price_pct, 100),
            direction="negative" if decomposition["price_mix_effect"] < 0 else "positive",
            confidence=0.7,
            method="Volume x price decomposition (deterministic)",
            controllable=True,
            evidence_query="pricing promotion discount average ticket",
            explanation=(
                "Change in average ticket, holding transaction count at its baseline value, "
                "explains this share of the revenue movement."
            ),
        ))

        explained = min(vol_pct, 100) + min(price_pct, 100)
        unexplained_pct = max(0, 100 - explained)
    else:
        unexplained_pct = 0

    corr = wait_time_correlation(staffing_df, transactions_df)
    if abs(corr) > 0.15:
        drivers.append(Driver(
            name="Wait Time / Staffing",
            contribution_pct=round(abs(corr) * 100 * 0.6, 1),
            direction="negative" if corr < 0 else "positive",
            confidence=min(0.8, abs(corr) + 0.2),
            method=f"Correlation analysis (r = {corr:.2f})",
            controllable=True,
            evidence_query="staffing wait time queue understaffed unavailable",
            explanation=(
                "Daily wait time is correlated with daily transaction volume across the "
                "network, consistent with slower service suppressing throughput."
            ),
        ))

    promo_ended, promo_id = check_promotion_ended(promotions_df, transactions_df)
    if promo_ended:
        drivers.append(Driver(
            name="Promotion Ended",
            contribution_pct=12.0,
            direction="negative",
            confidence=0.55,
            method="Business rule: promotion end-date check",
            controllable=True,
            evidence_query="promotion ended campaign discount",
            explanation=f"Promotion {promo_id} ended shortly before the current period began.",
        ))

    stocked_out, products, stores = check_stockout(inventory_df)
    if stocked_out:
        drivers.append(Driver(
            name="Inventory Stockout",
            contribution_pct=8.0,
            direction="negative",
            confidence=0.6,
            method="Business rule: stockout flag check",
            controllable=True,
            evidence_query=f"{products[0] if products else 'product'} stockout out of stock supplier",
            explanation=f"{', '.join(products)} was out of stock at {', '.join(stores)} during the current period.",
        ))

    if unexplained_pct > 0:
        drivers.append(Driver(
            name="Unexplained",
            contribution_pct=round(unexplained_pct, 1),
            direction="n/a",
            confidence=0.0,
            method="Residual after decomposition and business rules",
            controllable=False,
            evidence_query="",
            explanation="Portion of the movement not attributable to the modeled drivers above.",
        ))

    drivers.sort(key=lambda x: x.contribution_pct, reverse=True)
    return drivers
