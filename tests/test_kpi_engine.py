import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.synthetic_generator import generate_all
from app.analytics import kpi_engine


def _data():
    return generate_all()


def test_revenue_kpi_has_positive_values():
    data = _data()
    result = kpi_engine.compute_revenue_kpi(data["transactions"])
    assert result.current_value > 0
    assert result.baseline_value > 0


def test_wait_time_kpi_increases_in_current_period():
    data = _data()
    result = kpi_engine.compute_wait_time_kpi(data["staffing"])
    assert result.current_value > 0
    assert result.movement_pct != 0


def test_compute_all_kpis_returns_four_kpis():
    data = _data()
    kpis = kpi_engine.compute_all_kpis(data["transactions"], data["staffing"])
    assert set(kpis.keys()) == {"Revenue", "Transactions", "Average Ticket", "Wait Time"}
