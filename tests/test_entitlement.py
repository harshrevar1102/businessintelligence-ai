import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.synthetic_generator import generate_all
from app.entitlement.entitlement import allowed_locations, filter_dataframe


def test_store_manager_sees_only_stores():
    locations = allowed_locations("Store Manager")
    # Store Manager should NOT see "All India" or bare city names
    assert "All India" not in locations
    for city in ["Ahmedabad", "Jaipur", "Delhi", "Mumbai", "Bengaluru", "Hyderabad"]:
        assert city not in locations  # no city-level aggregate
    # But should see individual stores
    assert "Mumbai - Bandra" in locations
    assert "Delhi - Connaught Place" in locations
    assert len(locations) == 12  # 6 cities × 2 stores each


def test_store_manager_filtered_data_sees_store():
    data = generate_all()
    filtered = filter_dataframe(data["transactions"], "Store Manager", "Mumbai - Bandra")
    assert set(filtered["store"].unique()) == {"Bandra"}
    assert set(filtered["city"].unique()) == {"Mumbai"}


def test_regional_manager_no_all_india():
    locations = allowed_locations("Regional Manager")
    assert "All India" not in locations
    assert "Mumbai" in locations  # city-level visible
    assert "Mumbai - Bandra" in locations  # store-level visible


def test_ceo_sees_all_cities():
    data = generate_all()
    filtered = filter_dataframe(data["transactions"], "CEO / Executive", "All India")
    assert len(filtered["city"].unique()) == 6

