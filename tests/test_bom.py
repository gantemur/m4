from m4.data.bom import parse_bom_date, step_policy_rate
from m4.data.transforms import monthly_stock_to_quarter_end


def test_bom_date_and_quarter_end_stock():
    assert parse_bom_date("2026-07-31T00:00:00") .isoformat() == "2026-07-31"
    rows = [{"period": "2025-01", "value": 1}, {"period": "2025-03", "value": 3}, {"period": "2025-04", "value": 4}]
    assert monthly_stock_to_quarter_end(rows, "period", "value")["2025-Q1"] == 3.0


def test_policy_rate_step_is_effective_date_based():
    changes = [{"effective_date": "2007-07-01", "rate": 10}, {"effective_date": "2020-04-13", "rate": 9}]
    assert step_policy_rate(changes, ["2007-06-30", "2007-07-31", "2020-04-30"]) == {"2007-07-31": 10.0, "2020-04-30": 9.0}
