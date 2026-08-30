"""Deterministic KPI calculations: current value, baseline, movement and materiality.

Nothing in this file calls an LLM. The LLM only narrates numbers that are
already computed here, which is the point - quantitative truth comes from
pandas and scipy, not from a language model.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from app.config import settings


@dataclass
class KPIResult:
    name: str
    unit: str
    current_value: float
    baseline_value: float
    movement_pct: float
    movement_abs: float
    is_statistically_significant: bool
    p_value: float
    is_business_significant: bool
    materiality_score: float
    materiality_label: str


def _split_periods(df, date_col="date"):
    dates = pd.to_datetime(df[date_col])
    max_date = dates.max()
    current_start = max_date - pd.Timedelta(days=settings.CURRENT_PERIOD_DAYS - 1)
    current_mask = dates >= current_start

    baseline_end = current_start - pd.Timedelta(days=1)
    baseline_start = baseline_end - pd.Timedelta(
        days=settings.CURRENT_PERIOD_DAYS * settings.BASELINE_LOOKBACK_PERIODS - 1
    )
    baseline_mask = (dates >= baseline_start) & (dates <= baseline_end)

    return current_mask, baseline_mask


def _daily_series(df, current_mask, baseline_mask, value_col, date_col="date", agg="sum"):
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col])
    current_daily = d[current_mask].groupby(date_col)[value_col].agg(agg)
    baseline_daily = d[baseline_mask].groupby(date_col)[value_col].agg(agg)
    return current_daily, baseline_daily


def _materiality(current_daily, baseline_daily, current_total, baseline_total):
    movement_abs = current_total - baseline_total
    business_significant = abs(movement_abs) >= settings.MATERIALITY_BUSINESS_IMPACT_INR

    p_value = 1.0
    stat_significant = False
    if len(current_daily) >= 5 and len(baseline_daily) >= 5:
        try:
            _, p_value = stats.ttest_ind(current_daily.values, baseline_daily.values, equal_var=False)
            stat_significant = p_value < settings.MATERIALITY_P_VALUE_THRESHOLD
        except Exception:
            p_value = 1.0

    if business_significant and stat_significant:
        score, label = 0.9, "High"
    elif business_significant or stat_significant:
        score, label = 0.6, "Medium"
    else:
        score, label = 0.2, "Low"

    return stat_significant, p_value, business_significant, score, label


def compute_revenue_kpi(transactions_df):
    current_mask, baseline_mask = _split_periods(transactions_df)
    current_daily, baseline_daily = _daily_series(transactions_df, current_mask, baseline_mask, "revenue")

    current_total = float(current_daily.sum()) if len(current_daily) else 0.0
    baseline_total_period = float(baseline_daily.sum()) / max(settings.BASELINE_LOOKBACK_PERIODS, 1) if len(baseline_daily) else 0.0

    stat_sig, p_value, biz_sig, score, label = _materiality(current_daily, baseline_daily, current_total, baseline_total_period)
    movement_pct = ((current_total - baseline_total_period) / baseline_total_period * 100) if baseline_total_period else 0.0

    return KPIResult(
        name="Revenue", unit="INR",
        current_value=current_total, baseline_value=baseline_total_period,
        movement_pct=movement_pct, movement_abs=current_total - baseline_total_period,
        is_statistically_significant=stat_sig, p_value=p_value,
        is_business_significant=biz_sig, materiality_score=score, materiality_label=label,
    )


def compute_transactions_kpi(transactions_df):
    current_mask, baseline_mask = _split_periods(transactions_df)
    current_daily, baseline_daily = _daily_series(transactions_df, current_mask, baseline_mask, "transaction_id", agg="count")

    current_total = float(current_daily.sum()) if len(current_daily) else 0.0
    baseline_total_period = float(baseline_daily.sum()) / max(settings.BASELINE_LOOKBACK_PERIODS, 1) if len(baseline_daily) else 0.0

    stat_sig, p_value, biz_sig, score, label = _materiality(
        current_daily, baseline_daily, current_total, baseline_total_period,
    )
    movement_pct = ((current_total - baseline_total_period) / baseline_total_period * 100) if baseline_total_period else 0.0

    return KPIResult(
        name="Transactions", unit="count",
        current_value=current_total, baseline_value=baseline_total_period,
        movement_pct=movement_pct, movement_abs=current_total - baseline_total_period,
        is_statistically_significant=stat_sig, p_value=p_value,
        is_business_significant=biz_sig, materiality_score=score, materiality_label=label,
    )


def compute_avg_ticket_kpi(revenue_result, transactions_result):
    current_value = revenue_result.current_value / transactions_result.current_value if transactions_result.current_value else 0
    baseline_value = revenue_result.baseline_value / transactions_result.baseline_value if transactions_result.baseline_value else 0
    movement_pct = ((current_value - baseline_value) / baseline_value * 100) if baseline_value else 0.0

    return KPIResult(
        name="Average Ticket", unit="INR",
        current_value=current_value, baseline_value=baseline_value,
        movement_pct=movement_pct, movement_abs=current_value - baseline_value,
        is_statistically_significant=False, p_value=1.0,
        is_business_significant=abs(movement_pct) >= 2,
        materiality_score=0.4 if abs(movement_pct) >= 2 else 0.1,
        materiality_label="Medium" if abs(movement_pct) >= 2 else "Low",
    )


def compute_wait_time_kpi(staffing_df):
    current_mask, baseline_mask = _split_periods(staffing_df)
    current_daily, baseline_daily = _daily_series(staffing_df, current_mask, baseline_mask, "wait_time", agg="mean")

    current_value = float(current_daily.mean()) if len(current_daily) else 0.0
    baseline_value = float(baseline_daily.mean()) if len(baseline_daily) else 0.0

    stat_sig, p_value, biz_sig, score, label = _materiality(current_daily, baseline_daily, current_value, baseline_value)
    movement_pct = ((current_value - baseline_value) / baseline_value * 100) if baseline_value else 0.0

    return KPIResult(
        name="Wait Time", unit="minutes",
        current_value=current_value, baseline_value=baseline_value,
        movement_pct=movement_pct, movement_abs=current_value - baseline_value,
        is_statistically_significant=stat_sig, p_value=p_value,
        is_business_significant=biz_sig, materiality_score=score, materiality_label=label,
    )


def compute_all_kpis(transactions_df, staffing_df):
    revenue = compute_revenue_kpi(transactions_df)
    transactions = compute_transactions_kpi(transactions_df)
    avg_ticket = compute_avg_ticket_kpi(revenue, transactions)
    wait_time = compute_wait_time_kpi(staffing_df)
    return {
        "Revenue": revenue,
        "Transactions": transactions,
        "Average Ticket": avg_ticket,
        "Wait Time": wait_time,
    }


def revenue_trend_series(transactions_df):
    """Daily revenue for charting, plus the baseline mean as a flat reference line."""
    d = transactions_df.copy()
    d["date"] = pd.to_datetime(d["date"])
    daily = d.groupby("date")["revenue"].sum().reset_index().sort_values("date")

    current_mask, baseline_mask = _split_periods(transactions_df)
    baseline_daily_mean = d[baseline_mask].groupby("date")["revenue"].sum().mean()

    daily["baseline"] = baseline_daily_mean
    daily["is_current_period"] = pd.to_datetime(daily["date"]) >= (
        pd.to_datetime(transactions_df["date"]).max() - pd.Timedelta(days=settings.CURRENT_PERIOD_DAYS - 1)
    )
    return daily
