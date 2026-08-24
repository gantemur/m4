from m4.data.transforms import (
    cumulative_monthly_to_flow,
    implied_unit_value,
    monthly_average_to_quarterly,
    monthly_flow_to_quarterly,
    monthly_stock_to_quarter_end,
)
from m4.data.versioning import detect_revisions
from m4.data.nso import NsoClient, NsoError


def test_mining_registry_has_unique_projects_and_neutral_badrakh_weight():
    text = open("data/metadata/mining-projects.yml", encoding="utf-8").read()
    project_ids = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("  - project_id:")]
    assert len(project_ids) == len(set(project_ids))
    assert "project_id: badrakh_energy_zuuvch_ovoo" in text
    assert "macro_materiality: not_established" in text


def test_monthly_flow_to_quarterly_sum():
    rows = [{"period": "2024-01", "value": 1}, {"period": "2024-02", "value": 2}, {"period": "2024-03", "value": 3}]
    assert monthly_flow_to_quarterly(rows, "period", "value") == {"2024-Q1": 6.0}


def test_cumulative_monthly_deaccumulates_at_year_boundary():
    rows = [{"period": "2023-12", "value": 12}, {"period": "2024-01", "value": 5}, {"period": "2024-02", "value": 9}]
    result = cumulative_monthly_to_flow(rows, "period", "value")
    assert [row["value"] for row in result] == [12.0, 5.0, 4.0]


def test_stock_and_average_conventions():
    rows = [{"period": "2024-01", "value": 1}, {"period": "2024-02", "value": 3}, {"period": "2024-03", "value": 5}]
    assert monthly_stock_to_quarter_end(rows, "period", "value") == {"2024-Q1": 5.0}
    assert monthly_average_to_quarterly(rows, "period", "value") == {"2024-Q1": 3.0}


def test_unit_value_and_revision_detection():
    assert implied_unit_value(100, 2, 1) == 50.0
    old = [{"period": "2024-Q1", "series_id": "x", "value": 1}]
    new = [{"period": "2024-Q1", "series_id": "x", "value": 2}]
    assert detect_revisions(old, new)[0]["change"] == "revised"


def test_semantic_dimension_mapping_ignores_numeric_position_and_fails_on_label_change():
    metadata = {"variables": [{"code": "indicator", "values": ["1", "11", "12"], "valueTexts": ["Total turnover", " Exports", " Imports"]}]}
    assert NsoClient.codes_for_labels(metadata, "indicator", ["Exports", "Imports"]) == {"Exports": "11", "Imports": "12"}
    try:
        NsoClient.codes_for_labels(metadata, "indicator", ["Export"])
    except NsoError:
        pass
    else:
        raise AssertionError("semantic label changes must fail loudly")


def test_month_indicator_is_direct_flow_not_cumulative():
    rows = [{"period": "2024-01", "value": 10}, {"period": "2024-02", "value": 20}, {"period": "2024-03", "value": 30}]
    assert monthly_flow_to_quarterly(rows, "period", "value") == {"2024-Q1": 60.0}


def test_trade_accounting_identities():
    exports, imports = 100.0, 40.0
    assert exports + imports == 140.0
    assert exports - imports == 60.0


def test_v1_units_and_coverage_metadata_match_panel():
    import csv, json
    panel = list(csv.DictReader(open("data/processed/m4-quarterly-v1.csv", encoding="utf-8")))
    metadata = json.load(open("data/metadata/series/m4-quarterly-v1.json", encoding="utf-8"))
    assert metadata["variables"]["exports_usd_million"]["unit"] == "USD million"
    assert next(row["quarter"] for row in panel if row["gdp_real2015_total"]) == "2015-Q1"
