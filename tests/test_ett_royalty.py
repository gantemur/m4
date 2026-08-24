import pytest

from m4.fiscal import ReferencePrice, RoyaltyInput, evaluate_ett_coal_royalty, evaluate_royalty, map_mse_ett_coal_product
from m4.model import Baseline, Scenario


def input_for(product_class="raw_coal", price=50.0, month="2026-08", sale_type="exported", quantity=1000.0):
    return RoyaltyInput(month, quantity, product_class,
        ReferencePrice(price, month, "2026-08-11", "https://example.test/mrpam", product_label="1/3 coking coal"),
        3500.0, sale_type)


def test_raw_coal_brackets_and_exact_thresholds():
    assert evaluate_royalty(input_for(price=25)).additional_rate_percent == 0
    assert evaluate_royalty(input_for(price=25.0001)).additional_rate_percent == 1
    assert evaluate_royalty(input_for(price=50)).additional_rate_percent == 1
    assert evaluate_royalty(input_for(price=125)).additional_rate_percent == 4
    assert evaluate_royalty(input_for(price=125.01)).additional_rate_percent == 5


def test_processed_and_final_product_schedules():
    assert evaluate_royalty(input_for("processed_coal", 100)).additional_rate_percent == 0
    assert evaluate_royalty(input_for("processed_coal", 130)).additional_rate_percent == 1
    assert evaluate_royalty(input_for("processed_coal", 210.01)).additional_rate_percent == 3
    assert evaluate_royalty(input_for("final_coal_product", 190)).additional_rate_percent == .5
    assert evaluate_royalty(input_for("final_coal_product", 270.01)).additional_rate_percent == 2.5


def test_units_and_institutional_trace_are_explicit():
    result = evaluate_ett_coal_royalty(input_for(price=50))
    assert result.status == "DETERMINED"
    assert result.assessed_sales_value_usd == 50_000
    assert result.assessed_sales_value_mnt == 175_000_000
    assert result.base_royalty_mnt == 8_750_000
    assert result.additional_royalty_mnt == 1_750_000
    assert result.total_royalty_million_mnt == 10.5
    assert result.fiscal_receipts() == {"mineral_royalty_amnat": 10.5}
    assert all(step["type"] == "institutional" for step in result.trace)


def test_domestic_missing_and_ambiguous_inputs_are_not_determined():
    assert evaluate_royalty(input_for(sale_type="domestic")).status == "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"
    assert evaluate_royalty(input_for(quantity=None)).status == "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"
    mapping = map_mse_ett_coal_product("1/3 coking coal")
    assert mapping.status == "AMBIGUOUS"
    assert evaluate_ett_coal_royalty(input_for(), mapping).status == "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"


def test_rule_based_mse_crosswalk_requires_quality_and_unknown_is_rejected():
    mapping = map_mse_ett_coal_product("1/3 coking coal", volatile_daf=33, caking_index=70)
    assert mapping.status == "RULE_BASED" and mapping.statutory_product_class == "raw_coal"
    assert map_mse_ett_coal_product("thermal coal").status == "UNMAPPED"
    with pytest.raises(ValueError, match="Unknown statutory"):
        evaluate_royalty(input_for("invented_class"))


def test_temporary_2025_mse_regime_is_not_automated_or_carried_into_2026():
    old = input_for(month="2025-10")
    old = RoyaltyInput(**{**old.__dict__, "valuation_regime": "mse_temporary_2025"})
    assert evaluate_royalty(old).status == "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"
    current = evaluate_royalty(input_for(month="2026-08"))
    assert current.status == "DETERMINED"
    bad_extension = RoyaltyInput(**{**input_for(month="2026-08").__dict__, "valuation_regime": "mse_temporary_2025"})
    assert evaluate_royalty(bad_extension).status == "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"


def test_notice_table_parser_returns_only_explicit_matching_rows():
    html = "<table><tr><td>1/3 coking coal</td><td>59.80</td></tr><tr><td>gas coal</td><td>62.49</td></tr></table>"
    from m4.fiscal.royalty import parse_mrpam_notice_html
    assert parse_mrpam_notice_html(html, "1/3 coking coal") == [["1/3 coking coal", "59.80"]]


def test_determined_receipt_is_an_explicit_institutional_project_contribution():
    contribution = evaluate_royalty(input_for()).to_project_contribution("2026-Q3")
    baseline = Baseline({"2026-Q3": {"government_revenue_mnt_million": 100.0}})
    result = Scenario(project_contributions=[contribution]).run(baseline)
    assert result.comparison("2026-Q3", "government_revenue_mnt_million")["linked_change"] == 10.5
    assert result.trace[0]["type"] == "institutional"
