import pytest
from pathlib import Path
from m4.model import AssumptionLinks, Baseline, Closure, NOT_DETERMINED, ProjectContribution, Scenario, Shock


def baseline():
    return Baseline({"2023-Q1": {
        "coal_export_quantity_thousand_t": 10.0, "coal_export_value_usd_thousand": 1000.0,
        "coal_production_thousand_t": 20.0, "copper_concentrate_export_value_usd_thousand": 400.0,
        "gold_export_value_usd_thousand": 0.0, "iron_ore_export_value_usd_thousand": 0.0,
        "exports_usd_million": 2.0, "imports_usd_million": 1.0, "trade_balance_usd_million": 1.0,
        "mnt_per_usd_quarterly_average": 3000.0, "government_revenue_mnt_million": 100.0,
        "government_expenditure_mnt_million": 90.0, "gdp_real2015_mining": 50.0,
        "gdp_nominal_mining": 30.0, "gdp_nominal_agriculture": 10.0, "gdp_nominal_construction": 5.0,
        "other_industry_gva_nominal_mnt_million": 40.0, "taxes_less_subsidies_nominal_mnt_million": 15.0,
        "gdp_nominal_total": 100.0,
    }})


def test_coal_export_shock_is_trade_direct_and_mining_gdp_is_not_determined():
    result = Scenario(shocks=[Shock("coal_export_quantity_thousand_t", .7, ("2023-Q1",))]).run(baseline())
    assert result.comparison("2023-Q1", "coal_export_value_usd_thousand")["scenario_value"] == 700.0
    assert result.comparison("2023-Q1", "exports_usd_million")["absolute_change"] == pytest.approx(-.3)
    assert result.comparison("2023-Q1", "trade_balance_usd_million")["absolute_change"] == pytest.approx(-.3)
    assert result.comparison("2023-Q1", "gdp_real2015_mining")["status"] == NOT_DETERMINED
    assert any(step["type"] == "identity" for step in result.trace)


def test_production_does_not_change_exports_without_an_explicit_link():
    result = Scenario(shocks=[Shock("coal_production_thousand_t", .7, ("2023-Q1",))]).run(baseline())
    assert result.comparison("2023-Q1", "coal_production_thousand_t")["scenario_value"] == 14.0
    assert result.comparison("2023-Q1", "coal_export_value_usd_thousand")["absolute_change"] == 0.0
    assert result.comparison("2023-Q1", "gdp_real2015_mining")["status"] == NOT_DETERMINED


def test_optional_fiscal_links_have_exact_fx_scaling_and_decomposition():
    links = AssumptionLinks(lambda_revenue=.1, phi_revenue_to_expenditure=.5)
    result = Scenario(Closure.USER_SPECIFIED_FISCAL_RESPONSE, [Shock("coal_export_quantity_thousand_t", .7, ("2023-Q1",))], links).run(baseline())
    revenue = result.comparison("2023-Q1", "government_revenue_mnt_million")
    spending = result.comparison("2023-Q1", "government_expenditure_mnt_million")
    assert revenue["linked_change"] == -90.0  # -0.3 USDm * 3,000 MNT/USD * 0.1
    assert spending["linked_change"] == -45.0
    assert result.comparison("2023-Q1", "exports_usd_million")["direct_change"] == pytest.approx(-.3)
    assert any(step.get("parameter") == "lambda_revenue" for step in result.trace)


def test_nominal_gdp_identity_and_zero_project_receipt():
    result = Scenario(shocks=[Shock("mining_gva", 2, ("2023-Q1",))], links=AssumptionLinks(project_fiscal_receipts_mnt_million={"2023-Q1": 0.0})).run(baseline())
    assert result.comparison("2023-Q1", "gdp_nominal_total")["scenario_value"] == 130.0
    assert result.comparison("2023-Q1", "government_revenue_mnt_million")["absolute_change"] == 0.0


def test_commodity_price_quantity_identity_uses_explicit_thousand_conversion():
    b = baseline()
    assert b.commodity_export_price_usd_per_native_quantity("2023-Q1", "coal") == 100000.0
    assert b.commodity_export_value_from_price_quantity_usd_thousand("2023-Q1", "coal") == 1000.0


def test_zero_production_badrakh_project_has_zero_macro_contribution():
    result = Scenario(project_contributions=[ProjectContribution("badrakh", "2023-Q1", "uranium")]).run(baseline())
    assert result.comparison("2023-Q1", "exports_usd_million")["absolute_change"] == 0.0
    assert result.comparison("2023-Q1", "government_revenue_mnt_million")["absolute_change"] == 0.0


def test_custom_and_permanent_paths_are_serializable():
    b = Baseline({"2023-Q1":{"imports_usd_million":10.0,"exports_usd_million":12.0,"trade_balance_usd_million":2.0}, "2023-Q2":{"imports_usd_million":10.0,"exports_usd_million":12.0,"trade_balance_usd_million":2.0}})
    result = Scenario(shocks=[Shock("imports_usd_million", start="2023-Q2", multiplier=1.1)]).run(b)
    assert result.comparison("2023-Q1", "imports_usd_million")["absolute_change"] == 0
    assert result.comparison("2023-Q2", "trade_balance_usd_million")["scenario_value"] == 1.0
    assert result.to_dict()["closure"] == "historical-default"


def test_corrected_v4_baseline_replays_all_available_accounting_identities():
    panel = Path(__file__).resolve().parents[1] / "data/processed/m4-quarterly-v4.csv"
    b = Baseline.load(panel)
    assert all(not failures for failures in b.replay_checks().values())
    assert Scenario().run(b).scenario == b.rows
