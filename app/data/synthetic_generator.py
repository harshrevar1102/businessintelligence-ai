"""Generates synthetic CafeCo data in memory.

Nothing is written to disk here on purpose - the data/synthetic folder in
this repo is intentionally left empty. Every dataframe below is built
fresh (with a fixed random seed for reproducibility) each time the app
starts, which also means this module doubles as documentation of the
data model: column names, grains and refresh cadences are all defined
here in one place.

The datasets are deliberately built with different grains and refresh
cadences (see loader.py for the metadata that describes this), and a
handful of scenarios are seeded on purpose:

- a staffing shortage at the Mumbai / Bandra store, with a supporting
  internal email
- a Cold Brew stockout in Delhi
- a promotion that ended partway through the current period
- a newly launched product (Chai Frappe) with only ~21 days of history
- contradictory evidence between an internal email and customer feedback
  at the Ahmedabad store
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from app.config import settings


def _date_range(days_back):
    end = datetime(2026, 7, 31)
    return [end - timedelta(days=i) for i in range(days_back)][::-1]


def _rng():
    return np.random.default_rng(settings.RANDOM_SEED)


def generate_transactions():
    rng = _rng()
    dates = _date_range(settings.DATA_HISTORY_DAYS)
    rows = []
    txn_id = 1

    base_price = {
        "House Latte": 129,
        "Cold Brew": 155,
        "Breakfast Combo": 160,
        "Cappuccino": 119,
        settings.NEW_PRODUCT: 148,
    }

    for date in dates:
        day_index = (date - dates[0]).days
        is_current_period = day_index >= settings.DATA_HISTORY_DAYS - settings.CURRENT_PERIOD_DAYS

        for city, stores in settings.STORES.items():
            for store in stores:
                base_daily_txns = rng.integers(140, 220)

                # scripted demand shock: revenue decline nationwide during the
                # current period, driven mostly by lower transaction volume
                demand_multiplier = 1.0
                if is_current_period:
                    demand_multiplier = 0.83
                if city == "Mumbai" and store == "Bandra" and is_current_period:
                    demand_multiplier *= 0.90  # staffing shortage compounds it
                if city == "Delhi" and is_current_period and day_index > settings.DATA_HISTORY_DAYS - 15:
                    demand_multiplier *= 0.92  # Cold Brew stockout effect

                n_txns = max(20, int(base_daily_txns * demand_multiplier))

                for _ in range(n_txns):
                    product = rng.choice(
                        settings.PRODUCTS,
                        p=[0.32, 0.24, 0.18, 0.18, 0.08],
                    )
                    if product == settings.NEW_PRODUCT:
                        launch_day = settings.DATA_HISTORY_DAYS - settings.NEW_PRODUCT_LAUNCH_DAYS_AGO
                        if day_index < launch_day:
                            product = "House Latte"

                    price = base_price[product] * rng.normal(1.0, 0.03)
                    # small price/mix uplift in the current period, partially offsetting volume decline
                    if is_current_period:
                        price *= 1.014
                    if product == "Cold Brew" and city == "Delhi" and is_current_period and day_index > settings.DATA_HISTORY_DAYS - 15:
                        continue  # stocked out, no sales possible

                    qty = rng.choice([1, 1, 1, 2])
                    revenue = round(price * qty, 2)

                    rows.append({
                        "transaction_id": f"TXN{txn_id:07d}",
                        "date": date.date().isoformat(),
                        "time": f"{rng.integers(7, 21):02d}:{rng.integers(0, 59):02d}",
                        "city": city,
                        "store": store,
                        "product": product,
                        "quantity": int(qty),
                        "price": round(price, 2),
                        "revenue": revenue,
                        "promotion_id": "PROMO-SUMMER24" if (date.month == 7 and date.day <= 15) else None,
                        "customer_segment": rng.choice(["Regular", "New", "Loyalty"], p=[0.55, 0.25, 0.2]),
                    })
                    txn_id += 1

    return pd.DataFrame(rows)


def generate_staffing():
    rng = _rng()
    dates = _date_range(settings.DATA_HISTORY_DAYS)
    rows = []

    for date in dates:
        day_index = (date - dates[0]).days
        is_current_period = day_index >= settings.DATA_HISTORY_DAYS - settings.CURRENT_PERIOD_DAYS

        for city, stores in settings.STORES.items():
            for store in stores:
                for hour in range(7, 21):
                    scheduled = rng.integers(6, 10)
                    available = scheduled
                    if city == "Mumbai" and store == "Bandra" and is_current_period and 18 <= hour <= 21:
                        available = max(3, scheduled - 3)  # three associates unavailable, evening only

                    base_wait = 6.0 + rng.normal(0, 0.4)
                    wait_time = base_wait
                    if available < scheduled:
                        wait_time += (scheduled - available) * 0.6
                    if is_current_period:
                        wait_time += 0.3  # mild general service pressure across the network

                    rows.append({
                        "date": date.date().isoformat(),
                        "hour": hour,
                        "city": city,
                        "store": store,
                        "staff_available": int(available),
                        "staff_scheduled": int(scheduled),
                        "wait_time": round(max(2.5, wait_time), 2),
                        "service_capacity": int(available * 12),
                    })

    return pd.DataFrame(rows)


def generate_inventory():
    rng = _rng()
    dates = _date_range(settings.DATA_HISTORY_DAYS)
    rows = []

    for date in dates:
        day_index = (date - dates[0]).days
        is_current_period = day_index >= settings.DATA_HISTORY_DAYS - settings.CURRENT_PERIOD_DAYS
        stockout_window = city_is_delhi_stockout = is_current_period and day_index > settings.DATA_HISTORY_DAYS - 15

        for city, stores in settings.STORES.items():
            for store in stores:
                for product in settings.PRODUCTS:
                    opening = rng.integers(40, 120)
                    received = rng.integers(20, 60)
                    sold = rng.integers(15, 55)
                    stockout = False
                    if product == "Cold Brew" and city == "Delhi" and stockout_window:
                        sold = min(sold, opening)
                        opening = 0
                        received = 0
                        stockout = True
                    closing = max(0, opening + received - sold)

                    rows.append({
                        "date": date.date().isoformat(),
                        "city": city,
                        "store": store,
                        "product": product,
                        "opening_stock": int(opening),
                        "received_stock": int(received),
                        "units_sold": int(sold),
                        "closing_stock": int(closing),
                        "stockout_flag": bool(stockout),
                    })

    return pd.DataFrame(rows)


def generate_promotions():
    return pd.DataFrame([
        {
            "promotion_id": "PROMO-SUMMER24",
            "start_date": "2026-06-01",
            "end_date": "2026-07-15",
            "store": "All",
            "product": "All",
            "discount": 0.10,
            "campaign_type": "Seasonal",
        },
        {
            "promotion_id": "PROMO-COLDBREW-JUN",
            "start_date": "2026-06-10",
            "end_date": "2026-06-30",
            "store": "All",
            "product": "Cold Brew",
            "discount": 0.15,
            "campaign_type": "Product Push",
        },
    ])


def generate_feedback():
    rng = _rng()
    dates = _date_range(settings.CURRENT_PERIOD_DAYS)
    rows = []
    fb_id = 1

    templates = {
        "wait": [
            "Waited far too long to get my order today.",
            "Queue was really slow during the evening rush.",
            "Service felt understaffed, long wait for a simple coffee.",
        ],
        "normal_traffic": [
            "Store felt about as busy as usual, nothing unusual.",
            "Quick visit, no real wait, same as always.",
        ],
        "stockout": [
            "Wanted Cold Brew but they were out of it again.",
            "Disappointed that Cold Brew was unavailable.",
        ],
        "positive": [
            "Loved the new Chai Frappe, will order again.",
            "Great service and friendly staff as usual.",
        ],
    }

    for date in dates:
        for city, stores in settings.STORES.items():
            for store in stores:
                n = rng.integers(1, 4)
                for _ in range(n):
                    if city == "Mumbai" and store == "Bandra":
                        topic = rng.choice(["wait", "wait", "positive"])
                    elif city == "Ahmedabad" and store == "Satellite":
                        # contradictory-evidence scenario: feedback says traffic is normal
                        topic = rng.choice(["normal_traffic", "normal_traffic", "positive"])
                    elif city == "Delhi":
                        topic = rng.choice(["stockout", "positive", "normal_traffic"])
                    else:
                        topic = rng.choice(["normal_traffic", "positive", "wait"], p=[0.5, 0.35, 0.15])

                    rows.append({
                        "feedback_id": f"FB{fb_id:06d}",
                        "date": date.date().isoformat(),
                        "city": city,
                        "store": store,
                        "text": rng.choice(templates[topic]),
                        "rating": {"wait": 2, "stockout": 2, "normal_traffic": 4, "positive": 5}[topic],
                        "topic": topic,
                    })
                    fb_id += 1

    return pd.DataFrame(rows)


def generate_documents():
    rows = [
        {
            "document_id": "DOC-EMAIL-001",
            "date": "2026-07-20",
            "sender_role": "Store Manager",
            "city": "Mumbai",
            "store": "Bandra",
            "subject": "Evening staffing gap this week",
            "content": (
                "Three associates at the Bandra store are unavailable this week due to "
                "medical leave and a scheduling conflict. Evening coverage between 6 and 9 PM "
                "will be reduced from 9 to about 6 staff. Expect longer queue times during "
                "peak hours until replacements are confirmed."
            ),
            "source_type": "internal_email",
            "sensitivity": "internal",
        },
        {
            "document_id": "DOC-OPS-002",
            "date": "2026-07-22",
            "sender_role": "Operations Manager",
            "city": "Mumbai",
            "store": "Bandra",
            "subject": "Weekly operations report - Bandra",
            "content": (
                "Wait time at Bandra has climbed noticeably this week, correlating with the "
                "reduced evening headcount flagged earlier. Transaction volume at this store "
                "is down relative to the last comparable period. Recommend prioritising "
                "temporary staff for the 6-9 PM shift."
            ),
            "source_type": "operations_report",
            "sensitivity": "internal",
        },
        {
            "document_id": "DOC-EMAIL-003",
            "date": "2026-07-18",
            "sender_role": "Store Manager",
            "city": "Delhi",
            "store": "Connaught Place",
            "subject": "Cold Brew out of stock",
            "content": (
                "Cold Brew has been out of stock at both Delhi stores since mid-July following "
                "a delayed supplier delivery. We are turning away Cold Brew orders and "
                "substituting with Cappuccino where customers agree."
            ),
            "source_type": "internal_email",
            "sensitivity": "internal",
        },
        {
            "document_id": "DOC-EMAIL-004",
            "date": "2026-07-24",
            "sender_role": "Store Manager",
            "city": "Ahmedabad",
            "store": "Satellite",
            "subject": "Footfall looks normal this week",
            "content": (
                "Just a quick note that footfall at Satellite looks completely normal this "
                "week, no unusual drop that I can see on the floor. Team hasn't reported any "
                "issues."
            ),
            "source_type": "internal_email",
            "sensitivity": "internal",
        },
        {
            "document_id": "DOC-OPS-005",
            "date": "2026-07-25",
            "sender_role": "Regional Manager",
            "city": "Ahmedabad",
            "store": "Satellite",
            "subject": "Ahmedabad transaction dip - unclear cause",
            "content": (
                "Sales data shows a transaction decline at the Ahmedabad Satellite store this "
                "period, but this conflicts with the store manager's note that footfall looked "
                "normal, and customer feedback for the store is also mostly neutral to "
                "positive. Cause is unclear pending further investigation."
            ),
            "source_type": "operations_report",
            "sensitivity": "internal",
        },
        {
            "document_id": "DOC-MKT-006",
            "date": "2026-07-16",
            "sender_role": "Marketing Manager",
            "city": "All",
            "store": "All",
            "subject": "Summer promotion ended",
            "content": (
                "The PROMO-SUMMER24 discount campaign ended on July 15. We should expect some "
                "softening in transaction volume in stores that over-indexed on promo-driven "
                "footfall, particularly for price-sensitive segments."
            ),
            "source_type": "internal_email",
            "sensitivity": "internal",
        },
        {
            "document_id": "DOC-PROD-007",
            "date": "2026-07-27",
            "sender_role": "Marketing Manager",
            "city": "All",
            "store": "All",
            "subject": "Chai Frappe early performance",
            "content": (
                "Chai Frappe launched three weeks ago and is showing encouraging early sales, "
                "but we only have about three weeks of history so far, which is not enough to "
                "draw firm conclusions about its trend or seasonality."
            ),
            "source_type": "internal_email",
            "sensitivity": "internal",
        },
    ]
    return pd.DataFrame(rows)


def generate_all():
    """Returns a dict of every synthetic dataframe, freshly generated."""
    return {
        "transactions": generate_transactions(),
        "staffing": generate_staffing(),
        "inventory": generate_inventory(),
        "promotions": generate_promotions(),
        "feedback": generate_feedback(),
        "documents": generate_documents(),
    }
