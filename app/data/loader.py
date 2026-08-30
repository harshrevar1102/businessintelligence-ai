"""Loads the synthetic datasets and the metadata that describes them.

data/synthetic/ can either hold the committed CSV files (transactions.csv,
staffing.csv, inventory.csv, promotions.csv, feedback.csv, documents.csv)
or be empty. If the CSVs are present, they're loaded directly so every
run of the app sees the exact same data that's checked into the repo. If
they're missing, generate_all() builds an equivalent dataset in memory on
the fly, so the app still works out of the box. Either way,
get_datasets() wraps the result with Streamlit's cache so this only runs
once per session.
"""

import os

import pandas as pd
import streamlit as st

from app.data.synthetic_generator import generate_all

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "synthetic")

DATASET_FILES = {
    "transactions": "transactions.csv",
    "staffing": "staffing.csv",
    "inventory": "inventory.csv",
    "promotions": "promotions.csv",
    "feedback": "feedback.csv",
    "documents": "documents.csv",
}

BOOLEAN_COLUMNS = {"inventory": ["stockout_flag"]}

SOURCE_METADATA = [
    {
        "source_name": "Sales Transactions",
        "source_type": "Structured",
        "grain": "Transaction / day / store",
        "refresh_cadence": "Daily",
        "last_refresh": "2026-07-31 06:00",
        "historical_coverage": "120 days",
        "data_quality": "Fresh",
        "owner": "Sales Data Engineering",
        "lineage": "POS system -> daily batch ETL -> transactions table",
        "access_restriction": "None",
    },
    {
        "source_name": "Operations / Staffing",
        "source_type": "Structured",
        "grain": "Store / hour / day",
        "refresh_cadence": "Hourly",
        "last_refresh": "2026-07-31 20:00",
        "historical_coverage": "120 days",
        "data_quality": "Fresh",
        "owner": "Store Operations",
        "lineage": "Workforce scheduling system -> hourly sync",
        "access_restriction": "None",
    },
    {
        "source_name": "Inventory",
        "source_type": "Structured",
        "grain": "Store / product / day",
        "refresh_cadence": "Daily",
        "last_refresh": "2026-07-30 22:00",
        "historical_coverage": "120 days",
        "data_quality": "Stale (last refresh > 24h)",
        "owner": "Supply Chain",
        "lineage": "Warehouse management system -> nightly batch",
        "access_restriction": "None",
    },
    {
        "source_name": "Promotions",
        "source_type": "Structured",
        "grain": "Campaign / store / product",
        "refresh_cadence": "On change",
        "last_refresh": "2026-07-16 09:00",
        "historical_coverage": "Full campaign history",
        "data_quality": "Fresh",
        "owner": "Marketing",
        "lineage": "Campaign management tool -> manual export",
        "access_restriction": "None",
    },
    {
        "source_name": "Customer Feedback",
        "source_type": "Unstructured",
        "grain": "Individual feedback item",
        "refresh_cadence": "Near real-time",
        "last_refresh": "2026-07-31 21:40",
        "historical_coverage": "30 days",
        "data_quality": "Fresh",
        "owner": "Customer Experience",
        "lineage": "Feedback app + review aggregator -> streaming ingest",
        "access_restriction": "None",
    },
    {
        "source_name": "Internal Emails / Reports",
        "source_type": "Unstructured",
        "grain": "Individual document",
        "refresh_cadence": "Near real-time",
        "last_refresh": "2026-07-31 10:15",
        "historical_coverage": "30 days",
        "data_quality": "Fresh",
        "owner": "Store Operations / Marketing",
        "lineage": "Corporate mailbox connector -> ingestion pipeline",
        "access_restriction": "Internal use only",
    },
]


def _csvs_present():
    return all(os.path.exists(os.path.join(DATA_DIR, filename)) for filename in DATASET_FILES.values())


def _load_from_csv():
    datasets = {}
    for name, filename in DATASET_FILES.items():
        df = pd.read_csv(os.path.join(DATA_DIR, filename), low_memory=False)
        for col in BOOLEAN_COLUMNS.get(name, []):
            df[col] = df[col].astype(bool)
        datasets[name] = df
    return datasets


@st.cache_resource(show_spinner=False)
def get_datasets():
    if _csvs_present():
        return _load_from_csv()
    return generate_all()


def using_committed_dataset():
    """True if the app is reading the committed CSVs rather than generating fresh data."""
    return _csvs_present()


def get_source_metadata():
    return SOURCE_METADATA