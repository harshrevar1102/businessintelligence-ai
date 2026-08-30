import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.synthetic_generator import generate_all
from app.entitlement.entitlement import allowed_locations, filter_dataframe


def test_store_manager_locked_to_bandra():
    locations = allowed_locations("Store Manager")
    assert locations == ["Mumbai - Bandra"]


def test_store_manager_filtered_data_only_has_bandra():
    data = generate_all()
    filtered = filter_dataframe(data["transactions"], "Store Manager", "Mumbai - Bandra")
    assert set(filtered["store"].unique()) == {"Bandra"}
    assert set(filtered["city"].unique()) == {"Mumbai"}


def test_ceo_sees_all_cities():
    data = generate_all()
    filtered = filter_dataframe(data["transactions"], "CEO / Executive", "All India")
    assert len(filtered["city"].unique()) == 6
