from m4.model import Baseline, Closure, NOT_DETERMINED, Scenario, Shock


def baseline():
    return Baseline({"2023-Q1": {"coal_export_quantity_thousand_t": 10.0, "coal_export_value_usd_thousand": 1000.0, "copper_concentrate_export_quantity_thousand_t": 2.0, "copper_concentrate_export_value_usd_thousand": 400.0, "government_revenue_mnt_million": 100.0, "government_expenditure_mnt_million": 90.0, "exports_usd_million": 2.0, "imports_usd_million": 1.0, "trade_balance_usd_million": 1.0, "gold_export_value_usd_thousand": 0.0, "iron_ore_export_value_usd_thousand": 0.0}})


def test_quantity_shock_changes_matching_export_value_only():
    result = Scenario(Closure.HISTORICAL_DEFAULT, [Shock("coal_export_quantity_thousand_t", .7, ("2023-Q1",))]).run(baseline())
    assert result.comparison("2023-Q1", "coal_export_value_usd_thousand")["scenario_value"] == 700.0
    assert result.comparison("2023-Q1", "copper_concentrate_export_value_usd_thousand")["absolute_deviation"] == 0.0


def test_closures_and_balances_are_explicit():
    b = baseline()
    fixed = Scenario(Closure.FIXED_GOVERNMENT_SPENDING, [Shock("coal_export_quantity_thousand_t", .7, ("2023-Q1",))]).run(b)
    assert fixed.comparison("2023-Q1", "government_expenditure_mnt_million")["status"] == NOT_DETERMINED
    fiscal = Scenario(Closure.HISTORICAL_DEFAULT, [], fiscal_response_phi=.5).run(b)
    assert fiscal.fiscal_balance("2023-Q1") == 10.0
    assert b.mining_export_usd_million("2023-Q1") == 1.4


def test_zero_production_has_zero_macro_contribution():
    b = Baseline({"2023-Q1": {"coal_export_value_usd_thousand": 0.0, "copper_concentrate_export_value_usd_thousand": 0.0, "gold_export_value_usd_thousand": 0.0, "iron_ore_export_value_usd_thousand": 0.0}})
    assert b.mining_export_usd_million("2023-Q1") == 0.0
