from pathlib import Path
from m4.model import Baseline, NOT_DETERMINED, Scenario, Shock

ROOT = Path(__file__).resolve().parents[1]

def test_illustrative_qa_scenarios_are_directional_not_forecasts():
    b = Baseline.load(ROOT / "data/processed/m4-quarterly-v4.csv")
    quarter = "2024-Q1"
    coal = Scenario(shocks=[Shock("coal_export_quantity_thousand_t", .7, (quarter,))]).run(b)
    assert coal.comparison(quarter, "exports_usd_million")["absolute_change"] < 0
    assert coal.comparison(quarter, "gdp_real2015_mining")["status"] == NOT_DETERMINED
    copper = Scenario(shocks=[Shock("copper_concentrate_export_price", 1.2, (quarter,))]).run(b)
    assert copper.comparison(quarter, "exports_usd_million")["absolute_change"] > 0
    assert Scenario(shocks=[Shock("imports_usd_million", 1.15, (quarter,))]).run(b).comparison(quarter, "trade_balance_usd_million")["absolute_change"] < 0
    assert Scenario(shocks=[Shock("government_expenditure_mnt_million", .9, (quarter,))]).run(b).comparison(quarter, "government_expenditure_mnt_million")["absolute_change"] < 0
    mining = Scenario(shocks=[Shock("mining_real_output", .9, (quarter,))]).run(b)
    assert mining.comparison(quarter, "gdp_real2015_mining")["absolute_change"] < 0
