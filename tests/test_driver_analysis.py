import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.synthetic_generator import generate_all
from app.analytics import driver_analysis


def test_rank_drivers_returns_sorted_list():
    data = generate_all()
    drivers = driver_analysis.rank_drivers(
        data["transactions"], data["staffing"], data["promotions"], data["inventory"],
    )
    assert len(drivers) > 0
    contributions = [d.contribution_pct for d in drivers]
    assert contributions == sorted(contributions, reverse=True)


def test_stockout_detected_for_delhi_cold_brew():
    data = generate_all()
    stocked_out, products, stores = driver_analysis.check_stockout(data["inventory"])
    assert stocked_out is True
    assert "Cold Brew" in products
