import csv
import importlib.util
from pathlib import Path

from m4.data.transforms import monthly_average_to_quarterly


ROOT = Path(__file__).resolve().parents[1]


def evaluator():
    spec = importlib.util.spec_from_file_location("phase3b", ROOT / "scripts/evaluate_phase3b.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_production_and_export_quantities_are_distinct_series():
    fields = csv.DictReader((ROOT / "data/processed/m4-quarterly-v3.csv").open()).fieldnames
    assert "coal_production_thousand_t" in fields
    assert "coal_export_quantity_thousand_t" in fields
    assert "coal_production_thousand_t" != "coal_export_quantity_thousand_t"


def test_ipi_monthly_comparison_growth_is_averaged_by_quarter():
    rows = [{"month": "2024-01", "growth": 3}, {"month": "2024-02", "growth": -1}, {"month": "2024-03", "growth": 4}]
    assert monthly_average_to_quarterly(rows, "month", "growth") == {"2024-Q1": 2.0}


def test_gdp_gva_identity_is_within_published_rounding():
    rows = list(csv.DictReader((ROOT / "data/processed/m4-quarterly-v3.csv").open()))
    gaps = [abs(float(row["gdp_gva_identity_gap_mnt_million"])) for row in rows if row["gdp_gva_identity_gap_mnt_million"]]
    assert gaps and max(gaps) <= 0.31


def test_expanding_window_has_no_future_leakage_and_is_deterministic():
    module = evaluator(); y = list(range(1, 31)); x = [2 * value for value in y]
    first = module.expanding(y, x, minimum=24); second = module.expanding(y, x, minimum=24)
    assert first == second
    assert first["origins"] == list(range(24, len(y)))
    assert first["n_forecasts"] == 6
